"""
Copyright © 2024 Noah Vogt <noah@noahvogt.com>

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

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QStyle,
    QLabel,
    QRadioButton,
    QPushButton,
    QMessageBox,
    QButtonGroup,
    QScrollArea,
    QWidget,
)
from PyQt5.QtCore import QSize


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
        self.setWindowTitle(window_title)

        self.master_layout = QVBoxLayout(self)

        scroll_area_layout = self.get_scroll_area_layout()

        self.radio_button_group = QButtonGroup(self)

        self.chosen = ""
        for num, item in enumerate(options):
            radio_button = QRadioButton(item)
            if num == 0:
                radio_button.setChecked(True)
            button_layout = QHBoxLayout()
            self.radio_button_group.addButton(radio_button)

            button_layout.addWidget(radio_button)

            play_button = self.get_player_button("SP_MediaPlay")
            play_button.setToolTip("Play CD Preview")

            pause_button = self.get_player_button("SP_MediaPause")
            pause_button.setToolTip("Pause CD Preview")

            stop_button = self.get_player_button("SP_MediaStop")
            stop_button.setToolTip("Stop CD Preview")

            seek_bwd_button = self.get_player_button("SP_MediaSeekBackward")
            seek_bwd_button.setToolTip("Seek 10 seconds backwards")

            seek_fwd_button = self.get_player_button("SP_MediaSeekForward")
            seek_fwd_button.setToolTip("Seek 10 seconds forwards")

            button_layout.addWidget(play_button)
            button_layout.addWidget(pause_button)
            button_layout.addWidget(stop_button)
            button_layout.addWidget(seek_bwd_button)
            button_layout.addWidget(seek_fwd_button)
            button_layout.addWidget(QLabel("01:23 / 80:00"))

            scroll_area_layout.addLayout(button_layout)

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

    def get_player_button(self, icon_name: str) -> QPushButton:
        stop_button = QPushButton("")
        stop_button.setMinimumSize(QSize(40, 40))
        stop_button.setMaximumSize(QSize(40, 40))
        pixmapi = getattr(QStyle, icon_name)
        icon = self.style().standardIcon(pixmapi)  # pyright: ignore
        stop_button.setIcon(icon)
        return stop_button

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
