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

import os
from utils import log
import config as const


def syncing_needed(offline_flag_enabled: bool) -> bool:
    if offline_flag_enabled:
        log("skipping sync with remote", color="cyan")
        return False

    log("checking for remote changes...")

    exit_code = os.system(
        'rclone check "{}" "{}" --one-way --quiet'.format(
            const.RCLONE_REMOTE_DIR, const.RCLONE_LOCAL_DIR
        )
    )

    # rclone check returns 0 when every file is identical
    return exit_code != 0
