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

# Adapt to gdb issues.

import gdb
import gui.params

bugs = {
    "15620": """Your gdb doesn't have a "new breakpoint" event.
This means that the source windows will not show you where
breakpoints have been set.""",

    "13598": """Your gdb doesn't have a "before prompt" event.
This means that various windows won't be able to react to
commands like "up" or "down"."""
}

_first_report = True

def notify_bug(bugno):
    
