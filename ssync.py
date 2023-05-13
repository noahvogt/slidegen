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
from slides import (
    SlideStyle,
    ClassicSongSlide,
    ClassicSongTemplate,
    ClassicStartSlide,
)
from input import (
    validate_ssync_config,
    slide_selection_iterator,
    parse_ssync_args_as_tuple,
)
from sync import sync_slide_repo, save_new_checkfile, syncing_needed


class Ssync:
    def __init__(self, offline: bool, sequential: bool, slide_style) -> None:
        validate_ssync_config()
        self.offline_flag_enabled = offline
        self.disable_async = sequential
        self.slide_style = slide_style

    def execute(self):
        if syncing_needed(self):
            sync_slide_repo()
            save_new_checkfile()
        clear_obs_slides_dir()
        slide_selection_iterator(self)


def main() -> None:
    colorama.init()

    classic_slide_style = SlideStyle(
        ClassicSongTemplate,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicStartSlide,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicSongSlide,  # pyright: ignore [reportGeneralTypeIssues]
    )
    ssync = Ssync(*parse_ssync_args_as_tuple(), slide_style=classic_slide_style)
    ssync.execute()


if __name__ == "__main__":
    main()
