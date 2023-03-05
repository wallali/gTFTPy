"""
GoodTFT Installer Script
Modified by Ali Lokhandwala to support GoodTFT 3.5 with XPT2046 Touch Controller
(C) Ali Lokhandwala, Creative Commons 3.0 - Attribution Share Alike

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
OTHER DEALINGS IN THE SOFTWARE.
"""

"""
Original script borrowed from Adafruit PiTFT Installer Script
(C) Adafruit Industries, Creative Commons 3.0 - Attribution Share Alike
Written in Python by Melissa LeBlanc-Williams for Adafruit Industries
https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/blob/main/adafruit-pitft.py
"""

import time
import os

try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: sudo pip3 install Click")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'GOODTFT'

__version__ = "1.0.0"

"""
This is the main configuration. Displays should be placed in the order
they are to appear in the menu.
"""
config = [  
    {
        "type": "3501r",
        "menulabel": "3.5” GoodTFT Display (MPI3501) resistive touch",
        "product": "3.5\" Resistive",
        "overlay_src": "./overlays/tft35a-overlay.dtb",
        "overlay_dest": "{boot_dir}/overlays/tft35a.dtbo",
        "touchscreen": {
            "identifier": "ADS7846 Touchscreen Calibration",
            "product": "ADS7846 Touchscreen",
            "transforms": {
                "0": "1.102807 0.000030 -0.066352 0.001374 1.085417 -0.027208 0 0 1",
                "90": "0.003893 -1.087542 1.025913 1.084281 0.008762 -0.060700 0 0 1",
                "180": "-1.098388 0.003455 1.052099 0.005512 -1.093095 1.026309 0 0 1",
                "270": "-0.000087 1.094214 -0.028826 -1.091711 -0.004364 1.057821 0 0 1",
            },
        },
        "overlay": "dtoverlay=tft35a,rotate={pitftrot},fps=60",
        "width": 480,
        "height": 320,
        "x11_scale": 2,
    },
]

# default rotations
fbcp_rotations = {
    "0": "1",
    "90": "0",
    "180": "3",
    "270": "2",
}

PITFT_ROTATIONS = ("90", "180", "270", "0")
UPDATE_DB = False
SYSTEMD = None
REMOVE_KERNEL_PINNING = False
pitft_config = None
pitftrot = None
auto_reboot = None

def warn_exit(message):
    shell.warn(message)
    shell.exit(1)

def uninstall_cb(ctx, param, value):
    if not value or ctx.resilient_parsing:
       return
    uninstall()

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
       return
    print("GoodTFT 3.5 Helper v{}".format(__version__))
    shell.exit(1)

def progress(ellipsis_count):
    for i in range(ellipsis_count):
        print("...", end='')
        time.sleep(1)
    print("")

def sysupdate():
    global UPDATE_DB
    if not UPDATE_DB:
        print("Updating apt indexes...", end='')
        progress(3)
        if not shell.run_command('sudo apt update', True):
            warn_exit("Apt failed to update indexes! Try running 'sudo apt update' manually.")
        if not shell.run_command('sudo apt-get update', True):
            warn_exit("Apt failed to update indexes! Try running 'sudo apt-get update' manually.")
        print("Reading package lists...")
        progress(3)
        UPDATE_DB = True
    return True

############################ Sub-Scripts ############################

def softwareinstall():
    print("Installing Pre-requisite Software...This may take a few minutes!")
    if not shell.run_command("apt-get install -y libts0", True):
        if not shell.run_command("apt-get install -y tslib"):
            if not shell.run_command("apt-get install -y libts-dev"):
                warn_exit("Apt failed to install TSLIB!")
    if not shell.run_command("apt-get install -y fbi git libts-bin build-essential"):
        warn_exit("Apt failed to install software!")
    return True

