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

"""Copy a PCM WAV without the pauses, with silence and short fades."""

import sys
import wave
from array import array

from .events import is_inner

FADE_MILIS = 300
CHUNK_FRAMES = 441000
ARRAY_TYPECODES = {2: "h", 4: "i"}


def get_wav_length_milis(wav_path: str) -> int:
    with wave.open(wav_path, "rb") as reader:
        return reader.getnframes() * 1000 // reader.getframerate()


def cut_wav(
    src_path: str,
    dst_path: str,
    intervals: list[tuple[int, int]],
    gap_milis: int,
    fade_milis: int = FADE_MILIS,
) -> None:
    with wave.open(src_path, "rb") as reader:
        with wave.open(dst_path, "wb") as writer:
            writer.setparams(reader.getparams())
            rate = reader.getframerate()
            length_frames = reader.getnframes()
            length_milis = length_frames * 1000 // rate
            fade_frames = fade_milis * rate // 1000
            frame_size = reader.getsampwidth() * reader.getnchannels()
            silence_byte = b"\x80" if reader.getsampwidth() == 1 else b"\x00"

            def to_frames(milis: int) -> int:
                return min(length_frames, milis * rate // 1000)

            pos = 0
            for start, end in intervals:
                copy_range(
                    reader, writer, (pos, to_frames(start)), fade_frames
                )
                if is_inner(start, end, length_milis):
                    gap_bytes = gap_milis * rate // 1000 * frame_size
                    writer.writeframesraw(silence_byte * gap_bytes)
                pos = to_frames(end)
            copy_range(reader, writer, (pos, length_frames), fade_frames)


def copy_range(
    reader: wave.Wave_read,
    writer: wave.Wave_write,
    frame_range: tuple[int, int],
    fade_frames: int,
) -> None:
    """Copy frames [first, last), fading at cuts.

    Fade in unless the range starts the file, fade out unless it ends it.
    """
    first, last = frame_range
    if last <= first:
        return
    fade_in = first > 0
    fade_out = last < reader.getnframes()
    reader.setpos(first)
    pos = first
    while pos < last:
        count = min(CHUNK_FRAMES, last - pos)
        data = reader.readframes(count)
        needs_fade = (fade_in and pos < first + fade_frames) or (
            fade_out and pos + count > last - fade_frames
        )
        if needs_fade:
            data = apply_fades(
                data,
                reader,
                (pos, first, last),
                (fade_in, fade_out, fade_frames),
            )
        writer.writeframesraw(data)
        pos += count


def apply_fades(
    data: bytes,
    reader: wave.Wave_read,
    positions: tuple[int, int, int],
    fades: tuple[bool, bool, int],
) -> bytes:
    typecode = ARRAY_TYPECODES.get(reader.getsampwidth())
    if typecode is None:
        return data  # unusual sample format: hard cut instead of a fade
    pos, first, last = positions
    fade_in, fade_out, fade_frames = fades
    channels = reader.getnchannels()

    samples = array(typecode, data)
    if sys.byteorder == "big":
        samples.byteswap()
    chunk_end = pos + len(samples) // channels
    to_fade = set()
    if fade_in:
        to_fade.update(range(pos, min(chunk_end, first + fade_frames)))
    if fade_out:
        to_fade.update(range(max(pos, last - fade_frames), chunk_end))
    for abs_frame in to_fade:
        gain = 1.0
        if fade_in and abs_frame < first + fade_frames:
            gain = min(gain, (abs_frame - first) / fade_frames)
        if fade_out and abs_frame >= last - fade_frames:
            gain = min(gain, (last - abs_frame) / fade_frames)
        start_index = (abs_frame - pos) * channels
        for index in range(start_index, start_index + channels):
            samples[index] = int(samples[index] * gain)
    if sys.byteorder == "big":
        samples.byteswap()
    return samples.tobytes()
