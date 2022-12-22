#!/usr/bin/env python3

"""
Copyright © 2022 Noah Vogt <noah@noahvogt.com>

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

from os import name, path
from abc import ABC, abstractmethod
import sys
import re

from termcolor import colored
import colorama

from wand.image import Image
from wand.color import Color
from wand.display import display
from wand.drawing import Drawing
from wand.font import Font
from wand.exceptions import BlobError

IMAGE_FORMAT = "jpeg"
FILE_EXTENSION = "jpg"
FILE_NAMEING = "folie"

WIDTH = 1920
HEIGHT = 1080
BG_COLOR = Color("white")
FG_COLOR = Color("#6298a4")

TITLE_COLOR = Color("#d8d5c4")
MAX_TITLE_FONT_SIZE = 70
MIN_TITLE_FONT_SIZE = 20
TITLE_FONT_SIZE_STEP = 10
TITLE_HEIGHT = 160
TITLEBAR_Y = 65

INFODISPLAY_FONT_SIZE = 25
INFODISPLAY_ITEM_WIDTH = 20

PLAYER_WIDTH = 560
PLAYER_HEIGHT = 315

BOLD_FONT_PATH = (
    "/usr/share/fonts/TTF/century-gothic/CenturyGothicBold.ttf"
    if name == "posix"
    else "winPATH"
)
FONT_PATH = (
    "/usr/share/fonts/TTF/century-gothic/CenturyGothic.ttf"
    if name == "posix"
    else "winPATH"
)
FONT = "Century-Gothic"
BOLD_FONT = "Century-Gothic-Bold"

TRIANGLE_WIDTH = 80
TRIANGLE_HEIGTH = 160

METADATA_FONT_SIZE = 36
METADATA_X = 70
BOOK_Y = 260
ATTRIBUTIONS_Y = 930

TEXT_COLOR = Color("black")

VERSE_X = 80
VERSE_Y = 400
TEXT_CANVAS_X = 160
TEXT_CANVAS_Y = 400
TEXT_CANVAS_WIDTH = 1600
TEXT_CANVAS_HEIGHT = 600
STRUCTURE_X = 1650
STRUCTURE_Y = 1000
MAX_CANVAS_FONT_SIZE = 55
MIN_CANVAS_FONT_SIZE = 35
CANVAS_FONT_SIZE_STEP = 5
INTERLINE_SPACING = 30

METADATA_STRINGS = ("title", "book", "text", "melody", "structure")


def error_msg(msg: str):
    print(colored("[*] Error: {}".format(msg), "red"))
    sys.exit(1)


def log(message: str):
    print(colored("[*] {}".format(message), "green"))


def get_empty_image() -> Image:
    img = Image(width=1, height=1, background=Color("white"))
    return img.clone()


def structure_as_list(structure: str) -> list:
    return structure.replace(" ", "").split(",")


def get_unique_structure_elements(structure: list) -> list:
    return list(dict.fromkeys(structure))


def get_songtext_by_structure(content: list, structure: str) -> str:
    found_desired_structure = False
    output_str = ""

    for line in content:
        stripped_line = line.strip()
        if found_desired_structure:
            if stripped_line.startswith("[") and stripped_line.endswith("]"):
                break
            output_str += stripped_line + "\n"

        if (
            stripped_line.startswith("[")
            and stripped_line.endswith("]")
            and structure in stripped_line
        ):
            found_desired_structure = True

    return output_str[:-1]


class SongTemplate(ABC):
    @abstractmethod
    def get_template(self, title: str) -> Image:
        pass


class StartSlide(ABC):
    @abstractmethod
    def get_slide(
        self,
        template_img: Image,
        book: str,
        text_author: str,
        melody_author: str,
    ):
        pass


class SongSlide(ABC):
    @abstractmethod
    def get_slide(
        self,
        template_img: Image,
        slide_text: str,
        song_structure: list,
        index: int,
    ):
        pass


class ClassicSongSlide(SongSlide):
    def get_slide(
        self,
        template_img: Image,
        slide_text: str,
        song_structure: list,
        index: int,
    ):
        canvas_img, font_size = self.get_text_canvas(slide_text)
        verse_or_chorus = song_structure[index]
        bg_img = template_img.clone()
        if "R" not in verse_or_chorus:
            bg_img.composite(
                self.get_index(verse_or_chorus, font_size),
                top=VERSE_Y,
                left=VERSE_X,
            )
        bg_img.composite(canvas_img, top=TEXT_CANVAS_Y, left=TEXT_CANVAS_X)
        bg_img.composite(
            self.get_structure_info_display(song_structure, index),
            top=STRUCTURE_Y,
            left=STRUCTURE_X,
        )
        return bg_img

    def get_text_canvas(self, slide_text: str) -> tuple:
        font_size = MAX_CANVAS_FONT_SIZE
        while font_size >= MIN_CANVAS_FONT_SIZE:
            with Drawing() as draw:
                draw.fill_color = TEXT_COLOR
                draw.text_interline_spacing = INTERLINE_SPACING
                draw.font_size = font_size
                draw.font = FONT
                draw.text(0, font_size, slide_text)
                with Image(
                    width=WIDTH, height=HEIGHT, background=BG_COLOR
                ) as img:
                    draw(img)
                    img.trim()
                    if (
                        img.width > TEXT_CANVAS_WIDTH
                        or img.height > TEXT_CANVAS_HEIGHT
                    ):
                        font_size -= CANVAS_FONT_SIZE_STEP
                        display(img)
                    else:
                        return img.clone(), font_size
        return get_empty_image(), 0

    def get_structure_info_display(self, structure: list, index: int) -> Image:
        with Drawing() as draw:
            draw.fill_color = TEXT_COLOR
            draw.font_size = INFODISPLAY_FONT_SIZE
            draw.font = FONT
            for current_index, item in enumerate(structure):
                if current_index == index:
                    draw.font = BOLD_FONT
                    draw.text(
                        current_index * INFODISPLAY_ITEM_WIDTH,
                        INFODISPLAY_FONT_SIZE,
                        item,
                    )
                    draw.font = FONT
                else:
                    draw.text(
                        current_index * INFODISPLAY_ITEM_WIDTH,
                        INFODISPLAY_FONT_SIZE,
                        item,
                    )
            with Image(width=WIDTH, height=HEIGHT, background=BG_COLOR) as img:
                draw(img)
                img.trim()

                return img.clone()

    def get_index(self, verse: str, font_size: int) -> Image:
        with Image(width=WIDTH, height=HEIGHT, background=BG_COLOR) as img:
            img.caption(
                verse + ".",
                font=Font(FONT_PATH, size=font_size, color=TEXT_COLOR),
            )
            img.trim()
            return img.clone()


class ClassicStartSlide(StartSlide):
    def get_slide(
        self,
        template_img: Image,
        book: str,
        text_author: str,
        melody_author: str,
    ):
        start_img = template_img.clone()
        start_img.composite(
            self.get_attributions(text_author, melody_author),
            left=METADATA_X,
            top=ATTRIBUTIONS_Y,
        )
        start_img.composite(self.get_book(book), left=METADATA_X, top=BOOK_Y)
        return start_img.clone()

    def get_metadata(self, text: str) -> Image:
        with Image(width=WIDTH, height=HEIGHT, background=BG_COLOR) as img:
            img.caption(
                text,
                font=Font(FONT_PATH, size=METADATA_FONT_SIZE, color=TEXT_COLOR),
            )
            img.trim()
            return img.clone()

    def get_attributions(self, text_author: str, melody_author: str) -> Image:
        if text_author == melody_author:
            return self.get_metadata("Text & Melodie: " + text_author)
        return self.get_metadata(
            "Text: " + text_author + "\nMelodie: " + melody_author
        )

    def get_book(self, book: str) -> Image:
        return self.get_metadata(book)


class ClassicSongTemplate(SongTemplate):
    def __init__(self):
        self.song_template = ""

    def get_base_image(self) -> Image:
        with Image(width=WIDTH, height=HEIGHT, background=BG_COLOR) as img:
            return img.clone()

    def get_titlebar_rectangle(self, text: str) -> Image:
        font_size = MAX_TITLE_FONT_SIZE
        while font_size >= MIN_TITLE_FONT_SIZE:
            with Image(
                width=WIDTH, height=TITLE_HEIGHT, background=FG_COLOR
            ) as img:
                img.caption(
                    text,
                    font=Font(
                        BOLD_FONT_PATH, size=font_size, color=TITLE_COLOR
                    ),
                )
                img.trim()
                img.border(color=FG_COLOR, width=30, height=0)
                trimmed_img_width = img.width
                trimmed_img_height = img.height
                concat_height = int((TITLE_HEIGHT - trimmed_img_height) / 2)
                correction_heigt = (
                    TRIANGLE_HEIGTH - trimmed_img_height - (2 * concat_height)
                )
                concatenated_img = Image(
                    width=trimmed_img_width,
                    height=concat_height,
                    background=FG_COLOR,
                )
                concatenated_img.sequence.append(img)
                concatenated_img.sequence.append(
                    Image(
                        width=trimmed_img_width,
                        height=concat_height + correction_heigt,
                        background=FG_COLOR,
                    )
                )
                concatenated_img.concat(stacked=True)
                if concatenated_img.width > (
                    WIDTH - PLAYER_WIDTH - TRIANGLE_WIDTH
                ):
                    font_size -= TITLE_FONT_SIZE_STEP
                    continue

                return concatenated_img.clone()
        return get_empty_image()

    def get_template(self, title: str) -> Image:
        titlebar_rectangle = self.get_titlebar_rectangle(title)
        titlebar_rectangle.sequence.append(self.get_titlebar_triangle())
        titlebar_rectangle.concat(stacked=False)
        base_img = self.get_base_image()
        base_img.composite(titlebar_rectangle, top=TITLEBAR_Y)
        self.song_template = base_img.clone()
        return base_img.clone()

    def get_titlebar_triangle(self) -> Image:
        with Drawing() as draw:
            draw.fill_color = FG_COLOR
            draw.path_start()
            draw.path_move(to=(TRIANGLE_WIDTH, 0))
            draw.path_line(to=(0, 0))
            draw.path_line(to=(0, TRIANGLE_HEIGTH))
            draw.path_close()
            draw.path_finish()

            with Image(
                width=TRIANGLE_WIDTH,
                height=TRIANGLE_HEIGTH,
                background=BG_COLOR,
            ) as img:
                draw(img)
                return img.clone()

    def display(self):
        display(self.song_template)


class Slidegen:
    def __init__(self, song_template_form, start_slide_form, song_slide_form):
        self.metadata: dict = {"": ""}
        self.songtext: dict = {"": ""}
        self.song_file_path: str = ""
        self.song_file_content: list = []
        self.output_dir: str = ""
        self.chosen_structure: list | str = ""
        self.generated_slides: list = []
        self.song_template_form = song_template_form
        self.start_slide_form = start_slide_form
        self.song_slide_form = song_slide_form
        self.parse_argv()

    def execute(self):
        self.parse_file()
        self.calculate_desired_structures()
        self.generate_slides()

    def generate_slides(self):
        song_template = self.song_template_form()
        log("generating template...")
        template_img = song_template.get_template(self.metadata["title"])

        first_slide = self.start_slide_form()
        log("generating start slide...")
        start_slide_img = first_slide.get_slide(
            template_img,
            self.metadata["book"],
            self.metadata["text"],
            self.metadata["melody"],
        )
        start_slide_img.format = IMAGE_FORMAT
        try:
            start_slide_img.save(
                filename=path.join(
                    self.output_dir, FILE_NAMEING + "1." + FILE_EXTENSION
                )
            )
        except BlobError:
            error_msg("could not write start slide to target directory")
        log("generating song slides...")
        for index, structure in enumerate(self.chosen_structure):
            log(
                "generating song slide [{} / {}]...".format(
                    index + 1, len(self.chosen_structure)
                )
            )
            song_slide = self.song_slide_form()
            song_slide_img = song_slide.get_slide(
                template_img,
                self.songtext[structure],
                self.chosen_structure,
                index,
            )
            song_slide_img.format = IMAGE_FORMAT
            try:
                song_slide_img.save(
                    filename=path.join(
                        self.output_dir,
                        FILE_NAMEING + str(index + 2) + "." + FILE_EXTENSION,
                    )
                )
            except BlobError:
                error_msg("could not write slide to target directory")

    def parse_file(self):
        self.parse_metadata()
        self.parse_songtext()

    def parse_metadata(self):
        metadata_dict = dict.fromkeys(METADATA_STRINGS)
        try:
            with open(self.song_file_path, mode="r", encoding="utf8") as opener:
                content = opener.readlines()
        except IOError:
            error_msg(
                "could not read the the song input file: '{}'".format(
                    self.song_file_path
                )
            )
        valid_metadata_strings = list(METADATA_STRINGS)

        for line_nr, line in enumerate(content):
            if len(valid_metadata_strings) == 0:
                content = content[line_nr:]
                break
            if not re.match(
                r"^(?!structure)\S+: .+|^structure: ([0-9]+|R)(,([0-9]+|R))+$",
                line,
            ):
                if line[-1] == "\n":
                    line = line[:-1]
                missing_metadata_strs = ""
                for metadata_str in valid_metadata_strings:
                    missing_metadata_strs += ", " + metadata_str
                missing_metadata_strs = missing_metadata_strs[2:]
                error_msg(
                    "invalid metadata syntax on line {}:\n{}\nThe ".format(
                        line_nr + 1, line
                    )
                    + "following metadata strings are still missing: {}".format(
                        missing_metadata_strs
                    )
                )
            metadata_str = line[: line.index(":")]
            if metadata_str in valid_metadata_strings:
                metadata_dict[metadata_str] = line[line.index(": ") + 2 : -1]
                valid_metadata_strings.remove(metadata_str)
                continue

            error_msg("invalid metadata string '{}'".format(metadata_str))

        self.metadata = metadata_dict
        self.song_file_content = content

    def parse_songtext(self):
        unique_structures = get_unique_structure_elements(
            structure_as_list(self.metadata["structure"])
        )
        output_dict = dict.fromkeys(unique_structures)

        for structure in unique_structures:
            output_dict[structure] = get_songtext_by_structure(
                self.song_file_content, structure
            )

        self.songtext = output_dict

    def calculate_desired_structures(self):
        full_structure_str = str(self.metadata["structure"])
        full_structure_list = structure_as_list(full_structure_str)
        if len(self.chosen_structure) == 0:
            self.chosen_structure = structure_as_list(full_structure_str)
            log("chosen structure: {}".format(str(self.chosen_structure)))
            return
        if not "-" in self.chosen_structure:
            self.chosen_structure = structure_as_list(
                str(self.chosen_structure)
            )
            log("chosen structure: {}".format(str(self.chosen_structure)))
            return

        dash_index = str(self.chosen_structure).find("-")
        start_verse = str(self.chosen_structure[:dash_index]).strip()
        end_verse = str(self.chosen_structure[dash_index + 1 :]).strip()

        try:
            if int(start_verse) >= int(end_verse):
                error_msg("{} < {} must be true".format(start_verse, end_verse))
            if start_verse not in full_structure_str:
                error_msg("structure {} unknown".format(start_verse))
            if end_verse not in full_structure_str:
                error_msg("structure {} unknown".format(end_verse))
        except (ValueError, IndexError):
            error_msg("please choose a valid integer for the song structure")

        start_index = full_structure_list.index(start_verse)
        if start_index != 0:
            if (
                full_structure_list[0] == "R"
                and full_structure_list[start_index - 1] == "R"
            ):
                start_index -= 1
        end_index = full_structure_list.index(end_verse)
        if end_index != len(full_structure_list) - 1:
            if (
                full_structure_list[-1] == "R"
                and full_structure_list[end_index + 1] == "R"
            ):
                end_index += 1

        self.chosen_structure = full_structure_list[start_index : end_index + 1]
        log("chosen structure: {}".format(str(self.chosen_structure)))

    def parse_argv(self):
        try:
            self.song_file_path = sys.argv[1]
            self.output_dir = sys.argv[2]
        except IndexError:
            error_msg("incorrect amount of arguments provided, exiting...")
        try:
            self.chosen_structure = sys.argv[3]
            if self.chosen_structure.strip() == "":
                self.chosen_structure = ""
        except IndexError:
            self.chosen_structure = ""

        log("parsing {}...".format(self.song_file_path))


def main():
    colorama.init()

    slidegen = Slidegen(
        ClassicSongTemplate, ClassicStartSlide, ClassicSongSlide
    )
    slidegen.execute()


if __name__ == "__main__":
    main()
