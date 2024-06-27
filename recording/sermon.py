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
from os import path, listdir
from shlex import split
from re import match
from subprocess import Popen
import ftplib
from shutil import copy2

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
    QInputDialog,
)

from utils import CustomException
from input import InfoMsgBox
from audio import (
    get_ffmpeg_timestamp_from_frame,
    SermonSegment,
    get_wave_duration_in_frames,
    get_index_line_as_frames,
)
import config as const
from .verify import (
    get_padded_cd_num_from_sheet_filename,
    is_legal_sheet_filename,
)


def get_full_wav_path(segment: SermonSegment) -> str:
    try:
        with open(
            segment.source_cue_sheet,
            mode="r",
            encoding="utf-8-sig",
        ) as cue_sheet_reader:
            cue_sheet_content = cue_sheet_reader.readlines()
        first_line = cue_sheet_content[0].strip()
        if not match(r"^FILE \".+\" WAVE$", first_line):
            raise CustomException("invalid first cue sheet line")
        full_wav_path = first_line[first_line.find('"') + 1 :]
        return full_wav_path[: full_wav_path.rfind('"')]
    except (
        FileNotFoundError,
        PermissionError,
        IOError,
        CustomException,
    ) as error:
        app = QApplication([])
        QMessageBox.critical(
            None,
            "Error",
            f"Could not parse cue sheet: '{segment.source_cue_sheet}',"
            + f"Reason: {error}",
        )
        del app
        sys.exit(1)


def get_audio_base_path_from_segment(segment: SermonSegment) -> str:
    splitted_sheet_path = path.split(segment.source_cue_sheet)
    yyyy_mm_dd = path.split(splitted_sheet_path[0])[1]
    cd_num = get_padded_cd_num_from_sheet_filename(splitted_sheet_path[1])
    mp3_path = path.join(
        splitted_sheet_path[0],
        f"{yyyy_mm_dd}-{cd_num}-segment-{segment.source_marker}",
    )
    return mp3_path


def make_sermon_segment_mp3(segment: SermonSegment) -> str:
    full_wav_path = get_full_wav_path(segment)

    mp3_path = f"{get_audio_base_path_from_segment(segment)}.mp3"
    cmd = "ffmpeg -y -i {} -acodec libmp3lame {}".format(
        full_wav_path,
        mp3_path,
    )
    process = Popen(split(cmd))
    _ = process.communicate()[0]  # wait for subprocess to end
    if process.returncode not in [255, 0]:
        app = QApplication([])
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            "ffmpeg terminated with " + f"exit code {process.returncode}",
        )
        del app

    return mp3_path


def prepare_audio_files_for_segment_chooser(
    segments: list[SermonSegment],
) -> None:
    for segment in segments:
        # TODO: check if file duration and type roughly match the target to
        # avoid useless regenerating. Also, parallelization.
        cmd = (
            f"ffmpeg -y -i {get_full_wav_path(segment)} -ss "
            + f" {get_ffmpeg_timestamp_from_frame(segment.start_frame)} "
            + f"-to {get_ffmpeg_timestamp_from_frame(segment.end_frame)} "
            + f"-acodec copy {get_audio_base_path_from_segment(segment)}.wav"
        )
        process = Popen(split(cmd))
        _ = process.communicate()[0]  # wait for subprocess to end
        if process.returncode not in [255, 0]:
            app = QApplication([])
            InfoMsgBox(
                QMessageBox.Critical,
                "Error",
                "ffmpeg terminated with " + f"exit code {process.returncode}",
            )
            del app
            sys.exit(1)


