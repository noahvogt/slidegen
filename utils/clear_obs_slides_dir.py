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
import shutil

import config as const

from .log import log, error_msg
from .path import expand_dir


def clear_obs_slides_dir() -> None:
    log("clearing obs slides directory...")
    expanded_dir = expand_dir(const.OBS_SLIDES_DIR)
    try:
        for filename in os.listdir(expanded_dir):
            file_path = os.path.join(expanded_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except (FileNotFoundError, PermissionError, IOError) as error:
                error_msg(
                    "Failed to delete %s. Reason: %s" % (file_path, error)
                )
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "could not list directory '{}'. Reason: {}".format(
                expanded_dir, error
            )
        )
