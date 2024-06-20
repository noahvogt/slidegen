"""
Copyright © 2022 Noah Vogt <noah@noahvogt.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from os import path, listdir
from subprocess import Popen
from shlex import split
from time import sleep
from re import match
from enum import Enum

from pyautogui import keyDown, keyUp
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
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
