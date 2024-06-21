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

from utils import (
    make_sure_there_is_no_ongoing_cd_recording,
    get_yyyy_mm_dd_date,
    upload_sermon_for_day,
)
from input import (
    validate_sermon_upload_config,
)


if __name__ == "__main__":
    validate_sermon_upload_config()
    make_sure_there_is_no_ongoing_cd_recording()
    upload_sermon_for_day(get_yyyy_mm_dd_date())
