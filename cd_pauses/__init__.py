# Copyright © 2026 Noah Vogt <noah@noahvogt.com>

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

"""Cut pauses (e.g. a prayer) out of a finished CD recording.

Standard library only on purpose, so it stays testable without PyQt5.
"""

from .events import (
    PAUSE_START,
    PAUSE_END,
    parse_pause_events,
    format_pause_event,
    is_pause_open,
    get_pause_intervals,
)
from .timeline import map_milis, get_new_length_milis, rewrite_markers
from .cue import parse_cue_sheet, format_cue_sheet
from .wav import cut_wav, get_wav_length_milis
