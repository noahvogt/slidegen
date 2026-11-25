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

"""Pauses in the CD recording (e.g. a prayer that is too far from the mics).

The recording itself keeps running. pause_cd_recording.py and
resume_cd_recording.py only note the time in pauses-<cd num>.txt next to
the cue sheet. When a CD is finished, the pauses are cut out of its WAV
and replaced by CD_RECORD_PAUSE_GAP_SECONDS of silence, the cue sheet is
shifted to match and the file is renamed to pauses-<cd num>.applied.txt.
"""

import os
import wave
from os import path, listdir
from re import match
from threading import Thread
from time import sleep

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QMessageBox,
)
from psutil import pid_exists

import config as const
from cd_pauses import (
    PAUSE_END,
    PAUSE_START,
    cut_wav,
    format_cue_sheet,
    format_pause_event,
    get_pause_intervals,
    get_wav_length_milis,
    is_pause_open,
    parse_cue_sheet,
    parse_pause_events,
    rewrite_markers,
)
from input import get_cachefile_content
from os_agnostic import lock_file_exclusively
from utils import expand_dir, log, warn, InfoMsgBox
from .verify import ongoing_cd_recording_detected

CUT_ERRORS = (OSError, ValueError, EOFError, wave.Error)
STOPPING_RECORDING_TIMEOUT_SECONDS = 15


def get_day_dir(yyyy_mm_dd: str) -> str:
    return path.join(expand_dir(const.CD_RECORD_OUTPUT_BASEDIR), yyyy_mm_dd)


def get_padded_cd_num(cd_num: int) -> str:
    return str(cd_num).zfill(const.CD_RECORD_FILENAME_ZFILL)


def get_pause_file_path(day_dir: str, cd_num: int, applied=False) -> str:
    suffix = ".applied.txt" if applied else ".txt"
    return path.join(day_dir, f"pauses-{get_padded_cd_num(cd_num)}{suffix}")


def read_pause_events(pause_file: str) -> list[tuple[str, int]]:
    if not path.isfile(pause_file):
        return []
    with open(pause_file, mode="r", encoding="utf-8") as reader:
        return parse_pause_events(reader.read())


def previous_cd_ended_paused(day_dir: str, cd_num: int) -> bool:
    for applied in (False, True):
        pause_file = get_pause_file_path(day_dir, cd_num - 1, applied)
        if path.isfile(pause_file):
            return is_pause_open(read_pause_events(pause_file))
    return False


def record_cd_pause_event(kind: str, unix_milis: int) -> None:
    """Note the start or end of a pause in the ongoing CD recording.

    Does nothing without an ongoing recording, or if the pause is already
    in that state (e.g. the button state got out of sync).
    """
    cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
    if not ongoing_cd_recording_detected(cachefile_content):
        log(f"no ongoing cd recording, ignoring pause {kind}")
        return

    day_dir = get_day_dir(cachefile_content[0].strip())
    cd_num = int(cachefile_content[5])
    offset_milis = max(0, unix_milis - int(cachefile_content[3]))
    pause_file = get_pause_file_path(day_dir, cd_num)
    events = read_pause_events(pause_file)

    if kind == PAUSE_START and is_pause_open(events):
        warn("cd recording is already paused, ignoring")
        return
    if kind == PAUSE_END and not is_pause_open(events):
        if events or not previous_cd_ended_paused(day_dir, cd_num):
            warn("cd recording is not paused, ignoring")
            return

    log(f"writing pause {kind} at {offset_milis}ms to {pause_file}")
    with open(pause_file, mode="a", encoding="utf-8") as writer:
        writer.write(format_pause_event(kind, offset_milis))


