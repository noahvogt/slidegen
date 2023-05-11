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

from utils import log, error_msg

import config as const


def validate_ssync_config() -> None:
    needed_constants: dict = {
        "RCLONE_LOCAL_DIR": const.RCLONE_LOCAL_DIR,
        "RCLONE_REMOTE_DIR": const.RCLONE_REMOTE_DIR,
        "SSYNC_CHECKFILE_NAMING": const.SSYNC_CHECKFILE_NAMING,
        "SSYNC_CACHEFILE_NAMING": const.SSYNC_CACHEFILE_NAMING,
        "SSYNC_CACHE_DIR": const.SSYNC_CACHE_DIR,
        "OBS_SLIDES_DIR": const.OBS_SLIDES_DIR,
        "OBS_SUBDIR_NAMING": const.OBS_SUBDIR_NAMING,
        "OBS_MIN_SUBDIRS": const.OBS_MIN_SUBDIRS,
    }
    general_config_validator(needed_constants)


def validate_songchooser_config() -> None:
    needed_constants: dict = {
        "NEXTSONG_CACHE_FILE": const.NEXTSONG_CACHE_FILE,
        "OBS_MIN_SUBDIRS": const.OBS_MIN_SUBDIRS,
    }
    general_config_validator(needed_constants)


def general_config_validator(needed_constants: dict) -> None:
    for key in needed_constants:
        if needed_constants.get(key) == "":
            error_msg("needed config entry '{}' is empty".format(key))
    log("configuration initialised")
