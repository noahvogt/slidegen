#!/usr/bin/env python3

"""
Copyright © 2024 Noah Vogt <noah@noahvogt.com>

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

import sys
from subprocess import Popen
from shlex import split

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import QTimer  # pylint: disable=no-name-in-module

from pycdio import DRIVER_DEVICE
from cdio import get_devices, Device, DriverUnsupportedError, DeviceException

from utils import (
    make_sure_file_exists,
    log,
)
from input import validate_cd_record_config
import config as const


class InfoMsgBox:
    def __init__(self, icon: QMessageBox.Icon, title: str, text: str) -> None:
        self.app = QApplication([])
        self.title = title
        self.text = text
        self.icon = icon
        self.show_msg_box()
        self.app.exec_()

    def show_msg_box(self):
        self.message_box = QMessageBox()
        self.message_box.setIcon(self.icon)
        self.message_box.setWindowTitle(self.title)
        self.message_box.setText(self.text)

        self.message_box.show()


class CDBurnerGUI:
    def __init__(self, drive: Device):
        self.app = QApplication([])
        self.drive = drive
        self.exit_code = 1
        self.show_burning_msg_box()
        self.start_burn_subprocess()
        self.app.exec_()

    def burning_successful(self) -> bool:
        if self.exit_code == 0:
            return True
        return False

    def show_burning_msg_box(self):
        self.message_box = QMessageBox()
        self.message_box.setWindowTitle("Info")
        self.message_box.setText("Burning CD...")
        self.message_box.setInformativeText(
            "Please wait for a few minutes. You can close this Window, as "
            + "there will spawn another window after the operation is "
            + "finished."
        )

        self.message_box.show()

    def start_burn_subprocess(self):
        process = Popen(["grep", "-a"])

        while process.poll() is None:
            QApplication.processEvents()
        self.message_box.accept()

        # Yeah this is hacky but it doesn't work when calling quit directly
        QTimer.singleShot(0, self.app.quit)
        self.exit_code = process.returncode


def get_cd_drives() -> list:
    cd_drives = get_devices(DRIVER_DEVICE)
    return cd_drives


def eject_drive(drive: Device) -> None:
    try:
        drive.eject_media()
    except (DriverUnsupportedError, DeviceException):
        log(f"Eject of CD-ROM drive {drive} failed")


if __name__ == "__main__":
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE)

    drives = get_cd_drives()
    if not drives:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            "Error: Could not find a CD-ROM. Please try again",
        )
        sys.exit(1)
    if len(drives) != 1:
        # TODO: let user choose between drive slots / letters / devices
        log("Warning: More than one cd drive found", color="yellow")
        drives = drives[0]

    BURN_SUCESS = CDBurnerGUI(drives[0]).burning_successful()
    if BURN_SUCESS:
        InfoMsgBox(QMessageBox.Info, "Info", "Successfully burned CD.")
    else:
        InfoMsgBox(QMessageBox.Critical, "Error", "Error: Failed to burn CD.")

    eject_drive(drives[0])
