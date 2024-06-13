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
from os import listdir

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QMessageBox,
)

from utils import (
    burn_cd_of_day,
    log,
)
from input import (
    validate_cd_record_config,
    RadioButtonDialog,
    InfoMsgBox,
)
import config as const


def choose_cd() -> list[str]:
    # pylint: disable=unused-variable
    app = QApplication([])
    try:
        dirs = sorted(listdir(const.CD_RECORD_OUTPUT_BASEDIR))
        dirs.reverse()

        if not dirs:
            return [
                f"Did not find any CD's in: {const.CD_RECORD_OUTPUT_BASEDIR}.",
                "",
            ]

        dialog = RadioButtonDialog(dirs, "Choose a CD to Burn")
        if dialog.exec_() == QDialog.Accepted:
            log(f"Burning CD for day: {dialog.chosen}")
            return ["", dialog.chosen]
        return ["ignore", ""]
    except (FileNotFoundError, PermissionError, IOError):
        pass

    return [
        f"Failed to access directory: {const.CD_RECORD_OUTPUT_BASEDIR}.",
        "",
    ]


def choose_and_burn_cd():
    msg, yyyy_mm_dd = choose_cd()
    if msg == "":
        burn_cd_of_day(yyyy_mm_dd)
    elif msg != "ignore":
        InfoMsgBox(QMessageBox.Critical, "Error", msg)


if __name__ == "__main__":
    validate_cd_record_config()
    choose_and_burn_cd()
