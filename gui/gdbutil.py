# Copyright (C) 2015 Tom Tromey <tom@tromey.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Little gdb utilities.

import gdb
from gui.startup import in_gdb_thread

@in_gdb_thread
def is_running():
    """Return True if the inferior is running."""
    # This seems good enough for now.
    # We can deal with scheduler locking and the rest later.
    if gdb.selected_thread() and gdb.selected_thread().is_running():
        return True
    return False
