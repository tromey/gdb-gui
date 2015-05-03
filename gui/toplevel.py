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

# Toplevel handling.

import gdb
import gui.startup
import threading
from gi.repository import Pango
from gui.startup import in_gdb_thread, in_gtk_thread

class _ToplevelState(object):
    def __init__(self):
        gui.startup.start_gtk()
        # This lock must be held when using the other globals here.
        self.toplevel_lock = threading.Lock()
        self.next_toplevel = 1
        self.toplevels = {}

    def add(self, obj):
        with self.toplevel_lock:
            obj.number = self.next_toplevel
            self.next_toplevel = self.next_toplevel + 1
            self.toplevels[obj.number] = obj

    def remove(self, obj):
        with self.toplevel_lock:
            del self.toplevels[obj.number]

    def get(self, winno):
        window = None
        with self.toplevel_lock:
            if winno in self.toplevels:
                window = self.toplevels[winno]
        return window

    def display(self):
        with self.toplevel_lock:
            if len(self.toplevels) == 0:
                print "No windows"
                return

            print ' Num    Name'
            for winno in range(1, self.next_toplevel):
                if winno in self.toplevels:
                    window = self.toplevels[winno]
                    print ' %3d    %s' % (window.number,
                                          window.window.get_title())

    @in_gtk_thread
    def _do_set_font(self, font_name):
        pango_font = Pango.FontDescription(font_name)
        with self.toplevel_lock:
            for num in self.toplevels:
                self.toplevels[num].set_font(pango_font)

    @in_gdb_thread
    def set_font(self, font_name):
        gui.startup.send_to_gtk(lambda: self._do_set_font(font_name))

state = _ToplevelState()

class Toplevel(object):
    def __init__(self):
        state.add(self)
        # The subclass must set this.
        self.window = None

    def destroy(self):
        state.remove(self)
        gui.startup.send_to_gtk(self.window.destroy)
        self.window = None

    def valid(self):
        return self.window is not None

    @in_gtk_thread
    def set_font(self, pango_font):
        # Subclasses can override this to be notified when the user
        # changes the font.
        pass
