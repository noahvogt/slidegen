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

import colorama
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)

from utils import (
    make_sure_file_exists,
)
from song_switcher import switch_to_song
from input import validate_obs_song_scene_switcher_config, InfoMsgBox
import config as const


# pylint: disable=inconsistent-return-statements
def get_force_int() -> int:
    try:
        return int(sys.argv[1])
    except IndexError:
        app = QApplication
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            "couldn't parse force song integer",
        )
        del app
        sys.exit(1)


def exit_if_force_int_is_illegal():
    force_int = get_force_int()
    msg = ""
    if force_int > const.OBS_MIN_SUBDIRS:
        msg = f"force integer {force_int} too big"
    if force_int < 1:
        msg = f"force integer {force_int} cannot be smaller than 1"
    if msg != "":
        app = QApplication
        InfoMsgBox(QMessageBox.Critical, "Error", msg)
        del app
        sys.exit(1)


if __name__ == "__main__":
    colorama.init()
    validate_obs_song_scene_switcher_config()
    make_sure_file_exists(const.NEXTSONG_CACHE_FILE, gui_error_out=True)
    exit_if_force_int_is_illegal()
    switch_to_song(get_force_int())
