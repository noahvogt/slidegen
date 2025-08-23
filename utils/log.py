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

from termcolor import colored
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)


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


def error_msg(msg: str):
    print(colored("[*] Error: {}".format(msg), "red"))
    sys.exit(1)


def warn(message: str) -> None:
    print(colored("[*] Warning: {}".format(message), "yellow"))


def log(message: str, color="green", end="\n") -> None:
    print(colored("[*] {}".format(message), color), end=end)  # pyright: ignore


class CustomException(Exception):
    pass