def apply_cd_pauses(yyyy_mm_dd: str, cd_num: int) -> None:
    """Cut the pauses out of a finished CD. Safe to call several times."""
    day_dir = get_day_dir(yyyy_mm_dd)
    pause_file = get_pause_file_path(day_dir, cd_num)
    if not path.isfile(pause_file):
        return

    with open(pause_file, mode="r", encoding="utf-8") as pause_reader:
        lock_file_exclusively(pause_reader)
        if not path.isfile(pause_file):
            return  # another process applied it while we waited

        padded_cd_num = get_padded_cd_num(cd_num)
        wav_path = path.join(day_dir, f"{yyyy_mm_dd}-{padded_cd_num}.wav")
        cue_path = path.join(day_dir, f"sheet-{padded_cd_num}.cue")
        length_milis = get_wav_length_milis(wav_path)
        gap_milis = int(const.CD_RECORD_PAUSE_GAP_SECONDS * 1000)
        intervals = get_pause_intervals(
            parse_pause_events(pause_reader.read()), length_milis, gap_milis
        )

        if intervals:
            log(f"cutting pauses {intervals} out of cd #{cd_num}...")
            replace_wav_and_cue(
                (wav_path, cue_path), intervals, length_milis, gap_milis
            )
        os.replace(pause_file, get_pause_file_path(day_dir, cd_num, True))


def replace_wav_and_cue(
    paths: tuple[str, str],
    intervals: list[tuple[int, int]],
    length_milis: int,
    gap_milis: int,
) -> None:
    wav_path, cue_path = paths
    # temporary names that the burn and sermon scripts do not pick up
    wav_tmp_path = f"{wav_path}.cutting"
    cue_tmp_path = f"{cue_path}.cutting"
    try:
        with open(cue_path, mode="r", encoding="utf-8-sig") as cue_reader:
            file_line, markers = parse_cue_sheet(cue_reader.read())
        new_markers = rewrite_markers(
            markers,
            intervals,
            length_milis,
            gap_milis,
            const.CD_RECORD_MIN_TRACK_MILIS,
        )
        cut_wav(wav_path, wav_tmp_path, intervals, gap_milis)
        with open(cue_tmp_path, mode="w", encoding="utf-8") as cue_writer:
            cue_writer.write(format_cue_sheet(file_line, new_markers))
        os.replace(wav_tmp_path, wav_path)
        os.replace(cue_tmp_path, cue_path)
    finally:
        for tmp_path in (wav_tmp_path, cue_tmp_path):
            if path.exists(tmp_path):
                os.remove(tmp_path)


def apply_cd_pauses_in_background(yyyy_mm_dd: str, cd_num: int) -> None:
    """For the recording process: cut while the next CD keeps recording.

    The thread is not a daemon, so the process waits for it before exiting.
    Errors are only logged here, the burn and sermon scripts try again and
    show them.
    """

    def run() -> None:
        try:
            apply_cd_pauses(yyyy_mm_dd, cd_num)
        except CUT_ERRORS as error:
            warn(f"could not cut the pauses out of cd #{cd_num}: {error}")

    Thread(target=run).start()


def get_recording_cd_num(yyyy_mm_dd: str) -> int | None:
    """Number of the CD whose ffmpeg still runs today, waiting if stopping."""
    for _ in range(STOPPING_RECORDING_TIMEOUT_SECONDS):
        content = get_cachefile_content(
            const.CD_RECORD_CACHEFILE, suppress_error=True
        )
        if (
            len(content) != 6
            or content[0].strip() != yyyy_mm_dd
            or not content[2].strip().isdigit()
            or not content[5].strip().isdigit()
            or not pid_exists(int(content[2]))
        ):
            return None
        if ongoing_cd_recording_detected(content):
            return int(content[5])
        # stopped, but ffmpeg is still finishing the WAV
        sleep(1)
    return None


def apply_pending_cd_pauses(yyyy_mm_dd: str) -> None:
    """Before burning or uploading: cut the pauses of all finished CDs."""
    day_dir = get_day_dir(yyyy_mm_dd)
    if not path.isdir(day_dir):
        return
    pending = []
    for file in sorted(listdir(day_dir)):
        file_match = match(r"^pauses-([0-9]+)\.txt$", file)
        if file_match:
            pending.append(int(file_match.group(1)))
    if not pending:
        return

    recording_cd_num = get_recording_cd_num(yyyy_mm_dd)
    for cd_num in pending:
        if cd_num == recording_cd_num:
            continue
        try:
            apply_cd_pauses(yyyy_mm_dd, cd_num)
        except CUT_ERRORS as error:
            InfoMsgBox(
                QMessageBox.Warning,
                "Warning",
                f"Could not cut the pauses out of CD #{cd_num}, "
                + f"it still contains them. Reason: {error}",
            )
