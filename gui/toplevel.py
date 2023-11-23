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

import threading

import gdb
from gi.repository import Pango

import gui.gdbutil
import gui.params
import gui.startup
import gui.storage
from gui.startup import in_gdb_thread, in_gtk_thread


class _ToplevelState(object):
    def __init__(self):
        gui.startup.start_gtk()
        # This lock must be held when using the other globals here.
        self.toplevel_lock = threading.Lock()
        self.next_toplevel = 1
        self.toplevels = {}
        self.byclass = {}

    def add(self, obj, window_type):
        with self.toplevel_lock:
            obj.number = self.next_toplevel
            self.next_toplevel = self.next_toplevel + 1
            self.toplevels[obj.number] = obj
            # Each window also has a window number specific to its
            # type.  Compute this here.
            if window_type not in self.toplevels:
                self.byclass[window_type] = []
            found = None
            for num in range(len(self.byclass[window_type])):
                if self.byclass[window_type][num] is None:
                    found = num
                    break
            if found is None:
                self.byclass[window_type].append(obj)
                found = len(self.byclass[window_type])
            else:
                self.byclass[found] = obj
            obj.type_number = found

    def remove(self, obj):
        with self.toplevel_lock:
            del self.toplevels[obj.number]
            self.byclass[obj.type_number] = None

    def get(self, winno):
        window = None
        with self.toplevel_lock:
            if winno in self.toplevels:
                window = self.toplevels[winno]
        return window

    def display(self):
        with self.toplevel_lock:
            if len(self.toplevels) == 0:
                print("No windows")
                return

            print(" Num    Name")
            for winno in range(1, self.next_toplevel):
                if winno in self.toplevels:
                    window = self.toplevels[winno]
                    print(" %3d    %s" % (window.number, window.window.get_title()))

    @in_gtk_thread
    def _do_set_font(self, font_name):
        pango_font = Pango.FontDescription(font_name)
        with self.toplevel_lock:
            for num in self.toplevels:
                self.toplevels[num].set_font(pango_font)

    @in_gdb_thread
    def set_font(self, font_name):
        gui.startup.send_to_gtk(lambda: self._do_set_font(font_name))

    @in_gtk_thread
    def _do_update_titles(self):
        with self.toplevel_lock:
            for num in self.toplevels:
                self.toplevels[num].update_title()

    @in_gdb_thread
    def update_titles(self):
        gui.startup.send_to_gtk(lambda: self._do_update_titles)

    @in_gtk_thread
    def _do_set_line_numbers(self, want_lines):
        with self.toplevel_lock:
            for num in self.toplevels:
                self.toplevels[num].set_line_numbers(want_lines)

    @in_gdb_thread
    def set_line_numbers(self, want_lines):
        gui.startup.send_to_gtk(lambda: self._do_set_line_numbers(want_lines))

    @in_gtk_thread
    def _do_set_tab_width(self, width):
        with self.toplevel_lock:
            for num in self.toplevels:
                self.toplevels[num].set_title(width)

    @in_gdb_thread
    def set_tab_width(self, width):
        gui.startup.send_to_gtk(lambda: self._do_set_tab_width(width))

    @in_gtk_thread
    def windows(self):
        return list(self.toplevels.values())


state = _ToplevelState()


class Toplevel(object):
    def __init__(self, window_type):
        state.add(self, window_type)
        # The subclass must set this.
        self.window = None
        self.window_type = window_type
        self.storage_name = window_type + "-" + str(self.type_number) + "-geom"
        gui.startup.send_to_gtk(self._do_gtk_initialize)

    @in_gtk_thread
    def gtk_initialize(self):
        """Subclasses should implement this method to do initialization
        in the Gtk thread."""
        pass

    @in_gtk_thread
    def _do_gtk_initialize(self):
        self.gtk_initialize()
        self.window.connect("configure-event", self._on_resize)
        geom = gui.storage.storage_manager.get(self.storage_name)
        if geom:
            self.window.parse_geometry(geom)
        self.update_title()
        self.window.show()

    @in_gdb_thread
    def _save_size(self, geom):
        gui.storage.storage_manager.set(self.storage_name, geom)

    @in_gtk_thread
    def _on_resize(self, widget, event):
        geom = "%dx%d+%d+%d" % (event.width, event.height, event.x, event.y)
        gdb.post_event(lambda: self._save_size(geom))
        return False

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

    @in_gtk_thread
    def update_title(self):
        fmt = gui.params.title_params[self.window_type].value
        title = gui.gdbutil.substitute_prompt_with_window(fmt, self)
        self.window.set_title(title)

    @in_gtk_thread
    def set_line_numbers(self, want_lines):
        pass

    @in_gtk_thread
    def set_tab_width(self, width):
        pass

    @in_gtk_thread
    def clear_source(self, buffer):
        pass
