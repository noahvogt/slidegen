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

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
    QInputDialog,
    QDialog,
)

from utils import CustomException, expand_dir, log
from input import InfoMsgBox
from audio import (
    get_ffmpeg_timestamp_from_frame,
    SermonSegment,
    get_wave_duration_in_frames,
    get_index_line_as_frames,
    AudioSourceFileType,
)
from input import WaveAndSheetPreviewChooserGUI
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
            encoding="utf-8",
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


def get_audio_rel_path_from_segment(segment: SermonSegment) -> str:
    splitted_sheet_path = path.split(segment.source_cue_sheet)
    yyyy_mm_dd = path.split(splitted_sheet_path[0])[1]
    cd_num = get_padded_cd_num_from_sheet_filename(splitted_sheet_path[1])
    return f"{yyyy_mm_dd}-{cd_num}-segment-{segment.source_marker}"


def get_audio_base_path_from_segment(segment: SermonSegment) -> str:
    base_path = path.split(segment.source_cue_sheet)[0]
    return path.join(
        base_path,
        get_audio_rel_path_from_segment(segment),
    )


def make_sermon_mp3(source_audio: str, target_audio: str) -> None:
    log("Generating final mp3...")
    cmd = "ffmpeg -y -i {} -acodec libmp3lame {}".format(
        source_audio,
        target_audio,
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


def generate_wav_for_segment(segment: SermonSegment) -> None:
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


def prepare_audio_files_for_segment_chooser(
    segments: list[SermonSegment],
) -> None:
    for segment in segments:
        generate_wav_for_segment(segment)


def get_possible_sermon_segments_of_day(yyyy_mm_dd: str) -> list[SermonSegment]:
    try:
        segments = []

        day_dir = path.join(const.CD_RECORD_OUTPUT_BASEDIR, yyyy_mm_dd)
        files = sorted(listdir(day_dir))
        cue_sheets = []
        for file in files:
            if is_legal_sheet_filename(file):
                cue_sheets.append(file)
        for sheet in cue_sheets:
            with open(
                path.join(day_dir, sheet),
                mode="r",
                encoding="utf-8",
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
            suitable_segments.append(segment)
    return suitable_segments


def upload_sermon_audiofile(audiofile: str) -> None:
    try:
        ext = ".mp3"
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
            f"Enter the filename for the Sermon (the {ext} can be omitted):",
        )
        del app
        if not wanted_filename.endswith(ext):
            wanted_filename = wanted_filename + ext

        if not accepted_dialog or wanted_filename == ext:
            session.quit()
            sys.exit(0)
        if wanted_filename in disallowed_filenames:
            InfoMsgBox(
                QMessageBox.Critical, "Error", "Error: filename already exists."
            )
            session.quit()
            sys.exit(1)

        mp3_final_path = path.join(path.split(audiofile)[0], wanted_filename)
        print(mp3_final_path)
        make_sermon_mp3(audiofile, mp3_final_path)

        with open(mp3_final_path, "rb") as file:
            session.storbinary(f"STOR {path.split(mp3_final_path)[1]}", file)
        session.quit()
        InfoMsgBox(
            QMessageBox.Information,
            "Success",
            f"Sermon '{mp3_final_path}' uploaded successfully.",
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


def upload_sermon_for_day(yyyy_mm_dd: str, choose_manually=False):
    segments = get_possible_sermon_segments_of_day(yyyy_mm_dd)
    if not segments:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: No segment for day '{yyyy_mm_dd}' found",
        )
        sys.exit(1)

    suitable_segments = get_segments_with_suitable_time(segments)
    if len(suitable_segments) == 1 and not choose_manually:
        generate_wav_for_segment(suitable_segments[0])
        upload_sermon_audiofile(
            f"{get_audio_base_path_from_segment(suitable_segments[0])}.wav"
        )
    else:
        manually_choose_and_upload_segments(segments, yyyy_mm_dd)


def manually_choose_and_upload_segments(segments, yyyy_mm_dd):
    prepare_audio_files_for_segment_chooser(segments)
    rel_wave_paths = []
    for segment in segments:
        rel_wave_paths.append(f"{get_audio_rel_path_from_segment(segment)}.wav")

    app = QApplication([])
    target_dir = path.join(
        expand_dir(const.CD_RECORD_OUTPUT_BASEDIR), yyyy_mm_dd
    )
    dialog = WaveAndSheetPreviewChooserGUI(
        target_dir,
        rel_wave_paths,
        f"Preview CD's for {yyyy_mm_dd}",
        AudioSourceFileType.WAVE,
    )
    if dialog.exec_() == QDialog.Accepted:
        if not dialog.chosen_audios:
            sys.exit(0)
        chosen_wave_paths = []
        for chosen_audio in dialog.chosen_audios:
            chosen_wave_paths.append(chosen_audio.wave_abs_path)

        del app  # pyright: ignore

        merge_wave_files(target_dir, chosen_wave_paths)
        upload_sermon_audiofile(path.join(target_dir, "merged.wav"))


def merge_wave_files(target_dir: str, wave_paths: list[str]) -> None:
    concat_file_path = path.join(target_dir, "concat.txt")
    log(f"Merging into mp3 file from wave files: {wave_paths}")
    create_concat_file(concat_file_path, wave_paths)
    merge_files_with_ffmpeg(concat_file_path, target_dir)


def create_concat_file(file_path: str, wave_paths: list[str]) -> None:
    try:
        with open(file_path, mode="w+", encoding="utf-8") as writer:
            for wave_path in wave_paths:
                if not "'" in wave_path:
                    writer.write(f"file '{wave_path}'\n")
                else:
                    writer.write(f'file "{wave_path}"\n')
    except (FileNotFoundError, PermissionError, IOError) as error:
        app = QApplication
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Failed to write to '{file_path}'. Reason: {error}",
        )
        del app
        sys.exit(1)


def merge_files_with_ffmpeg(concat_file_path, target_dir) -> None:
    cmd = "ffmpeg -y -f concat -safe 0 -i {} -acodec copy {}".format(
        concat_file_path,
        path.join(target_dir, "merged.wav"),
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
