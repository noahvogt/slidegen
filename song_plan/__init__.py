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
Which song goes into which slide folder ("Lied N"), from the Ablauf of the
service (gottesdienst.json of the intern area) and the song files:

- the song of "Lied 3" in the Ablauf goes to the folder "Lied 3", so the
  numbers are the same as in the mail; alternatives get no slides (one
  version is enough for the livestream), they are only named as a note;
  further songs of a place (older Ablauf) go to the free folders after the
  last song place
- the song file by song number (song_files), the title as a check
- the slide order from the verses of the Ablauf (song_structure)

Only the standard library; auto_slides.py shows the plan and makes the
slides.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from re import sub

from song_files import SongFile
from song_structure import resolve_prompt


@dataclass
class PlanItem:
    folder: int | None  # "Lied N"; None: no free folder left
    place: str  # "Lied 2 · (Kinder-)Lied 2"
    song: str  # "gm 268 Immer wieder könnt ich singen" or "" (open)
    verses: str  # as in the Ablauf, "" = all
    title: str = ""  # title alone, for comparing with the file
    alternative: bool = False
    note: str = ""  # Hinweis of the song place
    files: list[str] = field(default_factory=list)  # candidates, best first
    order: str = ""  # slide order for slidegen, "" = no slides
    warnings: list[str] = field(default_factory=list)


def normalize_title(title: str) -> str:
    """For comparing titles of the Liederdatenbank with the file names and
    titles, which are written without umlauts ("Grosser", "Hoeh")."""
    title = title.lower().replace("ß", "ss")
    for umlaut, ascii_form in (("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        title = title.replace(umlaut, ascii_form)
    title = sub(r"\((kernlied|standardlied|monatslied)\)", "", title)
    return sub(r"[^a-z0-9]+", " ", title).strip()


def title_similarity(a: str, b: str) -> float:
    a, b = normalize_title(a), normalize_title(b)
    if not a or not b:
        return 0.0
    if a.startswith(b) or b.startswith(a):  # shortened titles
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def service_warnings(service: dict) -> list[str]:
    ablauf = service.get("ablauf") or {}
    if not ablauf.get("vorhanden"):
        return ["Für diesen Gottesdienst gibt es noch keinen Ablauf."]
    if not ablauf.get("versandt"):
        return ["Der Ablauf ist noch nicht verschickt, er kann sich noch ändern."]
    if (ablauf.get("geaendert") or "") > ablauf["versandt"]:
        return [
            "Der Ablauf wurde nach dem Versand noch geändert "
            + f"({ablauf['geaendert']}), bitte mit der Leitung abgleichen."
        ]
    return []


def candidate_files(
    entry: dict, index: dict[str, list[str]], songs: dict[str, SongFile]
) -> list[str]:
    """Files for a song of gottesdienst.json, the best title match first."""
    keys = [entry.get("nr")] + [a.get("nr") for a in entry.get("auch") or []]
    files: list[str] = []
    for key in keys:
        for name in index.get(key or "", []):
            if name not in files:
                files.append(name)
    title = entry.get("titel") or ""
    if not files and title:
        # no song number (e.g. "nicht in der Datenbank"): the title alone,
        # only if it is clear
        files = [
            name
            for name, song in songs.items()
            if not song.errors
            and title_similarity(title, song.header.get("title", name)) == 1.0
        ]
    return sorted(
        files,
        key=lambda name: -title_similarity(
            title, songs[name].header.get("title", name)
        ),
    )


def plan_item(
    entry: dict,
    folder: int | None,
    index: dict[str, list[str]],
    songs: dict[str, SongFile],
) -> PlanItem:
    song = " ".join(x for x in (entry.get("nr"), entry.get("titel")) if x)
    item = PlanItem(
        folder=folder,
        place=entry.get("stelle", ""),
        song=song,
        title=entry.get("titel") or "",
        verses=(entry.get("strophen") or "").strip(),
        alternative=bool(entry.get("alternative")),
        note=entry.get("hinweis") or "",
    )
    if folder is None:
        item.warnings.append("Keine freie Folienstelle mehr (zu viele Lieder).")
    item.files = candidate_files(entry, index, songs)
    if not item.files:
        item.warnings.append("Keine Folien zu diesem Lied.")
        return item
    if len(item.files) > 1:
        item.warnings.append(
            f"{len(item.files)} Dateien zu diesem Lied, bitte die richtige wählen."
        )
    choose_file(item, item.files[0], songs)
    return item


def choose_file(item: PlanItem, name: str, songs: dict[str, SongFile]) -> None:
    """Set the file of an item (also when chosen in the overview) and its
    slide order; warnings about the file are made new."""
    item.warnings = [
        w
        for w in item.warnings
        if not w.startswith(("Titel", "Strophen", "Die Datei"))
    ]
    song = songs[name]
    item.files.remove(name)
    item.files.insert(0, name)
    if song.errors:
        item.order = ""
        item.warnings.append(f"Die Datei hat Fehler: {song.errors[0]}")
        return
    if title_similarity(item.title, song.header.get("title", name)) < 0.6:
        item.warnings.append(
            f"Titel weicht ab: Datei «{song.header.get('title', name)}»."
        )
    valid, order = resolve_prompt(item.verses, song.structure)
    if item.verses and not valid:
        item.warnings.append(
            f"Strophen «{item.verses}» passen nicht zum Lied "
            + f"({','.join(song.structure)}), es kommt das ganze Lied."
        )
    item.order = order if valid else ",".join(song.structure)


def build_plan(
    service: dict, songs: list[SongFile], max_folders: int
) -> list[PlanItem]:
    by_name = {song.name: song for song in songs}
    index: dict[str, list[str]] = {}
    for song in songs:
        if song.key:
            index.setdefault(song.key, []).append(song.name)

    places: dict[int, list[dict]] = {}
    for entry in service.get("lieder") or []:
        places.setdefault(int(entry.get("lied_nr") or 0), []).append(entry)
    spare = max(places, default=0) + 1

    items: list[PlanItem] = []
    extra: list[dict] = []
    for number in sorted(places):
        entries = places[number]
        if entries[0].get("offen"):
            items.append(
                PlanItem(
                    folder=number,
                    place=entries[0].get("stelle", ""),
                    song="",
                    verses="",
                    note=entries[0].get("hinweis") or "",
                    warnings=["Im Ablauf noch offen."],
                )
            )
            continue
        main = next((e for e in entries if not e.get("alternative")), entries[0])
        item = plan_item(main, number, index, by_name)
        for alt in (e for e in entries if e is not main and e.get("alternative")):
            name = " ".join(x for x in (alt.get("nr"), alt.get("titel")) if x)
            item.warnings.append(f"Alternative: {name} (keine Folien)")
        items.append(item)
        extra += [e for e in entries if e is not main and not e.get("alternative")]
    for entry in extra:
        folder = spare if spare <= max_folders else None
        spare += 1
        items.append(plan_item(entry, folder, index, by_name))
    return items
