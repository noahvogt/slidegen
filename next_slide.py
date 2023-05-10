#!/usr/bin/env python3

"""
Copyright © 2023 Noah Vogt <noah@noahvogt.com>

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

from datetime import date
from re import match
from os import path

from pyautogui import hotkey

from utils import log, error_msg
import config as const


def calculate_date() -> str:
    return date.strftime(date.today(), "%Y-%m-%d")


def get_cachefile_content() -> list:
    try:
        with open(
            const.NEXTSONG_CACHE_FILE, mode="r", encoding="utf8"
        ) as cachefile_reader:
            cachefile_content = cachefile_reader.readlines()
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to access cachefile in '{}'. Reason: {}".format(
                const.NEXTSONG_CACHE_FILE, error
            )
        )
    return cachefile_content


def cycle_to_next_slide() -> None:
    cachefile_content = get_cachefile_content()
    if (
        not (
            len(cachefile_content) == 2
            and match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0])
            and match(r"^[0-9]*$", cachefile_content[1])
        )
        or cachefile_content[0].strip() != calculate_date()
    ):
        switch_to_slide(1)
    else:
        switch_to_slide(int(cachefile_content[1]) + 1)


def switch_to_slide(slide: int) -> None:
    if slide > const.OBS_MIN_SUBDIRS:
        slide = 1
    log("sending hotkey Ctr + Shift + F{}".format(slide))
    hotkey("ctrl", "shift", "f{}".format(slide))
    create_cachfile_for_slide(slide)


def create_cachfile_for_slide(slide) -> None:
    log("writing slide {} cachefile...".format(slide))
    try:
        with open(
            const.NEXTSONG_CACHE_FILE, mode="w", encoding="utf8"
        ) as file_writer:
            file_writer.write(calculate_date() + "\n")
            file_writer.write(str(slide) + "\n")
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to write to cachefile '{}'. Reason: {}".format(
                const.NEXTSONG_CACHE_FILE, error
            )
        )


def validate_config() -> None:
    if const.NEXTSONG_CACHE_FILE == "":
        error_msg("needed config entry 'NEXTSONG_CACHE_FILE' is empty")
    if const.OBS_MIN_SUBDIRS == "":
        error_msg("needed config entry 'OBS_MIN_SUBDIRS' is empty")
    log("configuration initialised")


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


def main() -> None:
    validate_config()
    make_sure_cachefile_exists()
    cycle_to_next_slide()


if __name__ == "__main__":
    main()
