# Copyright (C) 2013 Tom Tromey <tom@tromey.com>

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

# Log window.

import gdb
import gui.toplevel
import gui.startup
from gi.repository import Gtk
import os.path
import functools

default_log_window = None

class LogWindow(gui.toplevel.Toplevel):
    def __init__(self):
        super(LogWindow, self).__init__()
        global default_log_window
        default_log_window = self
        gui.startup.send_to_gtk(self._initialize)

    def _initialize(self):
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(gui.self_dir, 'logwindow.xml'))
        builder.connect_signals(self)

        self.window = builder.get_object('logwindow')
        self.view = builder.get_object('textview')
        self.buffer = builder.get_object('buffer')

        self.window.set_title('GDB Log @%d' % self.number)
        self.window.show()

    def deleted(self, widget, event):
        if default_log_window == self:
            default_log_window = None

    def _append(self, text):
        self.buffer.insert_at_cursor(text)
        self.view.scroll_mark_onscreen(self.buffer.get_insert())

    def append(self, text):
        gui.startup.send_to_gtk(functools.partial(self._append, text))
