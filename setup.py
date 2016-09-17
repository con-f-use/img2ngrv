#!/usr/bin/python
from __future__ import division, print_function
from setuptools import setup

setup(
    name             = 'img2ngrv',
    version          = 0.5,
    author           = 'con-f-use',
    author_email     = 'con-f-use@gmx.net',
    description      = ('Iamge to Engraver Raster'),
    license          = 'Creative Common Attribution 4.0',
    keywords         = '3D-printing engraving G-code',
    url              = 'https://github.com/con-f-use/img2ngrv',
    py_modules       = ['img2ngrv'],
    install_requires = ['docopt','numpy','matplotlib','cairosvg','pint','pillow'],
    zip_safe         = False,
    entry_points='''
        [console_scripts]
        img2ngrv=img2ngrv:main
    ''',
)
