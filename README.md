img2ngrv - Image to Engraver Raster &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [![Build Status](https://travis-ci.org/con-f-use/img2ngrv.png?branch=master)](https://travis-ci.org/con-f-use/img2ngrv) [![Build Status](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)
=======================

Convert a pixel or vector image to [G-code](https://en.wikipedia.org/wiki/G-code) as commonly used by home-made (laser) engraving machines.

This particular code is tested with the [LulzBot](https://www.lulzbot.com/)
3D printers modified for laser engraving with one of the kits sold by
[J Tech Photonics](https://jtechphotonics.com/). The software is similar in end result to their
[LaserEtch](https://jtechphotonics.com/?product=laser-etch-bw-image-engraving-sw-license)
tool. For other engraves, you will have to teak the (G-)code manually,
especially the preamble. Luckily the program is contained in one python file.

# Usage

To install img2ngrv, you will need a copy of the code. Either download it
from the release section of [github](https://github.com/con-f-use/img2ngrv)
or run:

    git clone git@github.com:con-f-use/img2ngrv.git

After to you received a copy and uzipped the code, run:

    ./setup.py install   # --user
    # or
    # pip install --editable .

Once done, you should be able to get a the programs usage with:

    img2ngrv --help



License and Disclaimer
=======================

Copyright (c) 2016 con-f-use@gmx.net

The project along with all files in this repository are owned by the copy right holder. The content of this repository can be used under the <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>..

A copy of the license should be included with the distribution of this text.
If not, visit http://creativecommons.org/licenses/by/4.0/.

<sub>
THE WORK INCLUDING ANY DERIVED HARDWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
</sub>
