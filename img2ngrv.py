#!/usr/bin/python
# coding: UTF-8, break: linux, indent: 4 spaces, lang: python/eng
'''
Convert common image formats to G-code.

Program is optimized of a lulzbut Mini with a 1W engraving laser and tested
with KiCad plots as input. Usage with anything else at your own risk!

ToDo:
 - Enable grayscale engraving

Usage:
    {progname} --help | --version | --test
    {progname} [options] [-v...] INFILE [OUTFILE]

Options:
    -v --verbose                    Specify (multiply) to increase output
                                       messages
    --test                          Test this program and exit
    -r --target-resolution=<float>  Target resolution (dpi or diameter)
                                       [default: {tdpi}dpi]
    -i --invert                     Invert pixels of input image
    -1 --on-command=<str>           Command to turn the engraver on
                                       [default: {lon}]
    -0 --off-command=<str>          Command to turn the engraver off
                                       [default: {loff}]
    -f --light-speed=<float>        Speed for light engraving
                                       [default: {lghtspd}]
    -l --low-speed=<float>          Speed for full engraving
                                       [default: {lowspd}]
    -m --move-speed=<float>         Speed when moving without engraving
                                       [default: {mvspd}]
    -t --engraver-threshold=<int>   Threshold driving value for the engraver
                                       [default: 90]
    -M --engraver-max=<int>         Maximal driving value for the engraver
                                       [default: 255]
    -x --x-offset=<float>           Offset from zero position in x-direction
                                       [default: {xfst}mm]
    -y --y-offset=<float>           Offset from zero position in y-direction
                                       [default: {yfst}mm]
'''

#=======================================================================

from __future__ import division, print_function, unicode_literals
from logging import info, debug, error, warning as warn
import sys, os, re, math, glob, logging, time
import numpy as np
import pint
import matplotlib.pyplot as plt
from docopt import docopt
from PIL import Image
from io import StringIO

#=======================================================================

loff = 'M107'
lon  = 'M106'
lfon = lon +' S255'
lson = lon +' S90'
verb = 0
tdpi = 508
lghtspd = 300
lowspd = 70
mvspd = 1500
xfst = 20.0
yfst = 20.0
nvrt = False

tm = time.strftime('%c')

pre = ''';This Gcode has been generated specifically for the LulzBot Mini
;It assumes the engraver (laser) is controlled by fan1 output
;Creation Date: {tm}
;----------------------------------------------------------------------------
G26                          ; clear potential 'probe fail' condition
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
{loff}                         ; start with the fan off
M104 S0                      ; hotend off
M140 S0                      ; heated bed heater off (if you have it)
G92 E0                       ; set extruder position to 0
G28                          ; home all
G1 Z25  F{mvspd}                ; CRITICAL: set Z
G28 X0 Y0                    ; home x and y
M204 S300                    ; Set probing acceleration
G29                          ; Probe
M204 S2000                   ; Restore standard acceleration
G1 X5 Y15 Z25 F5000          ; get out the way
G4 S1                        ; pause
M400                         ; clear buffer
{lson}                     ; Turn on laser just enough to see it
G4 S100                      ; dwell to allow for laser focusing
G1 X0 Y0

; Bounding box for placement
G1 X{x0} Y{y0} ; Start (lower left corner)
{lon} S255
G1 X{x0} Y{y0} F{lghtspd} ; Lower left
G1 X{x1} Y{y0} F{lghtspd} ; Lower right
G1 X{x1} Y{y1} F{lghtspd} ; Upper right
G1 X{x0} Y{y1} F{lghtspd} ; Upper left
G1 X{x0} Y{y0} F{lghtspd} ; Lower left
{loff}
G4 S100 ; Dwell for positioning
{lson}
G1 X{x0} Y{y1} F{lghtspd} ; Warning movement
G1 X{x0} Y{y0} F{lghtspd} ; Warning movement
G4 S5   ; Dwell to let warning sink in

; Start Engraving
'''

post = '''\
; End Engraving

; Cleanup
{lon} S0                                      ; laser off
{loff}                                         ; laser really off
M104 S0                                      ; hotend off
M140 S0                                      ; heated bed off
M84                                          ; steppers off
G90                                          ; absolute positioning
'''

ureg = pint.UnitRegistry()
ureg.define('dotsperinch = 1/25.4/mm = dpi')


