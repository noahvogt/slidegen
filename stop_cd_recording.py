#!/usr/bin/env python3

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
from os import kill
from signal import SIGTERM
from time import sleep

import colorama
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)

from utils import (
    get_yyyy_mm_dd_date,
    make_sure_file_exists,
    get_unix_milis,
    warn,
    expand_dir,
)
from input import get_cachefile_content, validate_cd_record_config, InfoMsgBox
import config as const
from recording import is_valid_cd_record_checkfile, mark_end_of_recording


def stop_cd_recording() -> None:
    filename = expand_dir(const.CD_RECORD_CACHEFILE)
    cachefile_content = get_cachefile_content(filename)
    yyyy_mm_dd = get_yyyy_mm_dd_date()

    if is_valid_cd_record_checkfile(cachefile_content, yyyy_mm_dd):
        unix_milis = get_unix_milis()
        last_track_milis = int(cachefile_content[4])
        milis_diff = unix_milis - last_track_milis
        if milis_diff < const.CD_RECORD_MIN_TRACK_MILIS:
            warn(
                f"Minimum track length of {const.CD_RECORD_MIN_TRACK_MILIS}"
                + "ms not satisfied, sleeping until reached..."
            )
            sleep(milis_diff / 1000 + 1)

        try:
            kill(int(cachefile_content[2]), SIGTERM)
        except ProcessLookupError:
            app = QApplication
            InfoMsgBox(
                QMessageBox.Critical,
                "Error",
                "Recording not running, cannot be stopped.",
            )
            del app
            sys.exit(1)
        mark_end_of_recording(cachefile_content)
    else:
        app = QApplication
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"CD Record Checkfile {filename} is invalid.",
        )
        del app
        sys.exit(1)


if __name__ == "__main__":
    colorama.init()
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE, gui_error_out=True)
    stop_cd_recording()
