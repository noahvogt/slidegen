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

from os import path

from pyautogui import hotkey

from utils import error_msg, log, calculate_yyyy_mm_dd_date
import config as const


def make_sure_cachefile_exists() -> None:
    if not path.isfile(const.NEXTSONG_CACHE_FILE):
        try:
            with open(
                const.NEXTSONG_CACHE_FILE, mode="w+", encoding="utf8"
            ) as file_creator:
                file_creator.write("")
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                "Failed to create cachefile in '{}'. Reason: {}".format(
                    const.NEXTSONG_CACHE_FILE, error
                )
            )


def switch_to_song(song: int) -> None:
    if song > const.OBS_MIN_SUBDIRS:
        song = 1
    log("sending hotkey Ctr + Shift + F{}".format(song), color="cyan")
    hotkey("ctrl", "shift", "f{}".format(song))
    create_cachfile_for_song(song)


def create_cachfile_for_song(song) -> None:
    log("writing song {} to cachefile...".format(song))
    try:
        with open(
            const.NEXTSONG_CACHE_FILE, mode="w", encoding="utf8"
        ) as file_writer:
            file_writer.write(calculate_yyyy_mm_dd_date() + "\n")
            file_writer.write(str(song) + "\n")
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to write to cachefile '{}'. Reason: {}".format(
                const.NEXTSONG_CACHE_FILE, error
            )
        )
