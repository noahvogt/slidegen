#!/usr/bin/env python3

# Copyright © 2026 Noah Vogt <noah@noahvogt.com>

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

"""Usage: resume_cd_recording.py [UNIX_MILIS]

Notes the end of a pause in the ongoing CD recording, at UNIX_MILIS or
now. The pause is cut out once the CD is finished (see recording/pauses.py).
"""

import colorama

from utils import make_sure_file_exists
from input import validate_cd_record_config, parse_unix_milis_argv
from recording import record_cd_pause_event
import config as const

if __name__ == "__main__":
    colorama.init()
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE, gui_error_out=True)
    record_cd_pause_event("end", parse_unix_milis_argv())
