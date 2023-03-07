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

import os
import re

from utils import log

import config as const


def syncing_needed() -> bool:
    if not cachefiles_found():
        return True

    log("checking for remote changes...")
    os.system(
        "rclone md5sum {} --checkfile {} > {} 2> {}".format(
            const.RCLONE_REMOTE_DIR,
            os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CHECKFILE_NAMING),
            os.devnull,
            os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CACHEFILE_NAMING),
        )
    )

    with open(
        os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CACHEFILE_NAMING),
        mode="r",
        encoding="utf-8",
    ) as cachefile_reader:
        cachefile_content = cachefile_reader.readlines()
    for line in cachefile_content:
        if re.search(": ([0-9])+ differences found$", line):
            diffs = int(line[line.rfind(":") + 1 : line.find("differences")])
            return bool(diffs)
    return False


def cachefiles_found() -> bool:
    return os.path.isfile(
        os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CHECKFILE_NAMING)
    ) and os.path.isfile(
        os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CACHEFILE_NAMING)
    )
