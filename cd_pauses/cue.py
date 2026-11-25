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

"""Read and write the cue sheets that set_cd_marker.py writes."""

from re import match

CD_FRAMES_PER_SECOND = 75


def timestamp_to_milis(timestamp: str) -> int:
    mins, secs, frames = (int(part) for part in timestamp.split(":"))
    frames += (mins * 60 + secs) * CD_FRAMES_PER_SECOND
    # round up, so converting back gives the same frame
    return -(-frames * 1000 // CD_FRAMES_PER_SECOND)


def milis_to_timestamp(milis: int) -> str:
    frames = milis * CD_FRAMES_PER_SECOND // 1000
    secs, frames = divmod(frames, CD_FRAMES_PER_SECOND)
    mins, secs = divmod(secs, 60)
    return f"{mins:02d}:{secs:02d}:{frames:02d}"


def parse_cue_sheet(text: str) -> tuple[str, list[int]]:
    """Return the FILE line and the start of every track in milis."""
    lines = text.splitlines()
    if not lines or not match(r'^FILE ".+" WAVE$', lines[0].strip()):
        raise ValueError("invalid first cue sheet line")
    markers = []
    for line in lines[1:]:
        index_match = match(
            r"^\s+INDEX 01 ([0-9]{2,}:[0-9]{2}:[0-9]{2})\s*$", line
        )
        if index_match:
            markers.append(timestamp_to_milis(index_match.group(1)))
    if not markers or markers[0] != 0:
        raise ValueError("cue sheet does not start with a track at 00:00:00")
    return lines[0].strip(), markers


def format_cue_sheet(file_line: str, markers: list[int]) -> str:
    # same layout as set_cd_marker.py: a blank line after every later track
    text = f"{file_line}\n"
    for track, milis in enumerate(markers, start=1):
        text += f"  TRACK {track:02d} AUDIO\n"
        text += f"    INDEX 01 {milis_to_timestamp(milis)}\n"
        if track > 1:
            text += "\n"
    return text
