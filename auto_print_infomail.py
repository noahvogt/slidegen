#!/usr/bin/env python3

# Copyright © 2023 Noah Vogt <noah@noahvogt.com>

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

from os import system
from datetime import datetime
from re import match

import colorama

from utils import make_sure_file_exists, get_current_yyyy_mm_dd_date
from input import validate_autoprint_infomail_config, get_cachefile_content
import config as const


def is_sunday() -> bool:
    today = datetime.today()
    return today.weekday() == 6


def already_printed_today() -> bool:
    cachefile_content = get_cachefile_content(const.AUTOPRINT_INFOMAIL_DATEFILE)
    return bool(
        match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0])
        and cachefile_content[0].strip() == get_current_yyyy_mm_dd_date()
    )


if __name__ == "__main__":
    colorama.init()
    validate_autoprint_infomail_config()
    make_sure_file_exists(const.AUTOPRINT_INFOMAIL_DATEFILE, gui_error_out=True)
    if is_sunday() and not already_printed_today():
        system(const.AUTOPRINT_INFOMAIL_CMD)
