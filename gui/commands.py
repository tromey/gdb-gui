# Copyright (C) 2012 Tom Tromey <tom@tromey.com>

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

import gdb
import gui.startup
import gui.source

class GuiCommand(gdb.Command):
    def __init__(self):
        super(GuiCommand, self).__init__('gui', gdb.COMMAND_SUPPORT,
                                         prefix = True)

class GuiSourceCommand(gdb.Command):
    """Create a new source window.
    Usage: gui source
    This creates a new source window in the GUI.  Any number of source
    windows can be created."""

    def __init__(self):
        super(GuiSourceCommand, self).__init__('gui source',
                                               gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        gui.startup.start_gtk()
        gui.startup.send_to_gtk(gui.source.SourceWindow)

GuiCommand()
GuiSourceCommand()
