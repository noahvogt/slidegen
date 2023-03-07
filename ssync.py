#!/usr/bin/env python3

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

import colorama

from utils import clear_obs_slides_dir
from input import validate_ssync_config, slide_selection_iterator
from sync import sync_slide_repo, save_new_checkfile, syncing_needed


class Ssync:
    def __init__(self):
        validate_ssync_config()

    def execute(self):
        if syncing_needed():
            sync_slide_repo()
            save_new_checkfile()
        clear_obs_slides_dir()
        slide_selection_iterator()


def main() -> None:
    colorama.init()

    ssync: Ssync = Ssync()
    ssync.execute()


if __name__ == "__main__":
    main()
