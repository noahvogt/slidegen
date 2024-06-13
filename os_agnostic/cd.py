"""
Copyright © 2022 Noah Vogt <noah@noahvogt.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

from utils import log

if os.name == "nt":
    # pylint: disable=import-error
    import wmi  # pyright: ignore
else:
    from pycdio import DRIVER_DEVICE
    from cdio import (
        get_devices,
        Device,
        DriverUnsupportedError,
        DeviceException,
    )


def get_cd_drives() -> list:
    if os.name == "nt":
        c = wmi.WMI()
        cd_drives = []
        for cd in c.Win32_CDROMDrive():
            cd_drives.append(cd.Drive)
    # pylint: disable=possibly-used-before-assignment
    else:
        cd_drives = get_devices(DRIVER_DEVICE)
    return cd_drives


# pylint: disable=possibly-used-before-assignment
def eject_drive(drive: Device) -> None:  # pyright: ignore
    try:
        drive.eject_media()  # pyright: ignore
    # pylint: disable=possibly-used-before-assignment
    except (DriverUnsupportedError, DeviceException):
        log(f"Eject of CD-ROM drive {drive} failed")  # pyright: ignore
