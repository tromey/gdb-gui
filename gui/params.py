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

# Parameters

import gdb
import gui.startup
import gui.storage
import gui.toplevel

from gui.startup import in_gdb_thread, in_gtk_thread
from gi.repository import GtkSource, Pango

class _SetBase(gdb.Command):
    """Generic command for modifying GUI settings."""

    def __init__(self):
        super(_SetBase, self).__init__('set gui', gdb.COMMAND_NONE,
                                       prefix = True)

class _ShowBase(gdb.Command):
    """Generic command for showing GUI settings."""

    def __init__(self):
        super(_ShowBase, self).__init__('show gui', gdb.COMMAND_NONE,
                                        prefix = True)

class _Theme(gdb.Parameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set the source window theme."
    show_doc = "Show the source window theme."

    def __init__(self):
        self.manager = GtkSource.StyleSchemeManager.get_default()
        self.storage = gui.storage.storage_manager
        super(_Theme, self).__init__('gui theme', gdb.COMMAND_NONE,
                                     gdb.PARAM_ENUM,
                                     # Probably the wrong thread.
                                     self.manager.get_scheme_ids())
        val = self.storage.get('theme')
        if val is not None:
            self.value = val

    @in_gdb_thread
    def set_buffer_manager(self, b):
        self.buffer_manager = b

    @in_gtk_thread
    def get_scheme(self):
        # Sorta racy
        return self.manager.get_scheme(self.value)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The current theme is: " + self.value

    @in_gdb_thread
    def get_set_string(self):
        self.storage.set('theme', self.value)
        self.buffer_manager.change_theme()
        return ""

class _Font(gdb.Parameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set the source window font."
    show_doc = "Show the source window font."

    def __init__(self):
        self.manager = GtkSource.StyleSchemeManager.get_default()
        self.storage = gui.storage.storage_manager
        super(_Font, self).__init__('gui font', gdb.COMMAND_NONE,
                                    gdb.PARAM_STRING)
        val = self.storage.get('font')
        if val is not None:
            self.value = val
        else:
            self.value = 'monospace'

    @in_gtk_thread
    def get_font(self):
        # Sorta racy
        return Pango.FontDescription(self.value)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The current font is: " + self.value

    @in_gdb_thread
    def get_set_string(self):
        gui.toplevel.state.set_font(self.value)
        self.storage.set('font', self.value)
        return ""

_SetBase()
_ShowBase()
source_theme = _Theme()
font_manager = _Font()
