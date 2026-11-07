#!/usr/bin/env python3

# Copyright © 2026 Noah Vogt <noah@noahvogt.com>

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

"""
Song slides from the Ablauf of the service (VulcanBoard button "Folien aus
Ablauf"), instead of choosing every song in ssync:

1. sync the song files (as ssync), get gottesdienst.json of the day
2. plan which song goes into which "Lied N" folder (song_plan)
3. show the plan; the Live-Technik checks it and confirms
4. make the slides and put them into the OBS slideshows

ssync stays as the way by hand; note that it empties all "Lied N" folders
when it starts.

    ./auto_slides.py                    the service of today
    ./auto_slides.py --datum 2026-11-08
    ./auto_slides.py --dry-run          only print the plan (no GUI, no OBS)
"""

import argparse
import contextlib
import io
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests

import config as const
from song_files import read_songs
from song_plan import PlanItem, build_plan, choose_file, service_warnings

APP = None  # the QApplication, kept alive for all dialogs


def qt():
    # pylint: disable=import-outside-toplevel,global-statement
    from PyQt5.QtWidgets import QApplication

    global APP
    if QApplication.instance() is None:
        APP = QApplication([])
    return APP


def message(text: str, error: bool = False) -> None:
    print(text)
    # pylint: disable=import-outside-toplevel
    from PyQt5.QtWidgets import QMessageBox

    qt()
    box = QMessageBox(
        QMessageBox.Critical if error else QMessageBox.Information,
        "Folien aus dem Ablauf",
        text,
    )
    box.exec_()


def german_date(yyyy_mm_dd: str) -> str:
    return date.fromisoformat(yyyy_mm_dd).strftime("%d.%m.%Y")


def get_service(yyyy_mm_dd: str) -> dict:
    url = const.SERMON_UPLOAD_SERVICE_INFO_URL
    if not url:
        raise RuntimeError("Kein Link zum Gottesdienstplan eingestellt.")
    response = requests.get(
        url, params={"datum": yyyy_mm_dd}, timeout=const.HTTP_REQUEST_TIMEOUT_SECONDS
    )
    if response.status_code == 404:
        raise RuntimeError(f"Im Gottesdienstplan gibt es am {german_date(yyyy_mm_dd)} keinen Gottesdienst.")
    response.raise_for_status()
    return response.json()


def obs_client():
    # pylint: disable=import-outside-toplevel
    import obsws_python as obs

    with contextlib.redirect_stderr(io.StringIO()):
        return obs.ReqClient(
            host=const.OBS_WEBSOCKET_HOSTNAME,
            port=const.OBS_WEBSOCKET_PORT,
            password=const.OBS_WEBSOCKET_PASSWORD,
            timeout=3,
        )


def put_slides_into_obs() -> list[str]:
    """As add_slides_to_obs_slideshow_inputs() of ssync, but without waiting
    for a terminal: returns the problems instead."""
    pattern = re.compile(rf"{const.FILE_NAMING}(\d+)\.jpg$", re.IGNORECASE)
    try:
        client = obs_client()
    except Exception:  # pylint: disable=broad-except
        return ["OBS läuft nicht: die Folien sind erzeugt, OBS zeigt sie nach dem Start an."]
    problems = []
    for number in range(1, const.OBS_MIN_SUBDIRS + 1):
        folder = Path(const.OBS_SLIDES_DIR) / f"{const.OBS_SUBDIR_NAMING}{number}"
        slides = sorted(
            (int(m.group(1)), str(p.resolve()))
            for p in folder.iterdir()
            if (m := pattern.match(p.name))
        )
        source = f"{const.SSYNC_SLIDESHOW_INPUT_NAMING}{number}"
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                settings = dict(client.get_input_settings(source).input_settings)
                settings["files"] = [{"value": path} for _, path in slides]
                client.set_input_settings(name=source, settings=settings, overlay=False)
        except Exception:  # pylint: disable=broad-except
            problems.append(f"OBS-Quelle «{source}» nicht gefunden.")
    return problems


def make_slides(plan: list[PlanItem], songs_dir: str) -> list[str]:
    # pylint: disable=import-outside-toplevel
    import slidegen
    from input.slide_selection_iterator import create_and_get_dest_dir
    from slides import (
        ClassicSongSlide,
        ClassicSongTemplate,
        ClassicStartSlide,
        SlideStyle,
    )
    from utils import clear_obs_slides_dir, create_min_obs_subdirs, expand_dir

    style = SlideStyle(
        ClassicSongTemplate,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicStartSlide,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicSongSlide,  # pyright: ignore [reportGeneralTypeIssues]
    )
    clear_obs_slides_dir()
    threads = []
    for item in plan:
        if item.folder is None or not item.order or not item.files:
            continue
        dest_dir = create_and_get_dest_dir(expand_dir(const.OBS_SLIDES_DIR), item.folder)
        print(f"Lied {item.folder}: {item.files[0]} ({item.order})")
        threads += slidegen.Slidegen(
            style, str(Path(songs_dir) / item.files[0]), dest_dir, item.order
        ).execute()
    for thread in threads:
        thread.join()
    create_min_obs_subdirs()
    return put_slides_into_obs()


