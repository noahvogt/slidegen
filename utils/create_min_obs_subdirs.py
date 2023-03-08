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

import config as const

from .log import error_msg, log
from .path import expand_dir


def create_min_obs_subdirs() -> None:
    obs_slides_dir = expand_dir(const.OBS_SLIDES_DIR)

    subdirs_to_create = []
    for num in range(1, const.OBS_MIN_SUBDIRS + 1):
        subdirs_to_create.append(num)
    for file in os.listdir(obs_slides_dir):
        if file.startswith(str(const.OBS_SUBDIR_NAMING)):
            try:
                index = int(file[len(str(const.OBS_SUBDIR_NAMING)) :])
            except ValueError:
                error_msg(
                    "could not parse file '{}' in '{}'".format(
                        file, obs_slides_dir
                    )
                )
            if index in subdirs_to_create:
                subdirs_to_create.remove(index)

    dirname = ""
    try:
        for number in subdirs_to_create:
            dirname = os.path.join(
                obs_slides_dir,
                const.OBS_SUBDIR_NAMING + str(number),
            )
            os.mkdir(dirname)
            log("creating empty slide directory '{}'...".format(dirname))
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to create directory '{}'. Reason: {}".format(dirname, error)
        )
