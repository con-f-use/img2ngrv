#!/usr/bin/python
from __future__ import division, print_function
from setuptools import setup
import os, re, ast, subprocess, fileinput

infln = 'img2ngrv.py'

def get_field(field):
    regex = re.compile(r'^\s*__'+field+r'__\s*=\s*(.*)', flags=re.M)
    with open(infln, 'rb') as f:
        value = str( ast.literal_eval(
            regex.search( f.read().decode('utf-8') ).group(1)   ) )
    return value

try:
    vstr = subprocess.check_output('git describe --abbrev=5 --dirty=exp --always --tags'.split())
    _version = ' '.join(vstr.decode('ascii', 'ignore').split())
    r = re.compile(r'^'+
            r'v?(?P<tag>\d+(\.\d+)*)'+
            r'(-(?P<commit>\d+))?'+
            r'(-g(?P<hash>[a-fA-F0-9]{5,}))?'+
            r'(?P<exp>exp)?$' )
    m = [v.groupdict() for v in r.finditer(_version)]
    if m:
        m = m[0]
        _version = m['tag']
        if m['commit']: _version += '.dev'+ m['commit']
        if m['hash']:   _version += '+'+ m['hash']
        if m['exp']:    _version += '.'+ m['exp']
        flnm = os.path.join(os.path.dirname(__file__), infln)
        for line in fileinput.input(flnm, inplace=True, backup='.bak'):
            line = re.sub(
                r'^(\s*__version__\s*=\s*[\'"]).*?([\'"].*)$',
                r'\g<1>'+ str(_version) +r'\g<2>',
                line
            )
            print(line.strip('\n'))
except subprocess.CalledProcessError: pass

setup(
    name             = 'img2ngrv',
    version          = _version,
    author           = get_field('author'),
    author_email     = get_field('author_email'),
    description      = ('Iamge to Engraver Raster'),
    license          = 'Creative Common Attribution 4.0',
    keywords         = '3D-printing engraving G-code',
    url              = get_field('url'),
    py_modules       = ['img2ngrv'],
    install_requires = ['docopt','numpy','matplotlib','cairosvg','pint','pillow'],
    zip_safe         = False,
    entry_points='''
        [console_scripts]
        img2ngrv=img2ngrv:main
    ''',
)
