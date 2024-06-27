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
from re import match
from dataclasses import dataclass

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QStyle,
    QLabel,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QButtonGroup,
    QScrollArea,
    QWidget,
)
from PyQt5.QtMultimedia import (  # pylint: disable=no-name-in-module
    QMediaPlayer,
    QMediaContent,
)
from PyQt5.QtCore import (  # pylint: disable=no-name-in-module
    QSize,
    QUrl,
    QTimer,
)

from audio import SermonSegment
from utils import CustomException, get_wave_duration_in_secs, log
import config as const


@dataclass
class LabelConstruct:
    rel_path: str
    label: QLabel


@dataclass
class CheckBoxConstruct:
    rel_path: str
    check_box: QCheckBox


# pylint: disable=too-few-public-methods
class InfoMsgBox:
    def __init__(self, icon: QMessageBox.Icon, title: str, text: str) -> None:
        self.app = QApplication([])
        self.title = title
        self.text = text
        self.icon = icon
        self.show_msg_box()
        self.app.exec_()

    def show_msg_box(self):
        self.message_box = QMessageBox()
        self.message_box.setIcon(self.icon)
        self.message_box.setWindowTitle(self.title)
        self.message_box.setText(self.text)

        self.message_box.show()


class RadioButtonDialog(QDialog):  # pylint: disable=too-few-public-methods
    def __init__(self, options: list[str], window_title: str):
        super().__init__()
        self.setWindowTitle(window_title)

        self.master_layout = QVBoxLayout(self)

        scroll_area_layout = self.get_scroll_area_layout()

        self.radio_button_group = QButtonGroup(self)

        self.chosen = ""
        for num, item in enumerate(options):
            radio_button = QRadioButton(item)
            if num == 0:
                radio_button.setChecked(True)
            self.radio_button_group.addButton(radio_button)
            scroll_area_layout.addWidget(radio_button)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        self.master_layout.addWidget(ok_button)

    def get_scroll_area_layout(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.master_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        scroll_area_layout = QVBoxLayout(scroll_content)
        return scroll_area_layout

    def accept(self):
        selected_button = self.radio_button_group.checkedButton()
        if selected_button:
            self.chosen = selected_button.text()
            # QMessageBox.information(
            #     self, "Selection", f"You selected: {selected_button.text()}"
            # )
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select an option before proceeding.",
            )


