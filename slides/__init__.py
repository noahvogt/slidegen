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

from .song_template import SongTemplate
from .start_slide import StartSlide
from .song_slide import SongSlide

from .slide_style import SlideStyle

from .classic_song_template import ClassicSongTemplate
from .classic_start_slide import ClassicStartSlide
from .classic_song_slide import ClassicSongSlide

from .engine.generate_slides import generate_slides
from .engine.song_template import generate_song_template
from .engine.calc_slide_count import count_number_of_slides_to_be_generated
