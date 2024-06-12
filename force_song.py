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

from sys import argv


from utils import (
    error_msg,
    make_sure_file_exists,
    switch_to_song,
)
from input import validate_songchooser_config
import config as const


# pylint: disable=inconsistent-return-statements
def get_force_int() -> int:
    try:
        return int(argv[1])
    except IndexError:
        error_msg("couldn't parse force song integer")


def exit_if_force_int_is_illegal():
    force_int = get_force_int()
    if force_int > const.OBS_MIN_SUBDIRS:
        error_msg("force integer too big")
    if force_int < 1:
        error_msg("force integer cannot be smaller than 1")


def main() -> None:
    validate_songchooser_config()
    make_sure_file_exists(const.NEXTSONG_CACHE_FILE)
    exit_if_force_int_is_illegal()
    switch_to_song(get_force_int())


if __name__ == "__main__":
    main()
