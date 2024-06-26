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

from dataclasses import dataclass
from enum import Enum


@dataclass
class SermonSegment:
    start_frame: int
    end_frame: int
    source_cue_sheet: str
    source_marker: int


@dataclass
class ChosenAudio:
    sheet_rel_path: str
    wave_abs_path: str


@dataclass
class AudioSourceFileType(Enum):
    WAVE = "wave"
    CUESHEET = "cuesheet"
