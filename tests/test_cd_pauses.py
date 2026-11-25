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

"""Run from the repo root: python -m unittest discover tests"""

import tempfile
import unittest
import wave
from array import array
from os import path

from cd_pauses import (
    cut_wav,
    format_cue_sheet,
    get_new_length_milis,
    get_pause_intervals,
    is_pause_open,
    map_milis,
    parse_cue_sheet,
    parse_pause_events,
    rewrite_markers,
)

GAP = 3000
MIN_TRACK = 4200


class PauseEventsTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            parse_pause_events("start 1000\n\nend 5000\n"),
            [("start", 1000), ("end", 5000)],
        )
        with self.assertRaises(ValueError):
            parse_pause_events("pause 1000\n")

    def test_is_open(self):
        self.assertFalse(is_pause_open([]))
        self.assertTrue(is_pause_open([("start", 1)]))
        self.assertFalse(is_pause_open([("start", 1), ("end", 2)]))

    def test_intervals(self):
        events = [("start", 60000), ("end", 120000)]
        self.assertEqual(
            get_pause_intervals(events, 600000, GAP), [(60000, 120000)]
        )

    def test_open_pause_lasts_until_end(self):
        self.assertEqual(
            get_pause_intervals([("start", 60000)], 100000, GAP),
            [(60000, 100000)],
        )

    def test_leading_end_continues_previous_cd(self):
        self.assertEqual(
            get_pause_intervals([("end", 30000)], 100000, GAP),
            [(0, 30000)],
        )

    def test_end_without_start_later_is_ignored(self):
        events = [("start", 1000), ("end", 20000), ("end", 50000)]
        self.assertEqual(
            get_pause_intervals(events, 100000, GAP), [(1000, 20000)]
        )

    def test_short_inner_pause_dropped(self):
        events = [("start", 10000), ("end", 11000)]
        self.assertEqual(get_pause_intervals(events, 100000, GAP), [])

    def test_merge_and_clip(self):
        events = [
            ("start", 10000),
            ("end", 30000),
            ("start", 20000),
            ("end", 200000),
        ]
        self.assertEqual(
            get_pause_intervals(events, 100000, GAP), [(10000, 100000)]
        )


class TimelineTest(unittest.TestCase):
    intervals = [(60000, 120000)]
    length = 600000

    def map(self, milis):
        return map_milis(milis, self.intervals, self.length, GAP)

    def test_map(self):
        self.assertEqual(self.map(30000), 30000)
        self.assertIsNone(self.map(90000))
        self.assertEqual(self.map(120000), 63000)
        self.assertEqual(self.map(200000), 143000)
        self.assertEqual(
            get_new_length_milis(self.intervals, self.length, GAP), 543000
        )

    def test_no_gap_at_edges(self):
        self.assertEqual(map_milis(40000, [(0, 30000)], 100000, GAP), 10000)
        self.assertEqual(
            get_new_length_milis([(70000, 100000)], 100000, GAP), 70000
        )

    def test_rewrite_markers(self):
        markers = [0, 30000, 90000, 200000]
        self.assertEqual(
            rewrite_markers(
                markers, self.intervals, self.length, GAP, MIN_TRACK
            ),
            [0, 30000, 63000, 143000],
        )

    def test_resume_marker_wins_over_close_marker(self):
        # a song started 2s after the prayer ended
        markers = [0, 122000]
        self.assertEqual(
            rewrite_markers(
                markers, self.intervals, self.length, GAP, MIN_TRACK
            ),
            [0, 63000],
        )

    def test_no_track_shorter_than_minimum_at_end(self):
        self.assertEqual(
            rewrite_markers([0], [(50000, 98000)], 100000, GAP, MIN_TRACK),
            [0],
        )

    def test_max_tracks(self):
        markers = [i * 5000 for i in range(120)]
        self.assertEqual(
            len(rewrite_markers(markers, [], 600000, GAP, MIN_TRACK)), 99
        )


class CueSheetTest(unittest.TestCase):
    sheet = (
        'FILE "/x/2026-11-15-0000001.wav" WAVE\n'
        "  TRACK 01 AUDIO\n"
        "    INDEX 01 00:00:00\n"
        "  TRACK 02 AUDIO\n"
        "    INDEX 01 01:35:42\n"
        "\n"
        "  TRACK 03 AUDIO\n"
        "    INDEX 01 79:59:74\n"
        "\n"
    )

    def test_roundtrip(self):
        file_line, markers = parse_cue_sheet(self.sheet)
        self.assertEqual(file_line, 'FILE "/x/2026-11-15-0000001.wav" WAVE')
        self.assertEqual(format_cue_sheet(file_line, markers), self.sheet)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_cue_sheet("TRACK 01 AUDIO\n")


def write_wav(file_path, frames, rate=1000, value=1000):
    with wave.open(file_path, "wb") as writer:
        writer.setnchannels(2)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(array("h", [value] * frames * 2).tobytes())


def read_left_channel(file_path):
    with wave.open(file_path, "rb") as reader:
        samples = array("h", reader.readframes(reader.getnframes()))
    return list(samples[::2])


class CutWavTest(unittest.TestCase):
    def test_cut_with_gap_and_fades(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = path.join(tmp_dir, "src.wav")
            dst = path.join(tmp_dir, "dst.wav")
            write_wav(src, 10000)  # 10s at 1000 frames per second
            cut_wav(src, dst, [(2000, 6000)], 1000, fade_milis=100)
            left = read_left_channel(dst)

        # 2s audio, 1s silence, 4s audio
        self.assertEqual(len(left), 7000)
        self.assertEqual(left[0], 1000)
        self.assertEqual(left[1899], 1000)
        self.assertLess(left[1950], 1000)
        self.assertEqual(left[1999], 10)
        self.assertEqual(set(left[2000:3000]), {0})
        self.assertEqual(left[3000], 0)
        self.assertLess(left[3050], 1000)
        self.assertEqual(left[3100], 1000)
        self.assertEqual(left[-1], 1000)

    def test_cut_at_edges_without_gap(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = path.join(tmp_dir, "src.wav")
            dst = path.join(tmp_dir, "dst.wav")
            write_wav(src, 10000)
            cut_wav(src, dst, [(0, 1000), (8000, 10000)], 1000)
            left = read_left_channel(dst)
        self.assertEqual(len(left), 7000)


if __name__ == "__main__":
    unittest.main()