def overview(plan: list[PlanItem], service: dict, yyyy_mm_dd: str, songs: dict) -> bool:
    """The plan for the Live-Technik; True when confirmed. A song with
    several files gets a choice."""
    # pylint: disable=import-outside-toplevel
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )

    qt()
    dialog = QDialog()
    dialog.setWindowTitle(f"Folien aus dem Ablauf vom {german_date(yyyy_mm_dd)}")
    dialog.resize(1150, 520)
    layout = QVBoxLayout(dialog)
    notes = service_warnings(service) + [
        "Ersetzt die Folien in allen Ordnern «Lied 1» bis "
        + f"«Lied {const.OBS_MIN_SUBDIRS}». Bitte prüfen und bestätigen."
    ]
    label = QLabel("\n".join(notes))
    label.setWordWrap(True)
    layout.addWidget(label)

    table = QTableWidget(len(plan), 5)
    table.setHorizontalHeaderLabels(["Ordner", "Lied im Ablauf", "Datei", "Folien", "Hinweise"])
    for row, item in enumerate(plan):
        folder = f"Lied {item.folder}" if item.folder else "–"
        song = item.song or "(offen)"
        if item.alternative:
            song += f"  [Alternative zu {item.place}]"
        cells = [folder, song, "", item.order or "keine Folien",
                 "\n".join(([f"Hinweis: {item.note}"] if item.note else []) + item.warnings)]
        for col, text in enumerate(cells):
            cell = QTableWidgetItem(text)
            cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
            if col == 4 and any(not w.startswith("Alternative:") for w in item.warnings):
                cell.setForeground(Qt.darkRed)
            table.setItem(row, col, cell)
        if len(item.files) > 1:
            box = QComboBox()
            box.addItems(item.files)

            def changed(name, item=item, row=row):
                choose_file(item, name, songs)
                table.item(row, 3).setText(item.order or "keine Folien")
                table.item(row, 4).setText(
                    "\n".join(([f"Hinweis: {item.note}"] if item.note else []) + item.warnings)
                )

            box.currentTextChanged.connect(changed)
            table.setCellWidget(row, 2, box)
        else:
            table.setItem(row, 2, QTableWidgetItem(item.files[0] if item.files else "–"))
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    layout.addWidget(table)

    buttons = QDialogButtonBox()
    buttons.addButton("Folien erzeugen", QDialogButtonBox.AcceptRole)
    buttons.addButton("Abbrechen", QDialogButtonBox.RejectRole)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    return dialog.exec_() == QDialog.Accepted


def print_plan(plan: list[PlanItem], service: dict) -> None:
    for note in service_warnings(service):
        print(f"! {note}")
    for item in plan:
        print(
            f"Lied {item.folder or '–'}: {item.song or '(offen)'}"
            + (" [Alternative]" if item.alternative else "")
            + f" | Str. {item.verses or 'alle'} | {item.files[0] if item.files else '–'}"
            + f" | {item.order or 'keine Folien'}"
            + (f" | Hinweis: {item.note}" if item.note else "")
            + "".join(f"\n    ! {w}" for w in item.warnings)
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--datum", default=date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--offline", action="store_true", help="no rclone sync")
    args = parser.parse_args()

    # pylint: disable=import-outside-toplevel
    songs_dir = os.path.expandvars(os.path.expanduser(const.RCLONE_LOCAL_DIR))
    if not args.offline and not args.dry_run:
        import colorama
        from sync import sync_slide_repo, syncing_needed

        colorama.init()

        if syncing_needed(False):
            sync_slide_repo()
    try:
        service = get_service(args.datum)
    except (RuntimeError, requests.RequestException, ValueError) as error:
        if args.dry_run:
            sys.exit(f"Fehler: {error}")
        message(f"Gottesdienstplan: {error}\nDie Folien bitte wie bisher mit ssync machen.", error=True)
        return 1

    song_files = read_songs(songs_dir)
    plan = build_plan(service, song_files, const.OBS_MIN_SUBDIRS)
    if args.dry_run:
        print_plan(plan, service)
        return 0
    if not plan:
        message("Im Ablauf stehen keine Lieder.")
        return 1

    if not overview(plan, service, args.datum, {s.name: s for s in song_files}):
        print("abgebrochen")
        return 0
    problems = make_slides(plan, songs_dir)
    made = sum(1 for i in plan if i.folder and i.order and i.files)
    message(
        f"Folien für {made} Lieder erzeugt."
        + ("\n\n" + "\n".join(problems) if problems else "")
        + (
            "\n\nNicht alle Lieder haben Folien (siehe Übersicht). ssync kann sie"
            + " nicht ergänzen, es ersetzt immer alle Folien: entweder ohne diese"
            + " Folien arbeiten oder alle Lieder mit ssync machen."
            if any(i.folder and not (i.order and i.files) for i in plan if i.song)
            else ""
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