def write_gcode( dat, lfon=lfon, loff=loff, lowspd=lowspd, mvspd=mvspd, fl=sys.stdout ):
    r'''Traverses `dat` in zic-sac to create a gcode raster of it.

    Example:
    >>> dat = np.zeros((5,3),dtype='uint8')
    >>> dat[:,2] = 1
    >>> buff = StringIO()
    >>> write_gcode( dat, fl=buff )
    >>> _ = buff.seek(0)
    >>> ''.join(buff.readlines())
    u'M107\nG1 X20.1 Y20.0 F1500\n\nM106 S255\nG1 X20.1 Y20.05 F70\n\nM107\nG1 X20.1 Y20.1 F1500\n\nM106 S255\nG1 X20.1 Y20.15 F70\n\nM107\nG1 X20.1 Y20.2 F1500\n\n'
    '''
    lst = 0
    for y in xrange( 0, dat.shape[0]):
        if all( dat[y,:]>0 ): continue # Skip empty lines
        drcn = y % 2
        sta = int(       drcn  * (dat.shape[1]-1)          )
        end = int(  (not drcn) * (dat.shape[1]  ) - 1*drcn )
        for x in xrange( sta, end, 1-2*drcn ):
            val = dat[y,x]
            if val != lst:
                if val == 1:
                    fl.write(
                        loff +"\n"+
                        'G1 X'+ trfx(x+drcn) +' Y'+ trfy(y) +' F'+ str(mvspd) +"\n"
                    )
                else:
                    fl.write(
                        lfon +"\n"+
                        'G1 X'+ trfx(x+drcn) +' Y'+ trfy(y) +' F'+ str(lowspd) +"\n"
                    )
                lst = val
        fl.write("\n")


def crop(dat, clp=True, nvrt=False):
    '''Crops zero-edges of an array and clips it to [0,1].

    Example:
    >>> crop( np.array(
    ...       [[0,0,0,0,0,0],
    ...        [0,0,0,0,0,0],
    ...        [0,1,0,2,9,0],
    ...        [0,0,0,0,0,0],
    ...        [0,7,4,1,0,0],
    ...        [0,0,0,0,0,0]]
    ...     ))
    array([[1, 0, 1, 1],
           [0, 0, 0, 0],
           [1, 1, 1, 0]])
    '''
    if clp:    np.clip( dat, 0, 1, out=dat )
    if nvrt:   dat = 1-dat
    true_points = np.argwhere(dat)
    top_left = true_points.min(axis=0)
    bottom_right = true_points.max(axis=0)
    dat = dat[  top_left[0]:bottom_right[0]+1,
                top_left[1]:bottom_right[1]+1  ]
    return dat


def load_img( fn, tdpi, dx, dy, w, h ):
    '''Load raster image and prepare it for `write_gcode(...)`.'''
    img = Image.open( fn )
    img = img.convert('L') # grayscale
    if not w: w = img.width
    if not h: h = img.height
    if not dx: dx = img.info.get('dpi', [tdpi])[0]
    if not dy: dy = img.info.get('dpi', [None,tdpi])[1]
    debug('RSTR - w: %s, h: %s, pngdpi: %s', w, h, img.info.get('dpi', [None,None]) )
    sclx, scly = tdpi/dx, tdpi/dy
    nw, nh = int(sclx*w), int(scly*h)
    debug( 'RSTR - sclx: %s (%s px - %s dpi), scly: %s (%s px - %s dpi)',
                       sclx,  w,     dx,          scly,  h,     dy        )
    img = img.resize( (nw,nh), Image.BICUBIC ) # NEAREST
    img.info['dpi'] = (tdpi, tdpi)
    dat = np.asarray( img, dtype='uint8' )
    dat = crop(dat, nvrt=nvrt)
    debug('RSTR - Shape [0]: %s(y), [1]: %s(x)', dat.shape[0], dat.shape[1])
    return dat


