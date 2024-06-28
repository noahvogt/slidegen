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

import sys
import os

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
    QDialog,
)

from utils import log, CustomException, RadioButtonDialog

if os.name == "nt":
    # pylint: disable=import-error
    import wmi  # pyright: ignore
    import ctypes
    from subprocess import PIPE, run
    from re import match, search
    import config as const
else:
    from pycdio import DRIVER_DEVICE
    from cdio import (
        get_devices,
        DriverUnsupportedError,
        DeviceException,
    )


def choose_right_scsi_drive(drives: list) -> str:
    if len(drives) != 1:
        log("Warning: More than one SCSI drive found", color="yellow")
        if (
            # pylint: disable=possibly-used-before-assignment
            const.CD_RECORD_PREFERED_SCSI_DRIVE in drives
            and const.CD_RECORD_PREFERED_SCSI_DRIVE != ""
        ):
            return const.CD_RECORD_PREFERED_SCSI_DRIVE

        # pylint: disable=possibly-used-before-assignment
        dialog = RadioButtonDialog(drives, "Choose a SCSI Drive")
        if dialog.exec_() == QDialog.Accepted:
            log(f"Dialog accepted: {dialog.chosen}")
            return dialog.chosen
        log("Warning: Choosing first SCSI drive...", color="yellow")

    return drives[0]


def get_cdrecord_devname(cd_drive: str) -> str:
    if os.name == "nt":
        scsi_drives = get_scsi_drives()
        return choose_right_scsi_drive(scsi_drives)

    return cd_drive


def bytes_line_ends_with(line: bytes, target: str) -> bool:
    byte_len = len(line)
    if byte_len < len(target):
        return False

    if len(target) == 1 and ord(target[0]) != line[-1]:
        return False

    for index in range(-1, -1 * len(target), -1):
        if ord(target[index]) != line[index]:
            return False

    return True


def get_scsi_drives() -> list[str]:
    # pylint: disable=possibly-used-before-assignment, subprocess-run-check
    try:
        drives = []
        result = run(["cdrecord", "-scanbus"], stdout=PIPE)
        output = result.stdout
        if result.returncode != 0:
            raise CustomException("Command 'cdrecord -scanbus' failed.")
        for line in output.split(b"\n"):
            # pylint: disable=possibly-used-before-assignment
            if (
                match(rb"\s*[0-9](,[0-9])+\s*[0-9]+", line)
                and (not bytes_line_ends_with(line, "*"))
                and (not bytes_line_ends_with(line, "HOST ADAPTOR"))
            ):
                matches = search(rb"[0-9](,[0-9])+", line)
                if matches is None:
                    raise CustomException(f"could not parse line: '{line}'")
                drives.append(matches.group().decode("ascii"))

        if not drives:
            raise CustomException("Could not find any SCSI drives")

        return drives
    except CustomException as error:
        app = QApplication([])
        QMessageBox.critical(
            None,
            "Error",
            f"Could not get SCSI drives. Reason: {error}",
        )
        del app
        sys.exit(1)


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
