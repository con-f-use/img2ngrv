[![Build Status](https://travis-ci.org/con-f-use/img2ngrv.png?branch=master)](https://travis-ci.org/con-f-use/img2ngrv)

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

    ./setup.py install   # --user # --editable

Once done, you should be able to get a discripts of the programs usage with:

    img2ngrv --help

## License

Copyright (c) 2016 con-f-use@gmx.net

The project concept along with all files in this repository are owned by the copy right holder. The content of this repository is licensed under the Creative Commons Attribution 4.0 International License.

A copy of this license should be included with the distribution of this text.
If not, visit http://creativecommons.org/licenses/by/4.0/.

THE WORK INCLUDING ANY DERIVED HARDWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" property="dct:title">WeightWatcher</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="https://github.com/con-f-use/img2ngrv" property="cc:attributionName" rel="cc:attributionURL">con-f-use</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.
