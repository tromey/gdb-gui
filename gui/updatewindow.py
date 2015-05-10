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

# Auto-updating window.

from gui.toplevel import Toplevel
import gui.startup
from gui.startup import in_gdb_thread, in_gtk_thread
import gdb
import gui.events

class UpdateWindow(Toplevel):
    """A window that automatically updates in response to gdb changes.

    In particular, starting or stopping the inferior, or switching
    frames, causes this window to be eligible for updates."""

    def __init__(self, window_type):
        super(UpdateWindow, self).__init__(window_type)
        gui.startup.send_to_gtk(self.gtk_initialize)
        self._connect_events()
        # Display the data now.
        self.on_event()

    @in_gtk_thread
    def gtk_initialize(self):
        """Subclasses should implement this method to do initialization
        in the Gtk thread."""
        pass

    # FIXME: really ought to be passing in an event here.
    @in_gdb_thread
    def on_event(self):
        """Subclasses should implement this method.
        It is called with no arguments when the state changes."""
        pass

    @in_gdb_thread
    def _connect_events(self):
        gdb.events.stop.connect(self._on_event)
        gui.events.frame_changed.connect(self._on_event)

    @in_gdb_thread
    def _disconnect_events(self):
        gdb.events.stop.disconnect(self._on_event)
        gui.event.frame_changed.disconnect(self._on_event)

    @in_gdb_thread
    def _on_event(self, *args):
        self.on_event()

    @in_gtk_thread
    def deleted(self, *args):
        gdb.post_event(self._disconnect_events)
        self.destroy()
