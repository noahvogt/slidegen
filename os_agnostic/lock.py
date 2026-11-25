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

import sys
from typing import IO

if sys.platform == "win32":

    def lock_file_exclusively(file: IO) -> None:
        """No locking on windows."""

else:
    from fcntl import flock, LOCK_EX

    def lock_file_exclusively(file: IO) -> None:
        """Block until no other process holds the lock, released on close."""
        flock(file.fileno(), LOCK_EX)
