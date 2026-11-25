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

"""Where a point of the original recording ends up after the cut.

Each inner pause is replaced by gap_milis of silence. A pause at the start
or end of the WAV is cut away without a gap.
"""

from .events import is_inner

MAX_CD_TRACKS = 99


def get_gap(start: int, end: int, length_milis: int, gap_milis: int) -> int:
    return gap_milis if is_inner(start, end, length_milis) else 0


def map_milis(
    milis: int,
    intervals: list[tuple[int, int]],
    length_milis: int,
    gap_milis: int,
) -> int | None:
    """New position of milis, None if it lies inside a pause."""
    shift = 0
    for start, end in intervals:
        if milis < start:
            break
        if milis < end:
            return None
        shift += end - start - get_gap(start, end, length_milis, gap_milis)
    return milis - shift


def get_new_length_milis(
    intervals: list[tuple[int, int]], length_milis: int, gap_milis: int
) -> int:
    removed = sum(
        end - start - get_gap(start, end, length_milis, gap_milis)
        for start, end in intervals
    )
    return length_milis - removed


def rewrite_markers(  # pylint: disable=too-many-arguments
    markers: list[int],
    intervals: list[tuple[int, int]],
    length_milis: int,
    gap_milis: int,
    min_track_milis: int,
    *,
    max_tracks: int = MAX_CD_TRACKS,
) -> list[int]:
    """Track starts after the cut, always beginning with 0.

    Markers inside a pause are dropped. After each inner pause a new track
    starts where the audio resumes, so the gap sits between two tracks.
    These resume markers win over other markers closer than
    min_track_milis, as an audio CD needs a minimum track length.
    """
    new_length = get_new_length_milis(intervals, length_milis, gap_milis)
    chosen = [0]

    def try_add(milis: int | None) -> None:
        if milis is None or new_length - milis < min_track_milis:
            return
        if all(abs(milis - other) >= min_track_milis for other in chosen):
            chosen.append(milis)

    for start, end in intervals:
        if is_inner(start, end, length_milis):
            try_add(map_milis(end, intervals, length_milis, gap_milis))
    for marker in markers:
        try_add(map_milis(marker, intervals, length_milis, gap_milis))

    return sorted(chosen)[:max_tracks]