class SheetAndPreviewChooser(QDialog):  # pylint: disable=too-few-public-methods
    def __init__(
        self, base_dir: str, options: list[str], window_title: str
    ) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.setWindowTitle(window_title)

        self.master_layout = QVBoxLayout(self)

        scroll_area_layout = self.get_scroll_area_layout()

        self.check_buttons = []

        self.player = QMediaPlayer()

        self.chosen_sheets = []
        self.position_labels = []
        for num, item in enumerate(options):
            rel_wave_path = self.get_wav_relative_path_from_cue_sheet(item)

            check_box = QCheckBox(item)
            if num == 0:
                check_box.setChecked(True)
            button_layout = QHBoxLayout()
            check_box_construct = CheckBoxConstruct(item, check_box)
            self.check_buttons.append(check_box_construct)
            button_layout.addWidget(check_box)

            play_button = self.get_player_button("SP_MediaPlay")
            play_button.setToolTip("Play CD Preview")
            play_button.clicked.connect(
                lambda _, x=rel_wave_path: self.play_audio(x)
            )

            pause_button = self.get_player_button("SP_MediaPause")
            pause_button.setToolTip("Pause CD Preview")
            pause_button.clicked.connect(
                lambda _, x=rel_wave_path: self.pause_player(x)
            )

            stop_button = self.get_player_button("SP_MediaStop")
            stop_button.setToolTip("Stop CD Preview")
            stop_button.clicked.connect(
                lambda _, x=rel_wave_path: self.stop_player(x)
            )

            seek_bwd_button = self.get_player_button("SP_MediaSeekBackward")
            seek_bwd_button.setToolTip("Seek 10 seconds backwards")
            seek_bwd_button.clicked.connect(
                lambda _, x=rel_wave_path: self.seek_bwd_10secs(x)
            )

            seek_fwd_button = self.get_player_button("SP_MediaSeekForward")
            seek_fwd_button.setToolTip("Seek 10 seconds forwards")
            seek_fwd_button.clicked.connect(
                lambda _, x=rel_wave_path: self.seek_fwd_10secs(x)
            )

            button_layout.addWidget(play_button)
            button_layout.addWidget(pause_button)
            button_layout.addWidget(stop_button)
            button_layout.addWidget(seek_bwd_button)
            button_layout.addWidget(seek_fwd_button)

            secs = get_wave_duration_in_secs(path.join(base_dir, rel_wave_path))
            mins = secs // 60
            secs %= 60
            time_label = QLabel(f"00:00 / {mins:02}:{secs:02}")
            label_construct = LabelConstruct(rel_wave_path, time_label)
            self.position_labels.append(label_construct)
            button_layout.addWidget(time_label)
            timer = QTimer(self)
            timer.timeout.connect(self.update_position)
            timer.start(1000)

            scroll_area_layout.addLayout(button_layout)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        self.master_layout.addWidget(ok_button)

    def play_audio(self, rel_path: str) -> None:
        if self.player.state() == QMediaPlayer.PausedState:  # pyright: ignore
            media = self.player.media()
            if media.isNull():
                return
            if path.split(media.canonicalUrl().toString())[1] == rel_path:
                self.player.play()
        else:
            url = QUrl.fromLocalFile(path.join(self.base_dir, rel_path))
            content = QMediaContent(url)
            self.player.setMedia(content)
            self.player.play()

    def update_position(self) -> None:
        media = self.player.media()
        if media.isNull():
            return
        playing_path = path.split(media.canonicalUrl().toString())[1]
        for label_construct in self.position_labels:
            if label_construct.rel_path == playing_path:
                old_text = label_construct.label.text()
                old_text = old_text[old_text.find(" / ") :]
                secs = self.player.position() // 1000
                mins = secs // 60
                secs %= 60
                label_construct.label.setText(f"{mins:02}:{secs:02}{old_text}")

    def stop_player(self, rel_path: str) -> None:
        media = self.player.media()
        if media.isNull():
            return
        if path.split(media.canonicalUrl().toString())[1] == rel_path:
            self.player.stop()
            self.update_position()

    def seek_by(self, rel_path: str, seek_by_milis) -> None:
        media = self.player.media()
        if media.isNull():
            return
        if path.split(media.canonicalUrl().toString())[1] == rel_path:
            position = self.player.position()
            self.player.setPosition(position + seek_by_milis)
            self.update_position()

    def seek_fwd_10secs(self, rel_path: str) -> None:
        self.seek_by(rel_path, 10000)

    def seek_bwd_10secs(self, rel_path: str) -> None:
        self.seek_by(rel_path, -10000)

    def pause_player(self, rel_path: str) -> None:
        media = self.player.media()
        if media.isNull():
            return
        if path.split(media.canonicalUrl().toString())[1] == rel_path:
            self.player.pause()

    def get_scroll_area_layout(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.master_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        scroll_area_layout = QVBoxLayout(scroll_content)
        return scroll_area_layout

    def get_player_button(self, icon_name: str) -> QPushButton:
        stop_button = QPushButton("")
        stop_button.setMinimumSize(QSize(40, 40))
        stop_button.setMaximumSize(QSize(40, 40))
        pixmapi = getattr(QStyle, icon_name)
        icon = self.style().standardIcon(pixmapi)  # pyright: ignore
        stop_button.setIcon(icon)
        return stop_button

    def accept(self) -> None:
        for check_box_construct in self.check_buttons:
            if check_box_construct.check_box.isChecked():
                self.chosen_sheets.append(check_box_construct.rel_path)
        super().accept()

    def get_wav_relative_path_from_cue_sheet(
        self, sheet_relative_path: str
    ) -> str:
        full_path = path.join(self.base_dir, sheet_relative_path)

        try:
            with open(
                full_path,
                mode="r",
                encoding="utf-8-sig",
            ) as cachefile_reader:
                cachefile_content = cachefile_reader.readlines()
            first_line = cachefile_content[0].strip()
            if not match(r"^FILE \".+\" WAVE$", first_line):
                raise CustomException("invalid first cue sheet line")
            full_path_found = first_line[first_line.find('"') + 1 :]
            full_path_found = full_path_found[: full_path_found.rfind('"')]
            return path.split(full_path_found)[1]
        except (
            FileNotFoundError,
            PermissionError,
            IOError,
            IndexError,
            CustomException,
        ) as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not parse cue sheet: '{full_path}', Reason: {error}",
            )
            sys.exit(1)