def uninstall_bootconfigtxt():
    """Remove any old flexfb/fbtft stuff"""
    if shell.pattern_search(f"{boot_dir}/config.txt", "goodtft-py-helper"):
        print(f"Already have an goodtft-py-helper section in {boot_dir}/config.txt.")
        print("Removing old section...")
        shell.run_command(f"cp {boot_dir}/config.txt {boot_dir}/configtxt.bak")
        shell.pattern_replace(f"{boot_dir}/config.txt", '\n# --- added by goodtft-py-helper.*?\n# --- end goodtft-py-helper.*?\n', multi_line=True)
    return True

def install_drivers():
    """Add display driver and overlay if required"""
    if "overlay_src" in pitft_config and "overlay_dest" in pitft_config:
        print("Adding display driver...")
        destination = pitft_config['overlay_dest'].format(boot_dir=boot_dir)
        if not shell.run_command("cp -rf {src} {dest}".format(dest=destination, src=pitft_config['overlay_src']), True):
            return False

    return True

def update_configtxt(rotation_override=None):
    """update /boot/config.txt (or equivalent folder) with appropriate values"""
    uninstall_bootconfigtxt()
    overlay = pitft_config['overlay']
    if "{pitftrot}" in overlay:
        rotation = str(rotation_override) if rotation_override is not None else pitftrot
        overlay = overlay.format(pitftrot=rotation)
    if "{rotation}" in overlay and isinstance(pitft_config['rotations'], dict) and pitft_config['rotations'][pitftrot] is not None:
        overlay = overlay.format(rotation=pitft_config['rotations'][pitftrot])

    shell.write_text_file(f"{boot_dir}/config.txt", """
# --- added by added by goodtft-py-helper {date} ---
[all]
{overlay}
# --- end added by goodtft-py-helper {date} ---
""".format(date=shell.date(), overlay=overlay))
    return True

def update_udev():
    shell.write_text_file("/etc/udev/rules.d/95-touchmouse.rules", """
SUBSYSTEM=="input", ATTRS{name}=="touchmouse", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"
""", append=False)
    return True

