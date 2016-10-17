#!/usr/bin/python
# coding: UTF-8, break: linux, indent: 4 spaces, lang: python/eng
'''
Convert common image formats to G-code.

Program is optimized for a lulzbut Mini with a 1W engraving laser and tested
with KiCad .svg and .png plots as input. Usage with anything else than that
may prove difficult. When units are required, the program should accept the
most common ones (SI and imperial).

See: {__url__}

ToDo:
 - Think about changing engrving speed with pixel value as well
 - Change variable names to reflect argument dict
 - Do python variant of 'inkscape --verb=FitCanvasToDrawing --verb=FileSave --verb=FileClose *.svg' before hand (maybe https://github.com/skagedal/svgclip)

Usage:
    {__package__} --help | --version | --test
    {__package__} [options] [-v...] INFILE [OUTFILE]

Options:
    -v --verbose                    Specify (multiply) to increase output
                                       messages (and plot a preview)
    --test                          Test componentts of this program and exit
    -i --invert                     Invert pixel value of input image
    -m --mirror                     Flip input image left to right
    -a --alternate-mode             Fix rare issue with svg tranparency
    -b --black-and-white            Set every pixel non-zero pixel to maximum
                                        intensity
    -r --target-resolution=<res>    Target resolution (dpi or diameter)
                                       [default: 508dpi]
    -c --clip=<int>                 Threshold pixel value to be interpreted
                                        as engraver full on [default: 1]
    -1 --on-command=<str>           Command to turn the engraver on
                                       [default: M106]
    -0 --off-command=<str>          Command to turn the engraver off
                                       [default: M107]
    -f --light-speed=<float>        Speed for light engraving
                                       [default: 500]
    -l --low-speed=<float>          Speed for full engraving
                                       [default: 70]
    -m --move-speed=<float>         Speed when moving without engraving
                                       [default: 2000]
    -t --engraver-threshold=<int>   Threshold driving value for the engraver
                                       [default: 90]
    -M --engraver-max=<int>         Maximal driving value for the engraver
                                       [default: 255]
    -x --x-offset=<len>             Offset from zero position in x-direction
                                       [default: 20.0mm]
    -y --y-offset=<len>             Offset from zero position in y-direction
                                       [default: 20.0mm]
    -p --preamble=<filename>        Textfile containing the to be preamble of
                                        the output G-Code
    -f --footer=<filename>          Textfile containing the to be footer of
                                        the output G-Code
'''



from __future__ import division, print_function, unicode_literals
from logging import info, debug, error, warning as warn
import sys, os, re, logging, time
from io import StringIO
import numpy as np
import pint
import matplotlib.pyplot as plt
import docopt
from PIL import Image

__version__      = 'v0.4-21'
__author__       = 'con-f-use'
__author_email__ = 'con-f-use@gmx.net'
__url__          = 'https://github.com/con-f-use/img2ngrv'
__package__ = os.path.splitext(os.path.basename( __file__ ))[0]
__vstring__ = '{} {}\nWritten by {}'.format( __package__, __version__,
                                              __author__                )

#=======================================================================

pre = ''';This Gcode has been generated specifically for the LulzBot Mini
;It assumes the engraver (laser) is controlled by fan1 output
;Creation Date: {tm}
;----------------------------------------------------------------------------
G26                          ; clear potential 'probe fail' condition
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
{off_command}                         ; start with the fan off
M104 S0                      ; hotend off
M140 S0                      ; heated bed heater off (if you have it)
G92 E0                       ; set extruder position to 0
G28                          ; home all
G1 Z25  F{move_speed}                ; CRITICAL: set Z
G28 X0 Y0                    ; home x and y
M204 S300                    ; Set probing acceleration
G29                          ; Probe
M204 S2000                   ; Restore standard acceleration
G1 X5 Y15 Z25 F5000          ; get out the way
G4 S1                        ; pause
M400                         ; clear buffer
{lson}                     ; Turn on laser just enough to see it
G4 S100                      ; dwell to allow for laser focusing

; Bounding box for placement
G1 X{x0} Y{y0} ; Start (lower left corner)
{lfon}
G1 X{x1} Y{y0} F{light_speed} ; Lower right
G1 X{x1} Y{y1} F{light_speed} ; Upper right
G1 X{x0} Y{y1} F{light_speed} ; Upper left
G1 X{x0} Y{y0} F{light_speed} ; Lower left
{off-command}
G4 S100 ; Dwell for positioning
{lson}
G1 X{x0} Y{y1} F{light_speed} ; Warning movement
G1 X{x0} Y{y0} F{light_speed} ; Warning movement
G4 S5   ; Dwell to let warning sink in

; Start Engraving
'''

