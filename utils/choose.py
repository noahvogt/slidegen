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

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QDialog,
    QVBoxLayout,
    QRadioButton,
    QPushButton,
    QMessageBox,
    QButtonGroup,
    QScrollArea,
    QWidget,
    QCalendarWidget,
    QFileDialog,
)

from PyQt5.QtCore import QDate  # pylint: disable=no-name-in-module


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
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select an option before proceeding.",
            )


class DatePickerDialog(QDialog):  # pylint: disable=too-few-public-methods
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select a Date")
        self.setMinimumWidth(300)

        # Layout
        layout = QVBoxLayout()

        # Calendar widget
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setSelectedDate(QDate.currentDate())
        layout.addWidget(self.calendar)

        # OK button
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def selected_date(self):
        return self.calendar.selectedDate()


def get_mp3_file_via_picker_dialog(parent=None) -> str | None:
    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setNameFilter("MP3 Files (*.mp3)")
    if dialog.exec_():
        selected_files = dialog.selectedFiles()
        # Return the first selected file
        return selected_files[0]
    return None