class SegmentChooser(QDialog):  # pylint: disable=too-few-public-methods
    def __init__(
        self, base_dir: str, options: list[SermonSegment], window_title: str
    ) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.setWindowTitle(window_title)

        self.master_layout = QVBoxLayout(self)

        scroll_area_layout = self.get_scroll_area_layout()

        self.check_buttons = []

        self.player = QMediaPlayer()

        self.chosen_sheets = []
        self.position_labels = []
        for num, item in enumerate(options):
            rel_wave_path = self.get_wav_relative_path_from_cue_sheet(item)

            check_box = QCheckBox(item)
            if num == 0:
                check_box.setChecked(True)
            button_layout = QHBoxLayout()
            check_box_construct = CheckBoxConstruct(item, check_box)
            self.check_buttons.append(check_box_construct)
            button_layout.addWidget(check_box)

            play_button = self.get_player_button("SP_MediaPlay")
            play_button.setToolTip("Play CD Preview")
            play_button.clicked.connect(
                lambda _, x=rel_wave_path: self.play_audio(x)
            )

            pause_button = self.get_player_button("SP_MediaPause")
            pause_button.setToolTip("Pause CD Preview")
            pause_button.clicked.connect(
                lambda _, x=rel_wave_path: self.pause_player(x)
            )

            stop_button = self.get_player_button("SP_MediaStop")
            stop_button.setToolTip("Stop CD Preview")
            stop_button.clicked.connect(
                lambda _, x=rel_wave_path: self.stop_player(x)
            )

            seek_bwd_button = self.get_player_button("SP_MediaSeekBackward")
            seek_bwd_button.setToolTip("Seek 10 seconds backwards")
            seek_bwd_button.clicked.connect(
                lambda _, x=rel_wave_path: self.seek_bwd_10secs(x)
            )

            seek_fwd_button = self.get_player_button("SP_MediaSeekForward")
            seek_fwd_button.setToolTip("Seek 10 seconds forwards")
            seek_fwd_button.clicked.connect(
                lambda _, x=rel_wave_path: self.seek_fwd_10secs(x)
            )

            button_layout.addWidget(play_button)
            button_layout.addWidget(pause_button)
            button_layout.addWidget(stop_button)
            button_layout.addWidget(seek_bwd_button)
            button_layout.addWidget(seek_fwd_button)

            secs = get_wave_duration_in_secs(path.join(base_dir, rel_wave_path))
            mins = secs // 60
            secs %= 60
            time_label = QLabel(f"00:00 / {mins:02}:{secs:02}")
            label_construct = LabelConstruct(rel_wave_path, time_label)
            self.position_labels.append(label_construct)
            button_layout.addWidget(time_label)
            timer = QTimer(self)
            timer.timeout.connect(self.update_position)
            timer.start(1000)

            scroll_area_layout.addLayout(button_layout)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        self.master_layout.addWidget(ok_button)

    def play_audio(self, rel_path: str) -> None:
        if self.player.state() == QMediaPlayer.PausedState:  # pyright: ignore
            media = self.player.media()
            if media.isNull():
                return
            if path.split(media.canonicalUrl().toString())[1] == rel_path:
                self.player.play()
        else:
            url = QUrl.fromLocalFile(path.join(self.base_dir, rel_path))
            content = QMediaContent(url)
            self.player.setMedia(content)
            self.player.play()

    def update_position(self) -> None:
        media = self.player.media()
        if media.isNull():
            return
        playing_path = path.split(media.canonicalUrl().toString())[1]
        for label_construct in self.position_labels:
            if label_construct.rel_path == playing_path:
                old_text = label_construct.label.text()
                old_text = old_text[old_text.find(" / ") :]
                secs = self.player.position() // 1000
                mins = secs // 60
                secs %= 60
                label_construct.label.setText(f"{mins:02}:{secs:02}{old_text}")

    def stop_player(self, rel_path: str) -> None:
        media = self.player.media()
        if media.isNull():
            return
        if path.split(media.canonicalUrl().toString())[1] == rel_path:
            self.player.stop()
            self.update_position()

    def seek_by(self, rel_path: str, seek_by_milis) -> None:
        media = self.player.media()
        if media.isNull():
            return
        if path.split(media.canonicalUrl().toString())[1] == rel_path:
            position = self.player.position()
            self.player.setPosition(position + seek_by_milis)
            self.update_position()

    def seek_fwd_10secs(self, rel_path: str) -> None:
        self.seek_by(rel_path, 10000)

    def seek_bwd_10secs(self, rel_path: str) -> None:
        self.seek_by(rel_path, -10000)

    def pause_player(self, rel_path: str) -> None:
        media = self.player.media()
        if media.isNull():
            return
        if path.split(media.canonicalUrl().toString())[1] == rel_path:
            self.player.pause()

    def get_scroll_area_layout(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.master_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        scroll_area_layout = QVBoxLayout(scroll_content)
        return scroll_area_layout

    def get_player_button(self, icon_name: str) -> QPushButton:
        stop_button = QPushButton("")
        stop_button.setMinimumSize(QSize(40, 40))
        stop_button.setMaximumSize(QSize(40, 40))
        pixmapi = getattr(QStyle, icon_name)
        icon = self.style().standardIcon(pixmapi)  # pyright: ignore
        stop_button.setIcon(icon)
        return stop_button

    def accept(self) -> None:
        for check_box_construct in self.check_buttons:
            if check_box_construct.check_box.isChecked():
                self.chosen_sheets.append(check_box_construct.rel_path)
        super().accept()

    def get_wav_relative_path_from_cue_sheet(
        self, sheet_relative_path: str
    ) -> str:
        full_path = path.join(self.base_dir, sheet_relative_path)

        try:
            with open(
                full_path,
                mode="r",
                encoding="utf-8-sig",
            ) as cachefile_reader:
                cachefile_content = cachefile_reader.readlines()
            first_line = cachefile_content[0].strip()
            if not match(r"^FILE \".+\" WAVE$", first_line):
                raise CustomException("invalid first cue sheet line")
            full_path_found = first_line[first_line.find('"') + 1 :]
            full_path_found = full_path_found[: full_path_found.rfind('"')]
            return path.split(full_path_found)[1]
        except (
            FileNotFoundError,
            PermissionError,
            IOError,
            IndexError,
            CustomException,
        ) as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not parse cue sheet: '{full_path}', Reason: {error}",
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
