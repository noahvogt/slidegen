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
Sermon upload to the website of the Mennonitengemeinde Basel-Holee.

The metadata (title, preacher, Bible passage) is prefilled from the service
plan of the intern area (gottesdienst.json) and confirmed in one dialog. If
the plan is not reachable or incomplete, the fields stay empty and are filled
in by hand. The website endpoint (POST holee/v1/predigt) writes the ID3 tags,
file name and the Sermon Manager entry.
"""

import sys
from os import path
from shutil import copyfile
from subprocess import run
from dataclasses import dataclass
from datetime import date

import requests
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from utils import log
import config as const

UPLOAD_TIMEOUT_SECONDS = (10, 600)  # (connect, read): a sermon mp3 is ~40 MB


@dataclass
class Preacher:
    name: str
    guest: bool


@dataclass
class SermonMetadata:
    title: str = ""
    preacher: str = ""
    guest: bool = False
    bible_passage: str = ""


class SermonUploadError(Exception):
    pass


# Keeps the QApplication alive: the callers before us (e.g. the segment
# chooser) delete theirs, and an unreferenced new one would be garbage
# collected at once, so the next dialog aborts ("Must construct a
# QApplication before a QWidget").
_QAPP: QApplication | None = None


def get_qapp() -> QApplication:
    global _QAPP  # pylint: disable=global-statement
    app = QApplication.instance()
    if app is None:
        _QAPP = app = QApplication([])
    return app  # pyright: ignore


def show_message(icon: QMessageBox.Icon, title: str, text: str) -> None:
    get_qapp()
    box = QMessageBox(icon, title, text)
    box.exec_()


def fail(text: str) -> None:
    log(text, color="red")
    show_message(QMessageBox.Critical, "Predigt-Upload", text)
    sys.exit(1)


def german_date(yyyy_mm_dd: str) -> str:
    return date.fromisoformat(yyyy_mm_dd).strftime("%d.%m.%Y")


def api_url(endpoint: str) -> str:
    return const.SERMON_UPLOAD_HOLEE_API_BASE_URL.rstrip("/") + endpoint


def api_headers() -> dict:
    return {"X-Holee-Schluessel": const.SERMON_UPLOAD_HOLEE_KEY}


def error_text(response: requests.Response) -> str:
    try:
        message = response.json().get("message", "")
    except ValueError:
        message = ""
    return f"HTTP {response.status_code}" + (f": {message}" if message else "")


def api_get(endpoint: str, params: dict | None = None):
    try:
        response = requests.get(
            api_url(endpoint),
            params=params,
            headers=api_headers(),
            timeout=const.HTTP_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as error:
        raise SermonUploadError(
            f"Website nicht erreichbar ({type(error).__name__})."
        ) from error
    if response.status_code != 200:
        raise SermonUploadError(error_text(response))
    try:
        return response.json()
    except ValueError as error:
        raise SermonUploadError("Antwort der Website ist kein JSON.") from error


def get_preachers() -> list[Preacher]:
    data = api_get("/prediger")
    return [Preacher(str(p["name"]), bool(p["gast"])) for p in data]


def get_existing_sermon(yyyy_mm_dd: str) -> dict | None:
    data = api_get("/predigt", {"datum": yyyy_mm_dd})
    return data.get("predigt") if data.get("vorhanden") else None


def get_plan_metadata(yyyy_mm_dd: str) -> tuple[SermonMetadata, str]:
    """Metadata from the service plan of the intern area, plus a note for the
    dialog where the values come from or why they are missing."""
    url = const.SERMON_UPLOAD_SERVICE_INFO_URL
    if not url:
        return SermonMetadata(), "Kein Link zum Gottesdienstplan eingestellt."
    try:
        response = requests.get(
            url,
            params={"datum": yyyy_mm_dd},
            timeout=const.HTTP_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 404:
            # no service that day, or a wrong token ("Nicht gefunden")
            try:
                reason = response.json().get("fehler", "")
            except ValueError:
                reason = ""
            return SermonMetadata(), (
                f"Gottesdienstplan: {reason or 'nicht gefunden'}"
                + (" (Link prüfen)." if reason in ("", "Nicht gefunden") else ".")
            )
        response.raise_for_status()
        sermon = response.json()["predigt"]
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        log(f"could not get service plan: {e}", color="yellow")
        return SermonMetadata(), (
            f"Gottesdienstplan nicht erreichbar ({type(e).__name__})."
        )

    metadata = SermonMetadata(
        title=sermon.get("titel") or "",
        preacher=sermon.get("prediger") or "",
        guest=not sermon.get("prediger_konto", True),
        bible_passage=sermon.get("bibelstelle") or "",
    )
    return metadata, "Vorausgefüllt aus dem Gottesdienstplan."


def labels_of_empty_fields(metadata: SermonMetadata) -> list[str]:
    return [
        label
        for label, value in (
            ("Titel", metadata.title),
            ("Prediger", metadata.preacher),
            ("Bibelstelle", metadata.bible_passage),
        )
        if not value
    ]


def get_audio_duration(audiofile: str) -> str:
    """Length as "43:46" or "1:02:05", to see that the right audio was
    chosen; "unbekannt" if ffprobe cannot read it."""
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audiofile,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        secs = round(float(result.stdout.strip()))
    except ValueError:
        log(f"could not get duration of {audiofile}", color="yellow")
        return "unbekannt"
    hours, rest = divmod(secs, 3600)
    mins, secs = divmod(rest, 60)
    return f"{hours}:{mins:02}:{secs:02}" if hours else f"{mins}:{secs:02}"


class SermonMetadataDialog(QDialog):  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        yyyy_mm_dd: str,
        metadata: SermonMetadata,
        preachers: list[Preacher],
        note: str,
        duration: str,
        replace: bool,
    ):
        super().__init__()
        self.setWindowTitle("Predigt ersetzen" if replace else "Predigt hochladen")
        self.setMinimumWidth(520)
        self.preachers = preachers
        self.new_preacher = False
        action = "Ersetzen" if replace else "Hochladen"

        layout = QVBoxLayout(self)
        note_label = QLabel(
            note
            + "\nBitte prüfen und ergänzen. "
            + (
                f"Mit «{action}» wird die bestehende Predigt vom "
                + f"{german_date(yyyy_mm_dd)} auf der Website ersetzt."
                if replace
                else f"Mit «{action}» wird die Predigt auf der Website "
                + "veröffentlicht."
            )
        )
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        form = QFormLayout()
        form.addRow("Datum:", QLabel(german_date(yyyy_mm_dd)))
        form.addRow("Audio:", QLabel(f"{duration} (Länge)"))
        self.title_edit = QLineEdit(metadata.title)
        form.addRow("Titel:", self.title_edit)
        self.preacher_box = QComboBox()
        self.preacher_box.setEditable(True)
        self.preacher_box.setInsertPolicy(QComboBox.NoInsert)
        self.preacher_box.addItems(sorted({p.name for p in preachers}))
        self.preacher_box.setEditText(metadata.preacher)
        form.addRow("Prediger:", self.preacher_box)
        self.guest_check = QCheckBox("Gastprediger")
        self.guest_check.setChecked(metadata.guest)
        form.addRow("", self.guest_check)
        self.passage_edit = QLineEdit(metadata.bible_passage)
        self.passage_edit.setPlaceholderText("z.B. Epheser 6,1-9")
        form.addRow("Bibelstelle:", self.passage_edit)
        layout.addLayout(form)

        self.preacher_box.currentTextChanged.connect(self.sync_guest_flag)
        self.sync_guest_flag(metadata.preacher)

        buttons = QDialogButtonBox()
        buttons.addButton(action, QDialogButtonBox.AcceptRole)
        buttons.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def known_preacher(self, name: str) -> list[Preacher]:
        name = name.strip().casefold()
        return [p for p in self.preachers if p.name.casefold() == name]

    def sync_guest_flag(self, name: str) -> None:
        """A known preacher has a fixed guest flag on the website."""
        matches = self.known_preacher(name)
        if len(matches) == 1:
            self.guest_check.setChecked(matches[0].guest)
            self.preacher_box.setEditText(matches[0].name)

    def accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Titel fehlt", "Bitte einen Titel angeben.")
            return
        preacher = self.preacher_box.currentText().strip()
        if not preacher:
            QMessageBox.warning(self, "Prediger fehlt", "Bitte einen Prediger angeben.")
            return
        self.new_preacher = not self.known_preacher(preacher)
        if self.new_preacher:
            answer = QMessageBox.question(
                self,
                "Neuer Prediger",
                f"«{preacher}» gibt es auf der Website noch nicht.\n"
                + "Neu anlegen? (Bei einem Tippfehler «No» wählen und "
                + "korrigieren.)",
            )
            if answer != QMessageBox.Yes:
                return
        super().accept()

    def metadata(self) -> SermonMetadata:
        return SermonMetadata(
            title=self.title_edit.text().strip(),
            preacher=self.preacher_box.currentText().strip(),
            guest=self.guest_check.isChecked(),
            bible_passage=self.passage_edit.text().strip(),
        )


def convert_to_mp3(source_audio: str, target_audio: str) -> None:
    if path.splitext(source_audio)[1].lower() == ".mp3":
        copyfile(source_audio, target_audio)
        return
    log("Generating final mp3...")
    result = run(
        [
            "ffmpeg",
            "-y",
            "-i",
            source_audio,
            "-acodec",
            "libmp3lame",
            target_audio,
        ],
        check=False,
    )
    if result.returncode != 0:
        raise SermonUploadError(
            f"ffmpeg ist mit Exit-Code {result.returncode} abgebrochen."
        )


def post_sermon(
    mp3_path: str,
    yyyy_mm_dd: str,
    metadata: SermonMetadata,
    new_preacher: bool,
    replace: bool,
) -> dict:
    fields = {
        "datum": yyyy_mm_dd,
        "titel": metadata.title,
        "prediger": metadata.preacher,
        "bibelstelle": metadata.bible_passage,
        "gast": "1" if metadata.guest else "0",
        "neuer_prediger": "1" if new_preacher else "0",
        "ersetzen": "1" if replace else "0",
    }
    log(f"uploading {mp3_path} with {fields}...")
    try:
        with open(mp3_path, "rb") as mp3_file:
            response = requests.post(
                api_url("/predigt"),
                headers=api_headers(),
                data=fields,
                files={"datei": (path.basename(mp3_path), mp3_file, "audio/mpeg")},
                timeout=UPLOAD_TIMEOUT_SECONDS,
            )
    except (requests.exceptions.RequestException, OSError) as error:
        raise SermonUploadError(
            f"Upload fehlgeschlagen ({type(error).__name__}: {error})."
        ) from error
    if response.status_code not in (200, 201):
        raise SermonUploadError(error_text(response))
    return response.json()


def upload_sermon_to_website(audiofile: str, yyyy_mm_dd: str) -> None:
    get_qapp()
    try:
        preachers = get_preachers()
        existing = get_existing_sermon(yyyy_mm_dd)
    except SermonUploadError as error:
        fail(f"Website für den Predigt-Upload: {error}")
        return

    replace = False
    metadata, note = get_plan_metadata(yyyy_mm_dd)
    if existing:
        answer = QMessageBox.question(
            None,
            "Predigt schon vorhanden",
            f"Für den {german_date(yyyy_mm_dd)} gibt es schon die Predigt "
            + f"«{existing.get('titel')}».\nErsetzen?",
        )
        if answer != QMessageBox.Yes:
            sys.exit(0)
        replace = True
        # values of the existing sermon where the plan has none
        old_preachers = existing.get("prediger") or []
        plan_empty = labels_of_empty_fields(metadata)
        metadata = SermonMetadata(
            title=metadata.title or existing.get("titel") or "",
            preacher=metadata.preacher
            or (old_preachers[0].removesuffix(" (Gast)") if old_preachers else ""),
            guest=metadata.guest,
            bible_passage=metadata.bible_passage or existing.get("bibelstelle") or "",
        )
        taken = [f for f in plan_empty if f not in labels_of_empty_fields(metadata)]
        if taken:
            note += " Von der bestehenden Predigt übernommen: " + ", ".join(taken) + "."
    missing = labels_of_empty_fields(metadata)
    if missing:
        note += " Fehlt noch: " + ", ".join(missing) + "."

    dialog = SermonMetadataDialog(
        yyyy_mm_dd,
        metadata,
        preachers,
        note,
        get_audio_duration(audiofile),
        replace,
    )
    if dialog.exec_() != QDialog.Accepted:
        log("sermon upload canceled")
        sys.exit(0)
    metadata = dialog.metadata()

    mp3_path = path.join(path.dirname(audiofile), f"predigt-{yyyy_mm_dd}.mp3")
    try:
        convert_to_mp3(audiofile, mp3_path)
        result = post_sermon(
            mp3_path, yyyy_mm_dd, metadata, dialog.new_preacher, replace
        )
    except SermonUploadError as error:
        fail(f"Predigt nicht hochgeladen: {error}")
        return

    sermon = result.get("predigt", {})
    text = (
        f"Predigt «{sermon.get('titel', metadata.title)}» "
        + ("ersetzt" if result.get("ersetzt") else "hochgeladen")
        + f".\n\n{sermon.get('link', '')}"
    )
    warnings = result.get("warnungen") or []
    if warnings:
        text += "\n\nHinweis: " + "\n".join(warnings)
    log(text)
    show_message(
        QMessageBox.Warning if warnings else QMessageBox.Information,
        "Predigt-Upload",
        text,
    )
