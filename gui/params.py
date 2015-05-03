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
from gi.repository import GtkSource
import gui.startup
from gui.startup import in_gdb_thread, in_gtk_thread
import gui.storage

class _SetBase(gdb.Command):
    def __init__(self):
        super(_SetBase, self).__init__('set gui', gdb.COMMAND_NONE,
                                       prefix = True)

class _ShowBase(gdb.Command):
    def __init__(self):
        super(_ShowBase, self).__init__('show gui', gdb.COMMAND_NONE,
                                        prefix = True)

class _Theme(gdb.Parameter):
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

_SetBase()
_ShowBase()
source_theme = _Theme()
