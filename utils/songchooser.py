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
from time import sleep

from pyautogui import keyDown, keyUp

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


def switch_to_song(song_number: int) -> None:
    if song_number > const.OBS_MIN_SUBDIRS:
        song_number = 1
    log("sending hotkey to switch to scene {}".format(song_number), "cyan")
    scene_switch_hotkey = list(const.OBS_SWITCH_TO_SCENE_HOTKEY_PREFIX)
    scene_switch_hotkey.append("f{}".format(song_number))
    safe_send_hotkey(scene_switch_hotkey)

    log("sending hotkey to transition to scene {}".format(song_number), "cyan")
    safe_send_hotkey(const.OBS_TRANSITION_HOTKEY)

    create_cachfile_for_song(song_number)


def safe_send_hotkey(hotkey: list, sleep_time=0.1) -> None:
    for key in hotkey:
        keyDown(key)
    sleep(sleep_time)
    for key in hotkey:
        keyUp(key)


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
