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

import gdb
from gui.startup import in_gdb_thread


class Invoker(object):
    """A simple class that can invoke a gdb command.
    This is suitable for use as an event handler in Gtk."""

    def __init__(self, cmd):
        self.cmd = cmd

    # This is invoked in the gdb thread to run the command.
    @in_gdb_thread
    def do_call(self):
        gdb.execute(self.cmd, from_tty=True, to_string=True)

    # The object itself is the Gtk event handler -- though really this
    # can be run in any thread.
    def __call__(self, *args):
        gdb.post_event(self.do_call)
