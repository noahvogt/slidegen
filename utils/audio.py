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

import sys

from soundfile import SoundFile, LibsndfileError  # pyright: ignore
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QMessageBox,
)


def get_wave_duration_in_frames(file_name: str) -> int:
    try:
        wav = SoundFile(file_name)
        return int(wav.frames / wav.samplerate * 75)
    except LibsndfileError:
        QMessageBox.critical(
            None,
            "Error",
            f"Error: Could not get duration of {file_name}",
        )
        sys.exit(1)


def get_wave_duration_in_secs(file_name: str) -> int:
    return int(get_wave_duration_in_frames(file_name) / 75)
