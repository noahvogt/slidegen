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

from os import system, path

import shutil

from utils import log, expand_dir, error_msg

import config as const


def save_new_checkfile() -> None:
    cache_dir = expand_dir(const.SSYNC_CACHE_DIR)
    log("saving new checkfile...")
    system(
        'rclone md5sum "{}" > "{}"'.format(
            const.RCLONE_REMOTE_DIR,
            path.join(cache_dir, const.SSYNC_CHECKFILE_NAMING),
        )
    )
    try:
        if not path.isfile(path.join(cache_dir, const.SSYNC_CACHEFILE_NAMING)):
            shutil.copyfile(
                path.join(cache_dir, const.SSYNC_CHECKFILE_NAMING),
                path.join(cache_dir, const.SSYNC_CACHEFILE_NAMING),
            )
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg("Failed to save new checkfile. Reason: {}".format(error))