post = '''\
; End Engraving

; Cleanup
{on-command} S0                                      ; laser off
{off_command}                                         ; laser really off
M104 S0                                      ; hotend off
M140 S0                                      ; heated bed off
M84                                          ; steppers off
G90                                          ; absolute positioning
'''


def write_gcode( dat, lon='', loff='', lowspd='', mvspd='', fl=sys.stdout ):
    r'''Traverses input pixel array `dat` in zic-zac fashion to create a gcode raster of it.

    Example:
    >>> dat = np.zeros((3,4),dtype='uint8')
    >>> dat[:,1] = 40*np.arange(3); dat[:,2] = dat[:,1]+10
    >>> buff = StringIO()
    >>> write_gcode( dat, fl=buff )
    >>> _ = buff.seek(0)
    >>> ''.join(buff.readlines())
    u'M107\nG1 X20.1 Y20.0 F2000\nM106 S96\nG1 X20.15 Y20.0 F70\n\nM107\nG1 X20.15 Y20.05 F2000\nM106 S122\nG1 X20.1 Y20.05 F70\nM106 S115\nG1 X20.05 Y20.05 F70\n\nM107\nG1 X20.05 Y20.1 F2000\nM106 S141\nG1 X20.1 Y20.1 F70\nM106 S148\nG1 X20.15 Y20.1 F70\n\n'
    '''
    rvsd = lst = 0
    xrng = range(dat.shape[1])
    for y in range(dat.shape[0]):
        force = lst>0
        for x in reversed(xrng) if rvsd else xrng:
            val = dat[y,x]
            if val != lst or force:
                if lst<1:
                    fl.write(
                        loff +"\n"+
                        'G1 X'+ trfx(x+rvsd) +' Y'+ trfy(y) +' F'+ str(mvspd) +"\n"
                    )
                else:
                    fl.write(
                        lon +' S'+ trfv(lst) +"\n"+
                        'G1 X'+ trfx(x+rvsd) +' Y'+ trfy(y) +' F'+ str(lowspd) +"\n"
                    )
                lst = val
                force = False
        rvsd = not rvsd
        fl.write("\n")


# Coordinate transformations for `write_gcode(...)`.
def trfx( x ): return str( x*(1.0/tdpi*25.4) + xfst )
def trfy( y ): return str( y*(1.0/tdpi*25.4) + yfst )
def trfv( v ): return str( int( lint + v/255*(fint - lint) ) )


def write_ngrv_file(**a):
    '''Make a gcode raster for engraving from an input image.'''
    try:
        dat = load_svg(infl, tdpi, clp, None, None)
    except:
        try:
            dat = load_img(infl, tdpi, clp, None, None, None, None)
        except:
            raise

    # Preview if verbose
    if verb <= logging.WARNING:
        prevw_ngrv(infl, dat)

    # Write File
    fl = open( outfl, 'w' ) if outfl else sys.stdout
    x0, y0 = trfx(0), trfy(0)
    x1, y1 = trfx(dat.shape[1]), trfy(dat.shape[0])
    allvars = dict(globals(), **locals())

    fl.write( pre.format(**allvars) )
    write_gcode( dat, a.lon, a.loff, a.low_speed, a.move_speed, fl )
    fl.write( post.format( **globals() ) )


