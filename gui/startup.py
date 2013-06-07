# Copyright (C) 2012, 2013 Tom Tromey <tom@tromey.com>

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
import threading
import Queue

import fix_signals
fix_signals.save()

from gi.repository import Gtk, Gdk, GObject, GtkSource

import os

(read_pipe, write_pipe) = os.pipe()

_event_queue = Queue.Queue()

# Some kind of currying would be nice.
def send_to_gtk(func):
    _event_queue.put(func)
    os.write(write_pipe, 'x')

class _GtkThread(threading.Thread):
    def handle_queue(self, source, condition):
        global _event_queue
        os.read(source, 1)
        func = _event_queue.get()
        func()
        return True

    def run(self):
        global read_pipe
        GObject.io_add_watch(read_pipe, GObject.IO_IN, self.handle_queue)
        GObject.type_register(GtkSource.View)
        Gtk.main()

_t = None

def start_gtk():
    global _t
    if _t is None:
        GObject.threads_init()
        Gdk.threads_init()
        _t = _GtkThread()
        _t.setDaemon(True)
        _t.start()
        fix_signals.restore()
