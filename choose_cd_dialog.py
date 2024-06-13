#!/usr/bin/env python3

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
    QRadioButton,
    QPushButton,
    QMessageBox,
    QButtonGroup,
    QScrollArea,
    QWidget,
)

from PyQt5.QtGui import QColor, QIcon  # pylint: disable=all

from utils import (
    get_yyyy_mm_dd_date,
    make_sure_file_exists,
    is_valid_cd_record_checkfile,
    log,
)
from input import get_cachefile_content, validate_cd_record_config
import config as const


def stop_cd_recording() -> None:
    cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
    yyyy_mm_dd = get_yyyy_mm_dd_date()

    if is_valid_cd_record_checkfile(cachefile_content, yyyy_mm_dd):
        pass


class RadioButtonDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choose a CD to Burn")

        master_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        master_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        scroll_area_layout = QVBoxLayout(scroll_content)

        self.radio_button_group = QButtonGroup(self)

        self.radio_buttons = []
        for i in range(1, 101):
            radio_button = QRadioButton(f"Radio Button {i}")
            if i == 1:
                radio_button.setChecked(True)
            self.radio_buttons.append(radio_button)
            self.radio_button_group.addButton(radio_button)
            scroll_area_layout.addWidget(radio_button)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        master_layout.addWidget(ok_button)

    def accept(self):
        selected_button = self.radio_button_group.checkedButton()
        if selected_button:
            QMessageBox.information(
                self, "Selection", f"You selected: {selected_button.text()}"
            )
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select an option before proceeding.",
            )


def main() -> None:
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE)

    app = QApplication([])
    dialog = RadioButtonDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("Dialog accepted.")


if __name__ == "__main__":
    main()
