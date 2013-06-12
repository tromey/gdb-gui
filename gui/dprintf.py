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

# dprintf-like machinery.

import gdb
import gui.logwindow

class DPrintfBreakpoint(gdb.Breakpoint):
    def __init__(self, spec, window, arg):
        super(DPrintfBreakpoint, self).__init__(spec, gdb.BP_BREAKPOINT)
        self.window = window
        self.command = 'printf ' + arg

    def stop(self):
        window = self.window
        if window is not None:
            if not window.valid():
                gdb.post_event(self.delete)
                return False
        else:
            window = gui.logwindow.default_log_window
        if window is None:
            return False

        try:
            text = gdb.execute(self.command, False, True)
        except something:
            text = something
        window.append(text)

        return False
