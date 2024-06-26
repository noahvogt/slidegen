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
from subprocess import Popen
from shlex import split
from time import sleep
from re import match
from enum import Enum
from dataclasses import dataclass
import ftplib
from shutil import copy2

from pyautogui import keyDown, keyUp
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QDialog,
)
from PyQt5.QtCore import QTimer  # pylint: disable=no-name-in-module

from utils import (
    log,
    error_msg,
    get_yyyy_mm_dd_date,
    expand_dir,
    CustomException,
    get_wave_duration_in_frames,
)
from input import (
    validate_cd_record_config,
    RadioButtonDialog,
    InfoMsgBox,
    SheetAndPreviewChooser,
    get_cachefile_content,
)
from os_agnostic import get_cd_drives, eject_drive
import config as const


def make_sure_file_exists(cachefile: str) -> None:
    if not path.isfile(cachefile):
        try:
            with open(
                cachefile, mode="w+", encoding="utf-8-sig"
            ) as file_creator:
                file_creator.write("")
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                "Failed to create file in '{}'. Reason: {}".format(
                    cachefile, error
                )
            )


def choose_right_cd_drive(drives: list) -> str:
    if len(drives) != 1:
        log("Warning: More than one cd drive found", color="yellow")
        if (
            const.CD_RECORD_PREFERED_DRIVE in drives
            and const.CD_RECORD_PREFERED_DRIVE != ""
        ):
            return const.CD_RECORD_PREFERED_DRIVE

        dialog = RadioButtonDialog(drives, "Choose a CD to Burn")
        if dialog.exec_() == QDialog.Accepted:
            print(f"Dialog accepted: {dialog.chosen_sheets}")
            return dialog.chosen_sheets
        log("Warning: Choosing first cd drive...", color="yellow")

    return drives[0]


def get_burn_cmd(cd_drive: str, yyyy_mm_dd, padded_zfill_num: str) -> str:
    cue_sheet_path = path.join(
        expand_dir(const.CD_RECORD_OUTPUT_BASEDIR),
        yyyy_mm_dd,
        f"sheet-{padded_zfill_num}.cue",
    )
    return (
        f"cdrecord -pad dev={cd_drive} -dao -swab -text -audio "
        + f"-cuefile='{cue_sheet_path}'"
    )


class SongDirection(Enum):
    PREVIOUS = "previous"
    NEXT = "next"


def cycle_to_song_direction(song_direction: SongDirection):
    cachefile_content = get_cachefile_content(const.NEXTSONG_CACHE_FILE)
    if song_direction == SongDirection.PREVIOUS:
        step = -1
    else:
        step = 1
    if (
        not (
            len(cachefile_content) == 2
            and match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0])
            and match(r"^[0-9]+$", cachefile_content[1])
        )
        or cachefile_content[0].strip() != get_yyyy_mm_dd_date()
    ):
        switch_to_song(1)
    else:
        switch_to_song(int(cachefile_content[1]) + step)


def switch_to_song(song_number: int) -> None:
    if song_number > const.OBS_MIN_SUBDIRS:
        song_number = 1
    if song_number < 1:
        song_number = const.OBS_MIN_SUBDIRS
    log("sending hotkey to switch to scene {}".format(song_number), "cyan")
    scene_switch_hotkey = list(const.OBS_SWITCH_TO_SCENE_HOTKEY_PREFIX)
    scene_switch_hotkey.append("f{}".format(song_number))
    safe_send_hotkey(scene_switch_hotkey)

    log("sending hotkey to transition to scene {}".format(song_number), "cyan")
    safe_send_hotkey(const.OBS_TRANSITION_HOTKEY)

    create_cachfile_for_song(song_number)


def safe_send_hotkey(hotkey: list, sleep_time=0.1) -> None:
    for key in hotkey:
        keyDown(key)
    sleep(sleep_time)
    for key in hotkey:
        keyUp(key)


def create_cachfile_for_song(song) -> None:
    log("writing song {} to cachefile...".format(song))
    try:
        with open(
            const.NEXTSONG_CACHE_FILE, mode="w", encoding="utf-8-sig"
        ) as file_writer:
            file_writer.write(get_yyyy_mm_dd_date() + "\n")
            file_writer.write(str(song) + "\n")
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to write to cachefile '{}'. Reason: {}".format(
                const.NEXTSONG_CACHE_FILE, error
            )
        )


def mark_end_of_recording(cachefile_content: list) -> None:
    cachefile = expand_dir(const.CD_RECORD_CACHEFILE)

    log("marking end of recording...")
    try:
        with open(cachefile, mode="w+", encoding="utf-8-sig") as file_writer:
            file_writer.write(cachefile_content[0].strip() + "\n")
            file_writer.write("9001\n")
            file_writer.write(cachefile_content[2].strip() + "\n")
            file_writer.write(cachefile_content[3].strip() + "\n")
            file_writer.write(cachefile_content[4].strip() + "\n")
            file_writer.write(cachefile_content[5].strip() + "\n")
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to write to cachefile '{}'. Reason: {}".format(
                cachefile, error
            )
        )


