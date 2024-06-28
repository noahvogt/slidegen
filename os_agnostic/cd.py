# Copyright © 2024 Noah Vogt <noah@noahvogt.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from utils import log, CustomException

if os.name == "nt":
    # pylint: disable=import-error
    import wmi  # pyright: ignore
    import ctypes
else:
    from pycdio import DRIVER_DEVICE
    from cdio import (
        get_devices,
        DriverUnsupportedError,
        DeviceException,
    )


def get_cd_drives() -> list[str]:
    if os.name == "nt":
        c = wmi.WMI()
        cd_drives = []
        for cd in c.Win32_CDROMDrive():
            cd_drives.append(cd.Drive)
    # pylint: disable=possibly-used-before-assignment
    else:
        raw_cd_drives = get_devices(DRIVER_DEVICE)
        cd_drives = []
        for cd in raw_cd_drives:
            cd_drives.append(str(cd.get_device()))
    return cd_drives


# pylint: disable=possibly-used-before-assignment
def eject_drive(drive: str) -> None:  # pyright: ignore
    if os.name == "nt":
        ctypes.windll.WINMM.mciSendStringW(
            f"open {drive} type cdaudio alias d_drive", None, 0, None
        )
        ctypes.windll.WINMM.mciSendStringW(
            "set d_drive door open", None, 0, None
        )
    else:
        try:
            raw_drives = get_devices(DRIVER_DEVICE)
            drive_ejected = False
            for cd in raw_drives:
                if str(cd.get_device()) == drive:
                    drive.eject_media()  # pyright: ignore
                    drive_ejected = True
            if not drive_ejected:
                raise CustomException(f"Drive {drive} not found")
        # pylint: disable=possibly-used-before-assignment
        except (DriverUnsupportedError, DeviceException, CustomException):
            log(f"Eject of CD-ROM drive {drive} failed")  # pyright: ignore
