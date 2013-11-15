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
import functools
from gui.startup import in_gdb_thread, in_gtk_thread
import gui.events

# FIXME: TO DO:
# * highlight the changes

class DisplayWindow(gui.toplevel.Toplevel):
    def __init__(self, command):
        super(DisplayWindow, self).__init__()
        self.command = command
        gui.startup.send_to_gtk(self._initialize)
        self._connect_events()
        # Display the data now.
        self._on_event()

    @in_gdb_thread
    def _connect_events(self):
        # FIXME - we need an event for "selected frame changed".
        # ... and thread-changed
        # really just pre-prompt would be good enough
        gdb.events.stop.connect(self._on_event)
        gui.events.frame_changed.connect(self._on_event)

    @in_gdb_thread
    def _disconnect_events(self):
        gdb.events.stop.disconnect(self.on_event)
        gui.event.frame_changed.disconnect(self.on_event)

    @in_gdb_thread
    def _on_event(self, *args):
        try:
            text = gdb.execute(self.command, to_string = True)
        except gdb.error as what:
            text = str(what)
        gui.startup.send_to_gtk(lambda: self._update(text))

    @in_gtk_thread
    def _initialize(self):
        builder = gui.startup.create_builder('logwindow.xml')
        builder.connect_signals(self)

        self.window = builder.get_object('logwindow')
        self.view = builder.get_object('textview')
        self.buffer = builder.get_object('buffer')

        self.window.set_title('GDB "%s" @%d' % (self.command, self.number))
        self.window.show()

    @in_gtk_thread
    def remove(self, window):
        self.windows.remove(window)
        if len(self.windows) == 0:
            gdb.post_event(self._disconnect_events)

    def _update(self, text):
        self.buffer.delete(self.buffer.get_start_iter(),
                           self.buffer.get_end_iter())
        self.buffer.insert_at_cursor(text)
