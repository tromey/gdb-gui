# Copyright (C) 2012, 2013, 2015, 2023 Tom Tromey <tom@tromey.com>

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
import queue
import os
import os.path
import gui

from . import fix_signals
fix_signals.save()

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, Gdk, GObject, GtkSource, GLib, GdkPixbuf

(read_pipe, write_pipe) = os.pipe()

_event_queue = queue.Queue()

def send_to_gtk(func):
    _event_queue.put(func)
    # The payload is arbitrary.
    os.write(write_pipe, bytes(1))

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

_gdb_thread = threading.current_thread()
_t = None

def start_gtk():
    global _t
    if _t is None:
        GLib.set_application_name('GDB')
        GLib.set_prgname('GDB')
        Gdk.set_program_class('GDB')
        Gtk.Window.set_default_icon_name('GDB')
        path = os.path.join(gui.self_dir, 'icons/face-raspberry-symbolic.svg')
        Gtk.Window.set_default_icon(GdkPixbuf.Pixbuf.new_from_file(path))
        GObject.threads_init()
        Gdk.threads_init()
        _t = _GtkThread()
        _t.setDaemon(True)
        _t.start()
        fix_signals.restore()

def create_builder(filename):
    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(gui.self_dir, filename))
    return builder

def in_gdb_thread(func):
    def ensure_gdb_thread(*args, **kwargs):
        if threading.current_thread() is not _gdb_thread:
            raise RuntimeError("must run '%s' in gdb thread" % repr(func))
        return func(*args, **kwargs)
    return ensure_gdb_thread

def in_gtk_thread(func):
    def ensure_gtk_thread(*args, **kwargs):
        if threading.current_thread() is not _t:
            raise RuntimeError("must run '%s' in Gtk thread" % repr(func))
        return func(*args, **kwargs)
    return ensure_gtk_thread
