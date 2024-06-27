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
from os import path
from re import match

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QMessageBox,
)

import config as const
from utils import get_yyyy_mm_dd_date
from input import InfoMsgBox, get_cachefile_content


def is_valid_cd_record_checkfile(
    cachefile_content: list, yyyy_mm_dd: str
) -> bool:
    return (
        len(cachefile_content) == 6
        # YYYY-MM-DD
        and bool(match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0]))
        # last set marker
        and bool(match(r"^[0-9][0-9]?$", cachefile_content[1]))
        # pid of ffmpeg recording instance
        and bool(match(r"^[0-9]+$", cachefile_content[2]))
        # unix milis @ recording start
        and bool(match(r"^[0-9]+$", cachefile_content[3]))
        # unix milis @ last track
        and bool(match(r"^[0-9]+$", cachefile_content[4]))
        # cd number
        and bool(match(r"^[0-9]+$", cachefile_content[5]))
        # date matches today
        and cachefile_content[0].strip() == yyyy_mm_dd
    )


def make_sure_there_is_no_ongoing_cd_recording() -> None:
    if path.isfile(const.CD_RECORD_CACHEFILE):
        cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
        if is_valid_cd_record_checkfile(
            cachefile_content, get_yyyy_mm_dd_date()
        ):
            if cachefile_content[1].strip() != "9001":
                InfoMsgBox(
                    QMessageBox.Critical,
                    "Error",
                    "Error: Ongoing CD Recording detected",
                )
                sys.exit(1)


def is_legal_sheet_filename(filename: str) -> bool:
    return bool(match(r"^sheet-[0-9]+\.cue", filename)) and len(filename) == 17


def get_padded_cd_num_from_sheet_filename(filename: str) -> str:
    if not is_legal_sheet_filename(filename):
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: filename '{filename}' in illegal format",
        )
        sys.exit(1)

    return filename[6:13]