def crop(dat, clp=127, nvrt=False, flplr=False, flpud=False):
    '''Crops zero-edges of an array and clips it to [0,1].

    Example:
    >>> crop( np.array(
    ...       [[0,0,0,0,0,0,0,0],
    ...        [0,1,0,2,9,0,0,0],
    ...        [0,0,0,0,0,0,0,0],
    ...        [0,7,4,1,0,0,0,0]]
    ...     ), clp=0)
    array([[1, 0, 2, 9],
           [0, 0, 0, 0],
           [7, 4, 1, 0]])
    '''
    if clp:    dat[dat<=clp] = 0;
    if bw:     dat[dat>clp] = 255;
    if nvrt:   dat = 255-dat
    true_points = np.argwhere(dat)
    top_left = true_points.min(axis=0)
    bottom_right = true_points.max(axis=0)
    dat = dat[  top_left[0]:bottom_right[0]+1,
                top_left[1]:bottom_right[1]+1  ]
    if flplr:  np.fliplr(dat)
    if flpud:  np.flipud(dat)
    return dat


def prevw_ngrv(infl, dat):
    '''Preview data'''
    import tempfile
    nm = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
    mrrd = ' (mirrored)' if flplr else ''
    a = plt.imshow( dat, interpolation='none', cmap='Greys_r' ) # Greys_r'
    clrcode = ''
    if a.cmap.name == 'Greys': clrcode = '\nblack=substract; white=leave'
    if a.cmap.name == 'Greys_r': clrcode = '\nblack=leave; white=substract'
    plt.title('Engraving mask from '+ infl + mrrd + clrcode)
    plt.savefig(nm)
    plt.show()
    print( "Saved to '{}'".format(nm) )


def load_img( fn, tdpi, clp, dx, dy, w, h ):
    '''Load raster image and prepare it for `write_gcode(...)`.'''
    img = Image.open( fn )
    bgr = Image.new( "RGBA", img.size, (0,0,0) )
    bgr.paste( img, mask=img.split()[3] )
    mode = 'P' if altm else 'L'
    img = img.convert(mode) # greyscale
    if not w: w = img.width
    if not h: h = img.height
    if not dx: dx = img.info.get('dpi', [tdpi])[0]
    if not dy: dy = img.info.get('dpi', [None,tdpi])[1]
    debug('RSTR - w: %s, h: %s, pngdpi: %s', w, h, img.info.get('dpi', [None,None]) )
    sclx, scly = tdpi/dx, tdpi/dy
    nw, nh = int(sclx*w), int(scly*h)
    debug( 'RSTR - sclx: %s (%s px - %s dpi), scly: %s (%s px - %s dpi)',
                       sclx,  w,     dx,          scly,  h,     dy        )
    img = img.resize( (nw,nh), Image.BICUBIC ) # NEAREST, BICUBIC, BILINEAR, LANCZOS
    img.info['dpi'] = (tdpi, tdpi)
    dat = np.asarray( img, dtype='uint8' )
    dat.setflags(write=True)
    #dt = np.copy(dat)
    dat = crop(dat, clp=clp, nvrt=nvrt)
    debug('RSTR - Shape [0]: %s(y), [1]: %s(x)', dat.shape[0], dat.shape[1])
    return dat


def svg_get_phys_size( fn ):
    '''Get pyhsical dimentions from the metadata of an svg image.

    Example:
    >>> svg = StringIO()
    >>> _ = svg.write('<svg width="13.97cm" height="7.68in"></svg>')
    >>> _ = svg.seek(0)
    >>> svg_get_phys_size(svg)
    (139.7, 195.072)
    '''
    import xml.etree.ElementTree
    xml = xml.etree.ElementTree.parse(fn).getroot()
    wd, ht = xml.attrib.get('width', None), xml.attrib.get('height', None)
    wd, ht = ureg.parse_expression(wd), ureg.parse_expression(ht)
    debug( 'XML - height: %s, width: %s', wd.to('mm'), ht.to('mm') )
    return round(wd.to('mm').magnitude,4), round(ht.to('mm').magnitude,4)


