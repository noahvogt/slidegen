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

from re import match

from utils import (
    get_yyyy_mm_dd_date,
    switch_to_song,
    make_sure_file_exists,
)
from input import get_cachefile_content, validate_songchooser_config
import config as const


def cycle_to_next_song() -> None:
    cachefile_content = get_cachefile_content(const.NEXTSONG_CACHE_FILE)
    if (
        not (
            len(cachefile_content) == 2
            and match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0])
            and match(r"^[0-9]+$", cachefile_content[1])
        )
        or cachefile_content[0].strip() != get_yyyy_mm_dd_date()
    ):
        switch_to_song(1)
    else:
        switch_to_song(int(cachefile_content[1]) + 1)


def main() -> None:
    validate_songchooser_config()
    make_sure_file_exists(const.NEXTSONG_CACHE_FILE)
    cycle_to_next_song()


if __name__ == "__main__":
    main()