def is_valid_cd_record_checkfile(
    cachefile_content: list, yyyy_mm_dd: str
) -> bool:
    return (
        len(cachefile_content) == 6
        # YYYY-MM-DD
        and bool(match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", cachefile_content[0]))
        # last set marker
        and bool(match(r"^[0-9][0-9]?$", cachefile_content[1]))
        # pid of ffmpeg recording instance
        and bool(match(r"^[0-9]+$", cachefile_content[2]))
        # unix milis @ recording start
        and bool(match(r"^[0-9]+$", cachefile_content[3]))
        # unix milis @ last track
        and bool(match(r"^[0-9]+$", cachefile_content[4]))
        # cd number
        and bool(match(r"^[0-9]+$", cachefile_content[5]))
        # date matches today
        and cachefile_content[0].strip() == yyyy_mm_dd
    )


class CDBurnerGUI:
    def __init__(self, cd_drive: str, yyyy_mm_dd: str, cd_num: str):
        self.app = QApplication([])
        self.drive = cd_drive
        self.yyyy_mm_dd = yyyy_mm_dd
        self.cd_num = cd_num
        self.exit_code = 1
        self.show_burning_msg_box()
        self.start_burn_subprocess()
        self.app.exec_()

    def burning_successful(self) -> bool:
        if self.exit_code == 0:
            return True
        return False

    def show_burning_msg_box(self):
        self.message_box = QMessageBox()
        self.message_box.setWindowTitle("Info")
        self.message_box.setText("Burning CD...")
        self.message_box.setInformativeText(
            "Please wait for a few minutes. You can close this Window, as "
            + "there will spawn another window after the operation is "
            + "finished."
        )

        self.message_box.show()

    def start_burn_subprocess(self):
        process = Popen(
            split(get_burn_cmd(self.drive, self.yyyy_mm_dd, self.cd_num))
        )

        while process.poll() is None:
            QApplication.processEvents()
        self.message_box.accept()

        # Yeah this is hacky but it doesn't work when calling quit directly
        QTimer.singleShot(0, self.app.quit)
        self.exit_code = process.returncode


def burn_cds_of_day(yyyy_mm_dd: str) -> None:
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE)

    try:
        target_dir = path.join(
            expand_dir(const.CD_RECORD_OUTPUT_BASEDIR), yyyy_mm_dd
        )
        if not path.isdir(target_dir):
            exit_as_no_cds_found(target_dir)

        target_files = sorted(listdir(target_dir))
        cue_sheets = []
        for file in target_files:
            if is_legal_sheet_filename(file):
                cue_sheets.append(file)

        if not target_files:
            exit_as_no_cds_found(target_dir)

        if len(cue_sheets) == 1:
            burn_and_eject_cd(
                yyyy_mm_dd, "1".zfill(const.CD_RECORD_FILENAME_ZFILL)
            )
        else:
            app = QApplication([])
            dialog = SheetAndPreviewChooser(
                target_dir, cue_sheets, f"Preview CD's for {yyyy_mm_dd}"
            )
            if dialog.exec_() == QDialog.Accepted:
                if not dialog.chosen_sheets:
                    sys.exit(0)
                log(f"Burning CD's from sheets: {dialog.chosen_sheets}")
                num_of_chosen_sheets = len(dialog.chosen_sheets)
                for num, sheet in enumerate(dialog.chosen_sheets):
                    del app  # pyright: ignore
                    last_cd_to_burn = num == num_of_chosen_sheets
                    burn_and_eject_cd(
                        yyyy_mm_dd,
                        get_padded_cd_num_from_sheet_filename(sheet),
                        last_cd_to_burn,
                    )

    except (FileNotFoundError, PermissionError, IOError):
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            "Error: Could not access directory: "
            + f"'{const.CD_RECORD_OUTPUT_BASEDIR}'",
        )
        sys.exit(1)


def get_ffmpeg_timestamp_from_frame(frames: int) -> str:
    milis = int(frames / 75 * 1000)
    return f"{milis}ms"


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


def exit_as_no_cds_found(target_dir):
    InfoMsgBox(
        QMessageBox.Critical,
        "Error",
        f"Error: Did not find any CD's in: {target_dir}.",
    )
    sys.exit(1)


def is_legal_sheet_filename(filename: str) -> bool:
    return bool(match(r"^sheet-[0-9]+\.cue", filename)) and len(filename) == 17


def get_padded_cd_num_from_sheet_filename(filename: str) -> str:
    if not is_legal_sheet_filename(filename):
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: filename '{filename}' in illegal format",
        )
        sys.exit(1)

    return filename[6:13]


