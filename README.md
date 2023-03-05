# GoodTFT GPIO Installer (Python)

A _very basic_ python utility that helps you set up a [GoodTFT mini GPIO touch display][2] on a Raspberry Pi desktop to mirror the HDMI display.
It is inspired by (i.e. copied heavily from) the [Adafruit PiTFT script][3].

See [compatibility](#compatibility) for information if your GPIO display is supported by the script.

## Usage

Install dependencies and run the script.

```shell
cd ~
sudo apt-get update
sudo apt-get install -y git python3-pip
sudo pip3 install --upgrade adafruit-python-shell click
git clone --depth=1 https://github.com/wallali/gTFTPy.git
cd gTFTPy
sudo python3 install.py
```

### Parameters

If run without parameters as shown above, the `install.py` script will prompt you for the options it needs.

Alternatively you can run this script with parameters preconfigured,

```shell
sudo python3 install.py --display=3501r --rotation=90 --install-type=fbcp
```

`--install-type=uninstall` should remove the changes made by the script.

To change to a different `--rotation` option you can run the script again and choose another rotation (90, 180, 270, 0).

## What does this script do?

- installs the "driver" for your display to `/boot/overlays/`
- installs necessary libraries for screen support like `fbi`, `tslib` and `libts-bin`
- tweaks `/boot/config.txt`
  - enables serial port (i2c)
  - adds display driver
  - sets up display rotation parameters
  - sets up a suitable custom HDMI resolution
- builds and installs [`fbcp`][4]
- configures `fbcp` service to run during startup
- configures X11 calibration for the touch screen support
- configures udev support for the touch device

## Why this utility

The [GoodTFT repo][1] probably contains the script to setup the [GoodTFT display][2] you have purchased.
However that code,

- overwrites files without backup
- installs unnecessary files, sometime duplicates
- does not configure `systemd` services correctly
- does not configure the default X11 `libinput` and instead fallback to `evdev` installing a local bundled package

While this script,

- changes `/boot/config.txt` in a minimal way
- keeps `/boot/config.txt` compatible with using raspi-config afterwards
- installs only necessary files
- works correctly with `systemd`
- configures `libinput` correctly, no need for falling back to `evdev`
- allows connecting both the HDMI and the GPIO display simultaneously in mirror mode

## Compatibility

| Display | OS | OS Version | Raspberry Pi |
| - | - | - | - |
| [MPI3501- XPT2046](http://www.lcdwiki.com/3.5inch_RPi_Display) 3.5" TFT 320*480 (Pixel) | Raspbian | GNU/Linux 11 (bullseye) | Raspberry Pi 3 Model B Rev 1.2 |
| [MPI3501- XPT2046](http://www.lcdwiki.com/3.5inch_RPi_Display) 3.5" TFT 320*480 (Pixel) | Raspbian | GNU/Linux 10 (buster) | Raspberry Pi 3 Model B Rev 1.2 |

## Support

There is very little I can do to support if this script does not work for you. Sorry. Because there are many versions of the Raspberry Pi board, many operating systems and many GPIO screens and I do not have the time or resources to test on all of them.

So chances are you will need to debug it yourself, find a fix and hopefully contribute back to improve this script.

Hopefully, there is enough information and resources here that can help you debug and find the problem.

### Adding support for a new display

If your display is supported by the [Good TFT scripts][1], start your understanding there by looking at what that script does. From it you can get the correct driver/overlay file and place it in `overlays` folder of this script. Then add a compatible config section for your display into this script (around line 44).

## Useful Commands

Check your Raspberry Pi model:

```shell
cat /sys/firmware/devicetree/base/model
```

Check your OS details:

```shell
cat /etc/os-release
```

See information about the touchscreen product

```shell
xinput --list
xinput --list-props #device_id
```

Run touch screen calibration utility

```shell
sudo ts_calibrate
```

## Helpful References

1. [Good TFT LCD-show scripts and driver overlays][1]
2. [Raspberry Pi LCD Wiki][2]
3. [Adafruit PiTFT Installer Python Script][3]
4. [Framebuffer Copy (fbcp) utility][4]
5. [Raspberry Pi HDMI mode configuration][5]
6. [`libinput` calibration][6]
7. [Matrix Structure for screen rotation][7]

[1]: https://github.com/goodtft/LCD-show
[2]: http://www.lcdwiki.com/
[3]: https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/blob/main/adafruit-pitft.py
[4]: https://github.com/tasanakorn/rpi-fbcp
[5]: https://www.raspberrypi.com/documentation/computers/configuration.html#setting-a-custom-hdmi-mode
[6]: https://github.com/swkim01/waveshare-dtoverlays/blob/master/README.md
[7]: https://unix.stackexchange.com/questions/138168/matrix-structure-for-screen-rotation

## Disclaimer
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
