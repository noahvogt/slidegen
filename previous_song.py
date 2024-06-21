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

from utils import (
    SongDirection,
    cycle_to_song_direction,
    make_sure_file_exists,
)
from input import validate_obs_song_scene_switcher_config
import config as const

if __name__ == "__main__":
    validate_obs_song_scene_switcher_config()
    make_sure_file_exists(const.NEXTSONG_CACHE_FILE)
    cycle_to_song_direction(SongDirection.PREVIOUS)
