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
from re import match, sub
from subprocess import Popen
import ftplib
from datetime import datetime, timezone
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
    QInputDialog,
    QDialog,
)

from utils import (
    CustomException,
    expand_dir,
    log,
    InfoMsgBox,
    RadioButtonDialog,
)
from audio import (
    get_ffmpeg_timestamp_from_frame,
    SermonSegment,
    get_wave_duration_in_frames,
    get_index_line_as_frames,
    AudioSourceFileType,
)
import config as const
from .verify import (
    get_padded_cd_num_from_sheet_filename,
    is_legal_sheet_filename,
)
from .gui import WaveAndSheetPreviewChooserGUI


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
    cmd = 'ffmpeg -y -i "{}" -acodec libmp3lame "{}"'.format(
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
        f'ffmpeg -y -i "{get_full_wav_path(segment)}" -ss '
        + f" {get_ffmpeg_timestamp_from_frame(segment.start_frame)} "
        + f"-to {get_ffmpeg_timestamp_from_frame(segment.end_frame)} "
        + f'-acodec copy "{get_audio_base_path_from_segment(segment)}.wav"'
    )
    if segment.start_frame >= segment.end_frame:
        log("Empty segment detected, generating silent 1 sec wav in place...")
        cmd = (
            "ffmpeg -y -f lavfi -i anullsrc=r=11025:cl=mono -t 1 "
            + f'"{get_audio_base_path_from_segment(segment)}.wav"'
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


@dataclass
class Preacher:
    id: int
    name: str


def get_preachers():
    try:
        response = requests.get(
            const.SERMON_UPLOAD_WPSM_API_BASE_URL + "/wpfc_preacher",
            timeout=const.HTTP_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        preachers: list[Preacher] = []
        for preacher in data:
            preacher_id = int(preacher["id"])
            # pylint: disable=invalid-name
            name = str(preacher["name"])
            preachers.append(Preacher(preacher_id, name))
        if len(preachers) == 0:
            raise CustomException("Not enough preachers")
        return preachers
    except CustomException as e:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: Could not get preachers. Reason: {e}",
        )
        sys.exit(1)
    except (
        requests.exceptions.RequestException,
        KeyError,
        ValueError,
    ) as e:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: Could not get preachers. Reason: {type(e).__name__}",
        )
        sys.exit(1)


def choose_preacher() -> Preacher:
    preachers = get_preachers()
    preacher_names = [preacher.name for preacher in preachers]
    preacher_ids = [preacher.id for preacher in preachers]
    app = QApplication([])
    dialog = RadioButtonDialog(preacher_names, "Choose a Preacher")
    if dialog.exec_() == QDialog.Accepted:
        log(f"Dialog accepted: {dialog.chosen}")
        return Preacher(
            preacher_ids[preacher_names.index(dialog.chosen)], dialog.chosen
        )
    del app
    InfoMsgBox(
        QMessageBox.Critical,
        "Error",
        "Error: Sermon upload canceled as no preacher selected.",
    )
    sys.exit(1)


def make_sermon_filename(sermon_name: str) -> str:
    # Custom replacements for umlauts and ß
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
    for src, target in replacements.items():
        sermon_name = sermon_name.replace(src, target)

    sermon_name = sermon_name.replace(" ", "_")

    sermon_name = sub(r"[^a-zA-Z0-9_-]", "", sermon_name)

    return sermon_name + ".mp3"


def upload_mp3_to_wordpress(filename: str) -> None:
    app = QApplication([])
    sermon_name, accepted_dialog = QInputDialog.getText(
        None,
        "Input Dialog",
        "Enter the Name of the Sermon:",
    )
    del app

    if not accepted_dialog:
        sys.exit(0)

    wanted_filename = make_sermon_filename(sermon_name)

    mp3_final_path = path.join(path.split(filename)[0], wanted_filename)
    make_sermon_mp3(filename, mp3_final_path)

    headers = {
        "Content-Disposition": f"attachment; filename={wanted_filename}",
        "Content-Type": "audio/mpeg",
    }

    with open(mp3_final_path, "rb") as f:
        try:
            log(f"uploading f{mp3_final_path} to wordpress...")
            response = requests.post(
                const.SERMON_UPLOAD_WPSM_API_BASE_URL + "/media",
                headers=headers,
                data=f,
                auth=HTTPBasicAuth(
                    const.SERMON_UPLOAD_WPSM_USER,
                    const.SERMON_UPLOAD_WPSM_PASSWORD,
                ),
                timeout=const.HTTP_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            log(f"url of uploaded wordpress media: {data['guid']['rendered']}")
        except (
            requests.exceptions.RequestException,
            # KeyError,
            # FileNotFoundError,
            # PermissionError,
            # IOError,
        ) as e:
            InfoMsgBox(
                QMessageBox.Critical,
                "Error",
                f"Error: Could not upload sermon to wordpress. Reason: {e}",
            )
            sys.exit(1)


def upload_sermon_to_ftp_server(audiofile: str) -> None:
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
                QMessageBox.Critical,
                "Error",
                "Error: filename already exists.",
            )
            session.quit()
            sys.exit(1)

        mp3_final_path = path.join(path.split(audiofile)[0], wanted_filename)
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


def upload_sermon_audiofile(audiofile: str, yyyy_mm_dd: str) -> None:
    if const.SERMON_UPLOAD_USE_FTP:
        upload_sermon_to_ftp_server(audiofile)
    else:
        dt = datetime.fromisoformat(yyyy_mm_dd).replace(tzinfo=timezone.utc)
        # puts date to midnight of UTC
        unix_seconds = int(dt.timestamp())
        preacher = choose_preacher()
        upload_mp3_to_wordpress(audiofile)


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
            f"{get_audio_base_path_from_segment(suitable_segments[0])}.wav",
            yyyy_mm_dd,
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
        upload_sermon_audiofile(path.join(target_dir, "merged.wav"), yyyy_mm_dd)


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
    cmd = 'ffmpeg -y -f concat -safe 0 -i "{}" -acodec copy "{}"'.format(
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