def load_svg( fn, dpi, clp, w, h ):
    '''Load svg image and prepare it for `write_gcode(...)`.

    Example:
    >>> load_svg('https://www.w3.org/Icons/SVG/svg-logo.svg', 0, 1, 1, 1)
    array([[71]], dtype=uint8)
    '''
    import cairosvg
    from io import BytesIO
    if not dpi: dpi = 96
    debug( 'SVG - %s, dpi: %s', fn, dpi )
    buff = BytesIO()
    cairosvg.svg2png(url=fn, write_to=buff, dpi=dpi) #url=fn #file_obj=fn
    buff.seek(0)
    return load_img(buff, dpi, clp, dpi, dpi, w, h)


#=======================================================================
# From here on its argument handling and boring book keeping stuff


def run_tests():
    '''Run tests for all functions in this code.'''
    import doctest
    class Py23DocChecker(doctest.OutputChecker):
      def check_output(self, want, got, optionflags):
        if sys.version_info[0] > 2:
          want = re.sub("u'(.*?)'", "'\\1'", want)
          want = re.sub('u"(.*?)"', '"\\1"', want)
        return want == got
    doctest.OutputChecker = Py23DocChecker
    sys.exit( doctest.testmod(
            m=sys.modules.get('img2ngrv'),
            verbose=True
    )[0] )


class Bunch(docopt.Dict):
    def __init__(self, dict_):
        docopt.Dict.__init__(self, dict_)
        self.__dict__.update(dict_)

    def __setitem__(self, key, value):
        self.__dict__[key] = value
        docopt.Dict.__setitem__(self, key, value)


ureg = pint.UnitRegistry()
ureg.define('dotsperinch = 1/25.4/mm = dpi')


def convert_cmd_args(a):
    a = {re.sub('^--', '', k).replace('-','_').lower(): v for k, v in a.items()}
    a = Bunch(a)
    a['lson'] = a.on_command  +' S'+ a.engraver_threshold
    a['lfon'] = a.off_command +' S'+ a.engraver_max
    if a.preamble:
        with open(a.preamble) as fh:
            pre = ''.join(fh.readlines())
    if a.footer:
        with open(a.footer) as fh:
            post = ''.join(fh.readlines())
    for arg in ['target_resolution', 'x_offset', 'y_offset']:
        a[arg] = ureg.parse_expression(a[arg])
    for arg in ['x_offset','y_offset']:
        a[arg] = float(a[arg].to('mm').magnitude)
    if a.target_resolution.dimensionality == '[length]':
        a['target_resolution'] = 1.0/a.target_resolution
    a['target_resolution'] = a.target_resolution.to('dpi').magnitude
    for arg in ['engraver_threshold', 'engraver_max', 'light_speed', 'low_speed', 'move_speed', 'clip', 'target_resolution']:
        a[arg] = int(a[arg])
    a['verbose'] = logging.ERROR - int(a.verbose)*10
    return a


defaults = convert_cmd_args(docopt.docopt(__doc__,['.']))
#defaults = docopt.docopt(__doc__,['.'])
tm = time.strftime('%c')


def main():
    a = docopt.docopt(__doc__.format(**globals()), version=__vstring__)
    a = convert_cmd_args(a)
    if a['test']: run_tests()
    logging.basicConfig(
        level   = a.verbose,
        format  = '[%(levelname)-7.7s] (%(asctime)s '
                  '%(filename)s:%(lineno)s) %(message)s',
        datefmt = '%y%m%d %H:%M'   #, stream=, mode=, filename=
    )
    write_ngrv_file( **a )


if __name__ == '__main__':
    main()
