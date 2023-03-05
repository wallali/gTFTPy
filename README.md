# GoodTFT GPIO Installer (Python)

A _very basic_ python utility that helps you set up a [GoodTFT mini GPIO touch display][2] on a Raspberry Pi desktop to mirror the HDMI display.
It is inspired by (i.e. copied heavily from) the [Adafruit PiTFT script][3].

See [compatibility](#compatibility) for information if your GPIO display is supported by the script. 
If it's not-- dont give up so easily; try [adding support for your display](#adding-support-for-a-new-display).

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

If it's run without parameters, the `install.py` script will prompt you for the options it needs. It's friendly-- thanks Adafruit!

Alternatively you can run this script with parameters preconfigured, like this,

```shell
sudo python3 install.py --display=3501r --rotation=90 --install-type=fbcp
```

`--install-type=uninstall` should remove the changes made by the script.

To change to a different `--rotation` option you can run the script again and choose another rotation (90, 180, 270, 0).

## What does this script do?

- installs the "driver" for your display to [`/boot/overlays/`][8]
- installs some libraries for screen support like `fbi`, `tslib` and `libts-bin`
- tweaks `/boot/config.txt`
  - enables serial port (i2c)
  - adds display driver
  - sets up display rotation parameters
  - sets up a suitable custom HDMI resolution
- builds and installs [`fbcp`][4] (for HDMI mirroring)
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

Hopefully, I can give enough information and resources here that can help you find a solution. And it's more fun that way!

### Adding support for a new display

If your display is supported by the [Good TFT scripts][1], start your understanding there by looking at what that script does. From it you can get the correct driver/overlay files and parameters and use them in this script. You can add a compatible config section for your display into this script (around line 44). Did you get it to work? Wow, well done you! Now consider contributing your work back to this repo.

```py
config = [  
    {
        "type": "MHS3528r",                                   # short name, can be used on the command line
        "menulabel": "3.5” MHS resistive touch",
        "product": "3.5\" Resistive",
        "overlay_src": "./overlays/mhs35-overlay.dtb",        # driver file. do you need it (ls /boot/overlays/)? If yes, you can get these from GoodTFT repo.
        "overlay_dest": "{boot_dir}/overlays/mhs35.dtbo",     # This must match to the name used in the overlay section below
        "touchscreen": {
            "identifier": "ADS7846 Touchscreen Calibration",  
            "product": "ADS7846 Touchscreen",                 # xinput could tell you this
            "transforms": {                                   # hmm, tricky stuff, need to work out the correct values for your display. Try libinput calibration
                "0": "1.102807 0.000030 -0.066352 0.001374 1.085417 -0.027208 0 0 1",
                "90": "0.003893 -1.087542 1.025913 1.084281 0.008762 -0.060700 0 0 1",
                "180": "-1.098388 0.003455 1.052099 0.005512 -1.093095 1.026309 0 0 1",
                "270": "-0.000087 1.094214 -0.028826 -1.091711 -0.004364 1.057821 0 0 1",
            },
        },
        "overlay": "dtoverlay=tft35a,rotate={pitftrot},fps=60", # match filename with overlay_dest or an existing /boot/overlays/, without extension
        "width": 480,           # what your display supports
        "height": 320,          # what your display supports
        "x11_scale": 2,         # HDMI resolution scaling: 1.5, 2, ... 
    },
]
```

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
8. [RPi Device Tree and Overlays Information][8]

[1]: https://github.com/goodtft/LCD-show
[2]: http://www.lcdwiki.com/
[3]: https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/blob/main/adafruit-pitft.py
[4]: https://github.com/tasanakorn/rpi-fbcp
[5]: https://www.raspberrypi.com/documentation/computers/config_txt.html#custom-mode
[6]: https://github.com/swkim01/waveshare-dtoverlays/blob/master/README.md
[7]: https://unix.stackexchange.com/questions/138168/matrix-structure-for-screen-rotation
[8]: https://www.embeddedpi.com/documentation/installing-linux-os/mypi-industrial-raspberry-pi-device-tree-overlays

## Disclaimer
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