def get_possible_sermon_segments_of_day(yyyy_mm_dd: str) -> list[SermonSegment]:
    try:
        segments = []
        base_frames = 0
        max_frames = 0

        day_dir = path.join(const.CD_RECORD_OUTPUT_BASEDIR, yyyy_mm_dd)
        files = sorted(listdir(day_dir))
        cue_sheets = []
        for file in files:
            if is_legal_sheet_filename(file):
                cue_sheets.append(file)
        for sheet_num, sheet in enumerate(cue_sheets):
            with open(
                path.join(day_dir, sheet),
                mode="r",
                encoding="utf-8-sig",
            ) as sheet_reader:
                sheet_content = sheet_reader.readlines()
            start_frame = 0
            end_frame = 0
            wav_path = ""
            max_line_num = 0
            for line_num, line in enumerate(sheet_content):
                max_line_num = line_num
                if line_num == 0:
                    if not match(r"^FILE \".+\" WAVE$", line):
                        raise CustomException("invalid first cue sheet line")
                    wav_path = line[line.find('"') + 1 :]
                    wav_path = wav_path[: wav_path.rfind('"')]
                elif match(r"^\s+INDEX 01 ([0-9]{2}:){2}[0-9]{2}\s*$", line):
                    if line_num != 2:
                        end_frame = get_index_line_as_frames(line)
                        segments.append(
                            SermonSegment(
                                start_frame,
                                end_frame,
                                path.join(day_dir, sheet),
                                (max_line_num - 2) // 2,
                            )
                        )
                        start_frame = end_frame

            segments.append(
                SermonSegment(
                    start_frame,
                    get_wave_duration_in_frames(wav_path),
                    path.join(day_dir, sheet),
                    max_line_num // 2,
                )
            )

        return segments
    except (
        FileNotFoundError,
        PermissionError,
        IOError,
        CustomException,
    ) as error:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: Could not parse sermon segments. Reason: {error}",
        )
        sys.exit(1)


def get_segments_with_suitable_time(
    segments: list[SermonSegment],
) -> list[SermonSegment]:
    suitable_segments = []
    for segment in segments:
        if (
            segment.end_frame - segment.start_frame
            >= const.SERMON_UPLOAD_SUITABLE_SEGMENT_FRAMES
        ):
            # if segment.end_frame - segment.start_frame >= 90000:  # 75 * 60 * 20
            suitable_segments.append(segment)
    return suitable_segments


def upload_sermon_segment(segment: SermonSegment) -> None:
    try:
        session = ftplib.FTP_TLS(
            const.SERMON_UPLOAD_FTP_HOSTNAME,
            const.SERMON_UPLOAD_FTP_USER,
            const.SERMON_UPLOAD_FTP_PASSWORD,
        )
        session.cwd(const.SERMON_UPLOAD_FTP_UPLOAD_DIR)
        raw_filenames = session.nlst()
        disallowed_filenames = []
        for filename in raw_filenames:
            if filename not in (".", ".."):
                disallowed_filenames.append(filename)

        app = QApplication([])
        wanted_filename, accepted_dialog = QInputDialog.getText(
            None,
            "Input Dialog",
            "Enter the filename for the Sermon (the .mp3 can be omitted):",
        )
        del app
        if not wanted_filename.endswith(".mp3"):
            wanted_filename = wanted_filename + ".mp3"

        if not accepted_dialog or wanted_filename == ".mp3":
            session.quit()
            sys.exit(0)
        if wanted_filename in disallowed_filenames:
            InfoMsgBox(
                QMessageBox.Critical, "Error", "Error: filename already exists."
            )
            session.quit()
            sys.exit(1)

        orig_mp3 = make_sermon_segment_mp3(segment)
        mp3_final_path = path.join(path.split(orig_mp3)[0], wanted_filename)
        copy2(orig_mp3, mp3_final_path)

        with open(mp3_final_path, "rb") as file:
            session.storbinary(f"STOR {path.split(mp3_final_path)[1]}", file)
        session.quit()
        InfoMsgBox(
            QMessageBox.Information, "Success", "Sermon uploaded successfully."
        )
    except (
        *ftplib.all_errors,
        FileNotFoundError,
        PermissionError,
        IOError,
    ) as error:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: Could not connect to ftp server. Reason: {error}",
        )
        sys.exit(1)


def upload_sermon_for_day(yyyy_mm_dd: str):
    segments = get_possible_sermon_segments_of_day(yyyy_mm_dd)
    if not segments:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: No segment for day '{yyyy_mm_dd}' found",
        )
        sys.exit(1)

    suitable_segments = get_segments_with_suitable_time(segments)
    # TODO: remove
    # for segment in suitable_segments:
    #     print(f"start {segment.start_frame}")
    #     print(f"end {segment.end_frame}")
    #     print(f"sheet {segment.source_cue_sheet}")
    #     print(f"marker {segment.source_marker}")

    if not suitable_segments:
        # TODO: choose
        prepare_audio_files_for_segment_chooser(segments)
        InfoMsgBox(
            QMessageBox.Critical, "Error", "Error: no suitable segment found"
        )
    elif len(suitable_segments) == 1:
        upload_sermon_segment(suitable_segments[0])
    else:
        # TODO: choose
        pass
