#!/usr/bin/env python3

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

import colorama
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QMessageBox,
)

from recording import upload_sermon_for_day, choose_sermon_day
from input import (
    validate_sermon_upload_config,
)
from utils import InfoMsgBox


def choose_and_upload_sermon():
    msg, yyyy_mm_dd = choose_sermon_day()
    if msg == "":
        upload_sermon_for_day(yyyy_mm_dd, choose_manually=True)
    elif msg != "ignore":
        InfoMsgBox(QMessageBox.Critical, "Error", msg)


if __name__ == "__main__":
    colorama.init()
    validate_sermon_upload_config()
    choose_and_upload_sermon()
