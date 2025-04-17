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
from re import match
from enum import Enum

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from utils import (
    log,
    get_current_yyyy_mm_dd_date,
    expand_dir,
    InfoMsgBox,
)
from input import get_cachefile_content
import config as const
from .obs import change_to_song_scene


class SongDirection(Enum):
    PREVIOUS = "previous"
    NEXT = "next"


def cycle_to_song_direction(song_direction: SongDirection):
    cachefile_content = get_cachefile_content(const.NEXTSONG_CACHE_FILE)
    if song_direction == SongDirection.PREVIOUS:
        step = -1
    else:
        step = 1
    if (
        not (
            len(cachefile_content) == 2
            and match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0])
            and match(r"^[0-9]+$", cachefile_content[1])
        )
        or cachefile_content[0].strip() != get_current_yyyy_mm_dd_date()
    ):
        switch_to_song(1)
    else:
        switch_to_song(int(cachefile_content[1]) + step)


def switch_to_song(song_number: int) -> None:
    if song_number > const.OBS_MIN_SUBDIRS:
        song_number = 1
    if song_number < 1:
        song_number = const.OBS_MIN_SUBDIRS
    change_to_song_scene(song_number)
    create_cachfile_for_song(song_number)


def create_cachfile_for_song(song) -> None:
    log("writing song {} to cachefile...".format(song))
    cachefile = expand_dir(const.NEXTSONG_CACHE_FILE)
    try:
        with open(cachefile, mode="w", encoding="utf-8-sig") as file_writer:
            file_writer.write(get_current_yyyy_mm_dd_date() + "\n")
            file_writer.write(str(song) + "\n")
    except (FileNotFoundError, PermissionError, IOError) as error:
        app = QApplication
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            "Failed to write to cachefile '{}'. Reason: {}".format(
                cachefile, error
            ),
        )
        del app
        sys.exit(1)
