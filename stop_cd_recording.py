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

from os import kill
from signal import SIGTERM

from utils import (
    get_yyyy_mm_dd_date,
    make_sure_file_exists,
    is_valid_cd_record_checkfile,
    log,
    error_msg,
    expand_dir,
    mark_end_of_recording,
)
from input import get_cachefile_content, validate_cd_record_config
import config as const


def stop_cd_recording() -> None:
    cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
    yyyy_mm_dd = get_yyyy_mm_dd_date()

    if is_valid_cd_record_checkfile(cachefile_content, yyyy_mm_dd):
        try:
            kill(int(cachefile_content[2]), SIGTERM)
        except ProcessLookupError:
            error_msg("Recording not running, cannot be stopped.")
        mark_end_of_recording(cachefile_content)
    else:
        error_msg("CD Record Checkfile is invalid.")


def main() -> None:
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE)
    stop_cd_recording()


if __name__ == "__main__":
    main()