def burn_and_eject_cd(
    yyyy_mm_dd: str, padded_cd_num: str, expect_next_cd=False
) -> None:
    cd_drives = get_cd_drives()
    if not cd_drives:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            "Error: Could not find a CD-ROM. Please try again",
        )
        sys.exit(1)
    drive = choose_right_cd_drive(cd_drives)

    burn_success = CDBurnerGUI(
        drive, yyyy_mm_dd, padded_cd_num
    ).burning_successful()
    if expect_next_cd:
        extra_success_msg = "Please put the next CD into the drive slot before clicking the button."
    else:
        extra_success_msg = ""
    if burn_success:
        InfoMsgBox(
            QMessageBox.Info,
            "Info",
            "Successfully burned CD." + extra_success_msg,
        )
    else:
        InfoMsgBox(QMessageBox.Critical, "Error", "Error: Failed to burn CD.")

    eject_drive(drive)


def make_sure_there_is_no_ongoing_cd_recording() -> None:
    if path.isfile(const.CD_RECORD_CACHEFILE):
        cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
        if is_valid_cd_record_checkfile(
            cachefile_content, get_yyyy_mm_dd_date()
        ):
            if cachefile_content[1].strip() != "9001":
                InfoMsgBox(
                    QMessageBox.Critical,
                    "Error",
                    "Error: Ongoing CD Recording detected",
                )
                sys.exit(1)


def get_index_line_as_frames(line: str) -> int:
    stripped_line = line.strip()
    frames = 75 * 60 * int(stripped_line[9:11])
    frames += 75 * int(stripped_line[12:14])
    frames += int(stripped_line[15:17])
    return frames


@dataclass
class SermonSegment:
    start_frame: int
    end_frame: int
    source_cue_sheet: str
    source_marker: int


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
            # for segment in file_segments:
            #     log(f"start {segment.start_frame}")
            #     log(f"end {segment.end_frame}")
            #     log(f"sheet {segment.source_cue_sheet}")
            #     log(f"marker {segment.source_marker}")

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


def get_audio_base_path_from_segment(segment: SermonSegment) -> str:
    splitted_sheet_path = path.split(segment.source_cue_sheet)
    mp3_path = path.join(
        splitted_sheet_path[0],
        splitted_sheet_path[1][6:13] + f"-segment-{segment.source_marker}",
    )
    return mp3_path


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


@dataclass
class ArchiveTypeStrings:
    archive_type_plural: str
    action_to_choose: str
    action_ing_form: str


def choose_cd_day() -> list[str]:
    strings = ArchiveTypeStrings("CD's", "CD day to Burn", "Burning CD for day")
    return choose_archive_day(strings)


def choose_sermon_day() -> list[str]:
    strings = ArchiveTypeStrings(
        "Sermons", "Sermon day to upload", "Uploading Sermon for day"
    )
    return choose_archive_day(strings)


def choose_archive_day(strings: ArchiveTypeStrings) -> list[str]:
    # pylint: disable=unused-variable
    app = QApplication([])
    try:
        dirs = sorted(listdir(const.CD_RECORD_OUTPUT_BASEDIR))
        dirs.reverse()

        if not dirs:
            return [
                f"Did not find any {strings.archive_type_plural} in: "
                + f"{const.CD_RECORD_OUTPUT_BASEDIR}.",
                "",
            ]

        dialog = RadioButtonDialog(
            dirs, "Choose a " + f"{strings.action_to_choose}"
        )
        if dialog.exec_() == QDialog.Accepted:
            log(f"{strings.action_ing_form} for day: {dialog.chosen}")
            return ["", dialog.chosen]
        return ["ignore", ""]
    except (FileNotFoundError, PermissionError, IOError):
        pass

    return [
        f"Failed to access directory: {const.CD_RECORD_OUTPUT_BASEDIR}.",
        "",
    ]


def upload_sermon_for_day(yyyy_mm_dd: str):
    segments = get_possible_sermon_segments_of_day(yyyy_mm_dd)
    if not segments:
        InfoMsgBox(
            QMessageBox.Critical,
            "Error",
            f"Error: No segment for day '{yyyy_mm_dd}' found",
        )

    suitable_segments = get_segments_with_suitable_time(segments)
    for segment in suitable_segments:
        print(f"start {segment.start_frame}")
        print(f"end {segment.end_frame}")
        print(f"sheet {segment.source_cue_sheet}")
        print(f"marker {segment.source_marker}")

    if not suitable_segments:
        # TODO: choose
        InfoMsgBox(
            QMessageBox.Critical, "Error", "Error: no suitable segment found"
        )
    elif len(suitable_segments) == 1:
        upload_sermon_segment(suitable_segments[0])
    else:
        # TODO: choose
        pass
