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
The song files (slidegen format) as a collection: which song number a file
has ("gm 37" from its "book:" line), the index number -> files, and checks
for what makes slidegen stop on a file.

The song number is the key shared with the Liederdatenbank of the intern
area (gottesdienst.json gives "nr" like "gm 37"). Only the standard library,
like song_structure, so it is testable and usable outside the toolbox.
"""

from dataclasses import dataclass, field
from os import listdir, path
from re import IGNORECASE, match, search

METADATA_KEYS = ("title", "book", "text", "melody", "structure")
# the same rule as input/parse_file.py
HEADER_REGEX = r"^(?!structure)\S+: .+|^structure: ([0-9]+|R)(,([0-9]+|R))*$"
SECTION_REGEX = r"^\[([0-9]+|R)\]$"

# (pattern on the "book:" value, short name as in the Liederdatenbank,
#  canonical "book:" value)
BOOKS = (
    (r"mennoniten", "gm", "Gesangbuch «Gesangbuch der Mennoniten» Nr. {}"),
    (r"liederordner", "LO", "Liederordner Nr. {}"),
    (r"singt\s+mit\s+uns", "Smu", "Gesangbuch «Singt mit uns» Nr. {}"),
    (
        r"neues\s+gemeinschafts-?\s*liederbuch",
        "Nglb",
        "Gesangbuch «Neues Gemeinschaftsliederbuch» Nr. {}",
    ),
)


def book_key(book: str) -> tuple[str | None, str]:
    """("gm 37", "") for a known book with a number, else (None, reason)."""
    number = search(r"Nr\.?\s*(\d+)\s*$", book.strip())
    if not number:
        return None, "keine Nummer"
    for pattern, short, _ in BOOKS:
        if search(pattern, book, IGNORECASE):
            return f"{short} {int(number.group(1))}", ""
    return None, "Buch nicht im Katalog"


def canonical_book(key: str) -> str:
    short, number = key.split(" ")
    for _, book_short, template in BOOKS:
        if book_short == short:
            return template.format(number)
    raise ValueError(key)


@dataclass
class SongFile:
    name: str
    header: dict = field(default_factory=dict)
    structure: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    errors: list = field(default_factory=list)  # slidegen stops on these
    notes: list = field(default_factory=list)  # worth a look
    key: str | None = None


def read_song(file_path: str, line_limit: int = 85) -> SongFile:
    song = SongFile(path.basename(file_path))
    try:
        with open(file_path, encoding="utf-8-sig") as reader:
            lines = reader.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        song.errors.append(f"nicht lesbar: {error}")
        return song

    missing = list(METADATA_KEYS)
    body_start = len(lines)
    for number, line in enumerate(lines):
        if not missing:
            body_start = number
            break
        if not match(HEADER_REGEX, line):
            song.errors.append(f"Kopfzeile {number + 1} ungültig: «{line}»")
            break
        key = line[: line.index(":")]
        if key not in missing:
            song.errors.append(f"Kopfzeile «{key}» unbekannt oder doppelt")
            break
        song.header[key] = line[line.index(": ") + 2 :]
        missing.remove(key)
    if missing and not song.errors:
        song.errors.append("Kopfzeilen fehlen: " + ", ".join(missing))

    body = lines[body_start:]
    for line in body:
        stripped = line.strip()
        if match(SECTION_REGEX, stripped):
            song.sections.append(stripped[1:-1])
        elif search(r"^\[([0-9]+|R)\]\s*\S", stripped):
            song.errors.append(f"Text hinter der Abschnittszeile: «{stripped}»")
        # slidegen counts the line break too (utils/strings.py)
        if len(line) + 1 > line_limit:
            song.errors.append(
                f"Zeile länger als {line_limit - 1} Zeichen: «{line[:40]}…»"
            )

    if "structure" in song.header:
        song.structure = song.header["structure"].split(",")
        for element in dict.fromkeys(song.structure):
            if element not in song.sections:
                song.errors.append(f"Abschnitt [{element}] fehlt")
        unused = [s for s in song.sections if s not in song.structure]
        if unused:
            song.notes.append(
                "Abschnitte nicht in der structure: "
                + ", ".join(f"[{s}]" for s in unused)
            )
        if "R" in song.structure and song.structure[-1] != "R":
            song.notes.append(
                "structure endet ohne R, obwohl das Lied einen Refrain hat:"
                + " eigener Schluss in der letzten Strophe, oder fehlt ein R?"
            )

    if "book" in song.header:
        song.key, _ = book_key(song.header["book"])
    return song


def read_songs(directory: str, line_limit: int = 85) -> list[SongFile]:
    return [
        read_song(path.join(directory, name), line_limit)
        for name in sorted(listdir(directory))
        if name.endswith(".txt")
    ]


def song_index(songs: list[SongFile]) -> dict[str, list[str]]:
    """Song number -> file names (more than one: copies, translations)."""
    index: dict[str, list[str]] = {}
    for song in songs:
        if song.key:
            index.setdefault(song.key, []).append(song.name)
    return index