def svg_get_phys_size( fn ):
    '''Get pyhsical dimentions from the metadata of an svg image.

    Example:
    >>> svg = StringIO()
    >>> _ = svg.write('<svg width="13.97cm" height="7.68in"></svg>')
    >>> _ = svg.seek(0)
    >>> svg_get_phys_size(svg)
    (<Quantity(139.7, 'millimeter')>, <Quantity(195.072, 'millimeter')>)
    '''
    import xml.etree.ElementTree
    xml = xml.etree.ElementTree.parse(fn).getroot()
    wd, ht = xml.attrib.get('width', None), xml.attrib.get('height', None)
    wd, ht = ureg.parse_expression(wd), ureg.parse_expression(ht)
    debug( 'XML - height: %s, width: %s', wd.to('mm'), ht.to('mm') )
    return wd.to('mm'), ht.to('mm')


def load_svg( fn, dpi, w, h ):
    '''Load svg image and prepare it for `write_gcode(...)`.

    Example:
    >>> load_svg('https://www.w3.org/Icons/SVG/svg-logo.svg', 0, 1, 1)
    array([[1]], dtype=uint8)
    '''
    import cairosvg
    from io import BytesIO
    if not dpi: dpi = 96
    debug( 'SVG - %s, dpi: %s', fn, dpi )
    pngtxt = cairosvg.svg2png(url=fn, dpi=dpi)
    buff = BytesIO()
    buff.write(pngtxt)
    buff.seek(0)
    return load_img(buff, dpi, dpi, dpi, w, h)


def trfx( x ):
    return str(x*(1.0/tdpi*25.4)+xfst)

def trfy( y ):
    return str(y*(1.0/tdpi*25.4)+yfst)


def write_ngrv_file(infl, outfl):
    '''Make a gcode raster for engraving from an input image.'''
    try:
        dat = load_svg(infl, tdpi, None, None)
    except:
        try:
            dat = load_img(infl, tdpi, None, None, None, None)
        except:
            raise

    # Preview if verbose
    dat.setflags( write=True )
    if verb <= logging.WARNING:
        import tempfile
        nm = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
        plt.title('Engraving mask from '+ infl)
        plt.imshow( dat, interpolation='none', cmap='Greys_r' )
        plt.savefig(nm)
        plt.show()
        print( "Saved to '{}'".format(nm) )

    # Write File
    fl = open( outfl, 'w' ) if outfl else sys.stdout
    x0, y0 = trfx(0), trfy(0)
    x1, y1 = trfx(dat.shape[1]), trfy(dat.shape[0])
    allvars = dict(globals(), **locals())

    fl.write( pre.format(**allvars) )
    write_gcode( dat, lfon, loff, lowspd, mvspd, fl )
    fl.write( post.format( **globals() ) )


def main():
    # Argument handling and all the boring bookkeeping stuff
    progname = os.path.splitext(os.path.basename( __file__ ))[0]
    vstring = (' v0.4\nWritten by con-f-use@gmx.net\n'
               '(Sat Sep 14 12:01:51 CEST 2016) on confusion' )
    args = docopt(__doc__.format(progname=progname,**globals()), version=progname+vstring)
    if args['--test']: import doctest; doctest.testmod(); exit(0)
    verb    = logging.ERROR - int(args['--verbose'])*10
    logging.basicConfig(
        level   = verb,
        format  = '[%(levelname)-7.7s] (%(asctime)s '
                  '%(filename)s:%(lineno)s) %(message)s',
        datefmt = '%y%m%d %H:%M'   #, stream=, mode=, filename=
    )
    global lon, loff, nvrt, tdpi, xfst, yfst, lghtspd, lowspd, mvspd, lson, lfon
    lon     =      args['--on-command']
    loff    =      args['--off-command']
    nvrt    =      args['--invert']
    tdpi    = ureg.parse_expression(args['--target-resolution'])
    xfst    = ureg.parse_expression(args['--x-offset'])
    yfst    = ureg.parse_expression(args['--y-offset'])
    if tdpi.dimensionality == '[length]': tdpi = 1.0/tdpi
    tdpi = int( tdpi.to('dpi').magnitude )
    xfst = float( xfst.to('mm').magnitude )
    yfst = float( yfst.to('mm').magnitude )
    lghtspd = int( args['--light-speed'] )
    lowspd  = int( args['--low-speed']   )
    mvspd   = int( args['--move-speed']  )
    lson = lon +' S'+ str(int( args['--engraver-threshold'] ))
    lfon = lon +' S'+ str(int( args['--engraver-max']       ))

    write_ngrv_file( args['INFILE'], args['OUTFILE'] )


if __name__ == '__main__':
    main()
