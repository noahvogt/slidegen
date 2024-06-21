#!/usr/bin/env python3

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
    SsyncFlags,
)
from sync import sync_slide_repo, save_new_checkfile, syncing_needed


def ssync(ssync_flags: SsyncFlags, slide_style: SlideStyle) -> None:
    validate_ssync_config()
    if syncing_needed(ssync_flags.offline_enabled):
        sync_slide_repo()
        save_new_checkfile()
    clear_obs_slides_dir()
    slide_selection_iterator(ssync_flags.disable_async_enabled, slide_style)


def main() -> None:
    colorama.init()

    classic_slide_style = SlideStyle(
        ClassicSongTemplate,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicStartSlide,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicSongSlide,  # pyright: ignore [reportGeneralTypeIssues]
    )
    ssync_flags = SsyncFlags(*parse_ssync_args_as_tuple())

    ssync(ssync_flags, classic_slide_style)


if __name__ == "__main__":
    main()
