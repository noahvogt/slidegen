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

"""Pause file of one CD: one event per line, "start <ms>" or "end <ms>".

The milliseconds are the offset into the WAV of that CD. A pause that is
still open when the CD ends lasts until the end of the WAV. An "end"
as the very first event means the pause started on the previous CD.
"""

PAUSE_START = "start"
PAUSE_END = "end"


def parse_pause_events(text: str) -> list[tuple[str, int]]:
    events = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        parts = line.split()
        if not parts:
            continue
        if (
            len(parts) != 2
            or parts[0] not in (PAUSE_START, PAUSE_END)
            or not parts[1].isdigit()
        ):
            raise ValueError(f"invalid pause file line {line_num}: '{line}'")
        events.append((parts[0], int(parts[1])))
    return events


def format_pause_event(kind: str, milis: int) -> str:
    return f"{kind} {milis}\n"


def is_pause_open(events: list[tuple[str, int]]) -> bool:
    is_open = False
    for kind, _ in events:
        is_open = kind == PAUSE_START
    return is_open


def get_pause_intervals(
    events: list[tuple[str, int]], length_milis: int, min_inner_milis: int
) -> list[tuple[int, int]]:
    """Sorted, merged pauses as (start, end) milis within the WAV.

    Inner pauses (not touching the start or end of the WAV) shorter than
    min_inner_milis are dropped, they were most likely pressed by mistake.
    """
    intervals = []
    open_start = None
    for index, (kind, milis) in enumerate(events):
        if kind == PAUSE_START:
            if open_start is None:
                open_start = milis
        elif open_start is not None:
            intervals.append((open_start, milis))
            open_start = None
        elif index == 0:
            intervals.append((0, milis))
    if open_start is not None:
        intervals.append((open_start, length_milis))

    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        start, end = max(0, start), min(length_milis, end)
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return [
        (start, end)
        for start, end in merged
        if not is_inner(start, end, length_milis)
        or end - start >= min_inner_milis
    ]


def is_inner(start: int, end: int, length_milis: int) -> bool:
    return start > 0 and end < length_milis