def install_fbcp():
    global fbcp_rotations
    if not shell.exists("/usr/local/bin/fbcp"):
        print("Installing cmake...")
        if not shell.run_command("apt-get --yes install cmake", True):
            warn_exit("Apt failed to install software!")
        
        print("Downloading rpi-fbcp...")
        shell.pushd("/tmp")
        if not shell.run_command("git clone --depth=1 https://github.com/tasanakorn/rpi-fbcp", True):
            warn_exit("Failed to git clone fbcp from https://github.com/tasanakorn/rpi-fbcp")
        shell.chdir("rpi-fbcp")
        shell.run_command("mkdir build")
        shell.chdir("build")
        print("Building rpi-fbcp...")
        if not shell.run_command("cmake ..", True):
            warn_exit("Failed to cmake fbcp!")
        if not shell.run_command("make", True):
            warn_exit("Failed to make fbcp!")
        print("Installing rpi-fbcp...")
        shell.run_command("install fbcp /usr/local/bin/fbcp")
        shell.popd()
        shell.run_command("rm -rf /tmp/rpi-fbcp")

    if "fbcp_rotations" in pitft_config:
        fbcp_rotations = pitft_config['fbcp_rotations']

    # Start fbcp in the appropriate place, depending on init system:
    if SYSTEMD:
        # Add fbcp to /etc/rc.local:
        print("We have sysvinit, so add fbcp to /etc/rc.local...")
        if shell.pattern_search("/etc/rc.local", "fbcp"):
            # fbcp already in rc.local, but make sure correct:
            shell.pattern_replace("/etc/rc.local", "^.*fbcp.*$", "/usr/local/bin/fbcp \&")
        else:
            # Insert fbcp into rc.local before final 'exit 0':
            shell.pattern_replace("/etc/rc.local", "^exit 0", "/usr/local/bin/fbcp \&\\nexit 0")
    else:
        # Install fbcp systemd unit, first making sure it's not in rc.local:
        uninstall_fbcp_rclocal()
        print("We have systemd, so install fbcp systemd unit...")
        if not install_fbcp_unit():
            shell.bail("Unable to install fbcp unit file")
        shell.run_command("sudo systemctl enable fbcp.service")

    # if there's X11 installed...
    if shell.exists("/etc/lightdm"):
        print("Setting raspi-config to boot to desktop w/o login...")
        shell.run_command("raspi-config nonint do_boot_behaviour B4")

    # Disable overscan compensation (use full screen):
    shell.run_command("raspi-config nonint do_overscan 1")
    # Set up HDMI parameters:
    print("Configuring boot/config.txt for forced HDMI")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=1")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_group.*$", "hdmi_group=2")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_mode.*$", "hdmi_mode=87")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^[^#]*dtoverlay=vc4-kms-v3d.*$", "#dtoverlay=vc4-kms-v3d")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^[^#]*dtoverlay=vc4-fkms-v3d.*$", "#dtoverlay=vc4-fkms-v3d")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtparam=spi=.*$", "dtparam=spi=on")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtparam=i2c_arm=.*$", "dtparam=i2c_arm=on")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtparam=i2c1=.*$", "dtparam=i2c1=on")

    # if there's X11 installed...
    scale = 1
    if shell.exists("/etc/lightdm"):
        if "x11_scale" in pitft_config:
            scale = pitft_config["x11_scale"]
        else:
            scale = 2
    WIDTH = int(pitft_config['width'] * scale)
    HEIGHT = int(pitft_config['height'] * scale)

    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_cvt.*$", "hdmi_cvt={} {} 60 1 0 0 0".format(WIDTH, HEIGHT))

    try:
        default_orientation = int(list(fbcp_rotations.keys())[list(fbcp_rotations.values()).index("0")])
    except ValueError:
        default_orientation = 90

    if fbcp_rotations[pitftrot] == "0":
        # dont rotate HDMI on default orientation
        shell.reconfig(f"{boot_dir}/config.txt", "^.*display_hdmi_rotate.*$", "")
    else:
        display_rotate = fbcp_rotations[pitftrot]
        shell.reconfig(f"{boot_dir}/config.txt", "^.*display_hdmi_rotate.*$", "display_hdmi_rotate={}".format(display_rotate))
        # Because we rotate HDMI we have to 'unrotate' the TFT by overriding pitftrot!
        if not update_configtxt(default_orientation):
            shell.bail(f"Unable to update {boot_dir}/config.txt")
    return True

def install_fbcp_unit():
    shell.write_text_file("/etc/systemd/system/fbcp.service",
    """[Unit]
Description=Framebuffer copy utility for GoodTFT
After=network.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 10
ExecStart=/usr/local/bin/fbcp

[Install]
WantedBy=multi-user.target
""", append=False)
    return True

def uninstall_fbcp():
    uninstall_fbcp_rclocal()
    # Enable overscan compensation
    shell.run_command("sudo systemctl disable fbcp.service")
    # Set up HDMI parameters:
    shell.run_command("raspi-config nonint do_overscan 0")
    print("Configuring boot/config.txt for default HDMI")
    shell.reconfig(f"{boot_dir}/config.txt", "^.*hdmi_force_hotplug.*$", "hdmi_force_hotplug=0")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtoverlay=vc4-kms-v3d.*$", "dtoverlay=vc4-kms-v3d")
    shell.pattern_replace(f"{boot_dir}/config.txt", "^.*#.*dtoverlay=vc4-fkms-v3d.*$", "dtoverlay=vc4-fkms-v3d")
    shell.pattern_replace(f"{boot_dir}/config.txt", '^hdmi_group=2.*$')
    shell.pattern_replace(f"{boot_dir}/config.txt", '^hdmi_mode=87.*$')
    shell.pattern_replace(f"{boot_dir}/config.txt", '^hdmi_cvt=.*$')
    return True

def uninstall_fbcp_rclocal():
    """Remove fbcp from /etc/rc.local:"""
    print("Remove fbcp from /etc/rc.local, if it's there...")
    shell.pattern_replace("/etc/rc.local", '^.*fbcp.*$')
    return True

def update_xorg():
    if "touchscreen" in pitft_config:
        transform = "Option \"TransformationMatrix\" \"{}\"".format(pitft_config["touchscreen"]["transforms"][pitftrot])
        shell.write_text_file("/usr/share/X11/xorg.conf.d/20-calibration.conf", """
Section "InputClass"
        Identifier "{identifier}"
        MatchProduct "{product}"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
        {transform}
EndSection
""".format(
            identifier=pitft_config["touchscreen"]["identifier"],
            product=pitft_config["touchscreen"]["product"],
            transform=transform
        ),
        append=False,
    )
    return True

def get_config_types():
    types = []
    for item in config:
        types.append(item["type"])
    return types

def get_config(type):
    for item in config:
        if item["type"] == type:
            return item
    return None

def uninstall():
    shell.info("Uninstalling PiTFT")
    uninstall_bootconfigtxt()
    uninstall_fbcp()
    uninstall_fbcp_rclocal()
    success()

def success():
    global auto_reboot
    shell.info("Success!")
    print("""
Settings take effect on next boot.
""")
    if auto_reboot is None:
        auto_reboot = shell.prompt("REBOOT NOW?", default="y")
    if not auto_reboot:
        print("Exiting without reboot.")
        shell.exit()
    print("Reboot started...")
    shell.reboot()
    shell.exit()

####################################################### MAIN
target_homedir = "/home/pi"
username = os.environ["SUDO_USER"]
user_homedir = os.path.expanduser(f"~{username}")
if shell.isdir(user_homedir):
    target_homedir = user_homedir

boot_dir = "/boot"
@click.command()
@click.option('-v', '--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Print version information")
@click.option('-u', '--user', nargs=1, default=target_homedir, type=str, help="Specify path of primary user's home directory", show_default=True)
@click.option('--display', nargs=1, default=None, help="Specify a display option (1-{}) or type {}".format(len(config), get_config_types()))
@click.option('--rotation', nargs=1, default=None, type=int, help="Specify a rotation option (1-4) or degrees {}".format(tuple(sorted([int(x) for x in PITFT_ROTATIONS]))))
@click.option('--install-type', nargs=1, default=None, type=click.Choice(['fbcp', 'uninstall']), help="Installation Type")
@click.option('--reboot', nargs=1, default=None, type=click.Choice(['yes', 'no']), help="Specify whether to reboot after the script is finished")
@click.option('--boot', nargs=1, default="/boot", type=str, help="Specify the boot directory", show_default=True)
def main(user, display, rotation, install_type, reboot, boot):
    global target_homedir, pitft_config, pitftrot, auto_reboot, boot_dir
    shell.clear()
    if user != target_homedir:
        target_homedir = user
        print(f"Homedir = {target_homedir}")
    if boot != boot_dir:
        if shell.isdir(boot):
            boot_dir = boot
            print(f"Boot dir = {boot_dir}")
        else:
            print(f"{boot} not found or not a directory. Using {boot_dir} instead.")


    print("""This script downloads and installs
GoodTFT Support using userspace touch
controls and a DTO for display drawing.
Run time of up to 5 minutes. Reboot required!
""")
    if reboot is not None:
        auto_reboot = reboot.lower() == 'yes'

    if install_type == "uninstall":
        uninstall()

    if display in [str(x) for x in range(1, len(config) + 1)]:
        pitft_config = config[int(display) - 1]
        print("Display Type: {}".format(pitft_config["menulabel"]))
    elif display in get_config_types():
        pitft_config = get_config(display)
        print("Display Type: {}".format(pitft_config["menulabel"]))
    else:
        # Build menu from config
        selections = []
        for item in config:
            option = "{} ({}x{})".format(item['menulabel'], item['width'], item['height'])
            selections.append(option)
        selections.append("Uninstall PiTFT")
        selections.append("Quit without installing")

        PITFT_SELECT = shell.select_n("Select configuration:", selections)
        if PITFT_SELECT == len(config) + 2:
            shell.exit(1)
        if PITFT_SELECT == len(config) + 1:
            uninstall()
        pitft_config = config[PITFT_SELECT - 1]

    if rotation is not None and 1 <= rotation <= 4:
        pitftrot = PITFT_ROTATIONS[rotation - 1]
        print("Rotation: {}".format(pitftrot))
    elif str(rotation) in PITFT_ROTATIONS:
        pitftrot = str(rotation)
        print("Rotation: {}".format(pitftrot))
    else:
        PITFT_ROTATE = shell.select_n(
        "Select rotation:", (
            "90 degrees (landscape)",
            "180 degrees (portrait)",
            "270 degrees (landscape)",
            "0 degrees (portrait)"
        ))
        pitftrot = PITFT_ROTATIONS[PITFT_ROTATE - 1]

    if 'rotations' in pitft_config and isinstance(pitft_config['rotations'], dict) and pitftrot in pitft_config['rotations'] and pitft_config['rotations'][pitftrot] is None:
        shell.bail("""Unfortunately {rotation} degrees for the {display} is not working at this time. Please
restart the script and choose a different orientation.""".format(rotation=pitftrot, display=pitft_config["menulabel"]))

    # check init system (technique borrowed from raspi-config):
    shell.info('Checking init system...')
    if shell.run_command("which systemctl", True) and shell.run_command("systemctl | grep '\-\.mount'", True):
      SYSTEMD = True
      print("Found systemd")
    elif os.path.isfile("/etc/init.d/cron") and not os.path.islink("/etc/init.d/cron"):
      SYSTEMD = False
      print("Found sysvinit")
    else:
      shell.bail("Unrecognised init system")

    if shell.grep("boot", "/proc/mounts"):
        print("/boot is mounted")
    else:
        print("/boot must be mounted. if you think it's not, quit here and try: sudo mount /dev/mmcblk0p1 /boot")
        if shell.prompt("Continue?"):
            print("Proceeding.")
        else:
            shell.bail("Aborting.")

    if not shell.isdir(target_homedir):
        shell.bail("{} must be an existing directory (use -u /home/foo to specify)".format(target_homedir))

    shell.info("System update")
    if not sysupdate():
        shell.bail("Unable to apt-get update")

    shell.info("Installing Python libraries & Software...")
    if not softwareinstall():
        shell.bail("Unable to install software")

    if "overlay_src" in pitft_config and "overlay_dest" in pitft_config:
        shell.info("Installing display drivers and device tree overlay...")
        if not install_drivers():
            shell.bail("Unable to install display drivers")

    shell.info(f"Updating {boot_dir}/config.txt...")
    if not update_configtxt():
        shell.bail(f"Unable to update {boot_dir}/config.txt")

    if "touchscreen" in pitft_config:
        shell.info("Updating SysFS rules for Touchscreen...")
        if not update_udev():
            shell.bail("Unable to update /etc/udev/rules.d")

    if install_type == "fbcp" or (install_type is None and shell.prompt("Would you like the HDMI display to mirror to the PiTFT display?")):
        shell.info("Adding FBCP support...")
        if not install_fbcp():
            shell.bail("Unable to configure fbcp")

        if shell.exists("/etc/lightdm"):
            shell.info("Updating X11 default calibration...")
            if not update_xorg():
                shell.bail("Unable to update calibration")
    else:
        if not uninstall_fbcp():
            shell.bail("Unable to uninstall fbcp")

    success()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()