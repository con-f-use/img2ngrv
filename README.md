# img2ngrv - Iamge to Engraver Raster

Convert a pixel or vector image to [G-code](https://en.wikipedia.org/wiki/G-code) as commonly used by home-made (laser) engraving machines.

This particular code is tested with the [LulzBot](https://www.lulzbot.com/)
3D printers modified for laser engraving with one of the kits sold by
[J Tech Photonics](https://jtechphotonics.com/). The software is similar in end result to their
[LaserEtch](https://jtechphotonics.com/?product=laser-etch-bw-image-engraving-sw-license)
tool.

img2ngrv might support grayscale engraving once the demand arises.

# Usage

To install img2ngrv, you will need a copy of the code. Either download it
from the release section of [github](https://github.com/con-f-use/img2ngrv)
or run:

    git clone git@github.com:con-f-use/img2ngrv.git

After to you received a copy and uzipped the code, run:

    ./setup.py install

Once done, you should be able to get a discripts of the programs usage with:

    img2ngrv --help
