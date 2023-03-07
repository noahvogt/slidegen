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


def create_min_obs_subdirs(count: int) -> None:
    if count >= const.OBS_MIN_SUBDIRS:
        return

    for number in range(count, const.OBS_MIN_SUBDIRS + 1):
        dirname = os.path.join(
            const.OBS_SLIDES_DIR,
            const.OBS_TARGET_SUBDIR + " " + str(number),
        )
        os.mkdir(dirname)
