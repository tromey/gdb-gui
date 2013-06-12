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

# Toplevel handling.

import gdb
import gui.startup
import threading

class _ToplevelState(object):
    def __init__(self):
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

_toplevel_state = _ToplevelState()

class Toplevel(object):
    def __init__(self):
        _toplevel_state.add(self)
        # The subclass must set this.
        self.window = None

    def destroy(self):
        _toplevel_state.remove(self)
        gui.startup.send_to_gtk(self.window.destroy)

class InfoWindowsCommand(gdb.Command):
    def __init__(self):
        super(InfoWindowsCommand, self).__init__('info windows',
                                                 gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        _toplevel_state.display()

class DeleteWindowsCommand(gdb.Command):
    def __init__(self):
        super(DeleteWindowsCommand, self).__init__('delete window',
                                                   gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        winno = int(arg)
        window = _toplevel_state.get(winno)
        if window is not None:
            window.destroy()

InfoWindowsCommand()
DeleteWindowsCommand()
