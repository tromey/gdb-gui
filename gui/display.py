# Copyright (C) 2013, 2015 Tom Tromey <tom@tromey.com>

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
import gui.updatewindow
import gui.startup
from gi.repository import Gtk, Pango
import functools
from gui.startup import in_gdb_thread, in_gtk_thread
import gui.events
from difflib import SequenceMatcher

# FIXME: TO DO:
# * highlight the changes

class DisplayWindow(gui.updatewindow.UpdateWindow):
    def __init__(self, command, diff = False):
        self.command = command
        self.diff = diff
        self.last_text = None
        super(DisplayWindow, self).__init__('display')

    @in_gdb_thread
    def on_event(self):
        try:
            text = gdb.execute(self.command, to_string = True)
        except gdb.error as what:
            text = str(what)
        gui.startup.send_to_gtk(lambda: self._update(text))

    @in_gtk_thread
    def gtk_initialize(self):
        builder = gui.startup.create_builder('logwindow.xml')
        builder.connect_signals(self)

        self.window = builder.get_object('logwindow')
        self.view = builder.get_object('textview')
        self.view.modify_font(Pango.FontDescription('Fixed'))

        self.buffer = builder.get_object('buffer')

        if self.diff:
            self.tag = self.buffer.create_tag('new', foreground = 'red')

        self.update_title()
        self.window.show()

    def _update(self, text):
        self.buffer.delete(self.buffer.get_start_iter(),
                           self.buffer.get_end_iter())
        if self.diff:
            if self.last_text is None:
                self.last_text = text.splitlines(1)
                # Fall through.
            else:
                split = text.splitlines(1)
                d = difflib.Differ()
                for line in d.compare(self.last_text, split):
                    if line[0] == ' ':
                        self.buffer.insert(self.buffer.get_end_iter(),
                                           line[2:])
                    elif line[0] == '+':
                        self.buffer.insert_with_tags(self.buffer.get_end_iter(),
                                                     line[2:],
                                                     self.tag)
                    self.buffer.insert(self.buffer.get_end_iter(), '\n')
                self.last_text = split
                return
        self.buffer.insert_at_cursor(text)
