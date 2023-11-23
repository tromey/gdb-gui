# Copyright (C) 2015, 2023 Tom Tromey <tom@tromey.com>

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

# Notifications

import time

import gdb
from gi.repository import Notify

import gui.params
import gui.startup
from gui.startup import in_gdb_thread, in_gtk_thread

_initialized = False

_last_time = None


@in_gtk_thread
def _show_notification(title, content):
    global _initialized
    if not _initialized:
        _initialized = True
        Notify.init("gdb")
    n = Notify.Notification.new(title, content)
    n.show()


@in_gdb_thread
def _on_stop(event):
    global _last_time
    t = _last_time
    _last_time = None

    if (
        t is None
        or not gui.params.stop_notification.value
        or time.process_time() - t < gui.params.stop_notification_seconds.value
    ):
        return

    if isinstance(event, gdb.ExitedEvent):
        title = "gdb - inferior exited"
        if hasattr(event, "exit_code"):
            content = "inferior exited with code " + str(event.exit_code)
        else:
            content = "inferior exited, code unavailable"
    elif isinstance(event, gdb.BreakpointEvent):
        title = "gdb - inferior stopped"
        content = "inferior stopped at breakpoint " + str(event.breakpoints[0].number)
    elif isinstance(event, gdb.SignalEvent):
        title = "gdb - inferior stopped"
        content = "inferior stopped with signal: " + event.stop_signal
    else:
        title = "gdb - inferior stopped"
        content = "inferior stopped, reason unknown"

    gui.startup.send_to_gtk(lambda: _show_notification(title, content))


@in_gdb_thread
def _on_cont(event):
    global _last_time
    _last_time = time.process_time()


gdb.events.stop.connect(_on_stop)
gdb.events.cont.connect(_on_cont)
gdb.events.exited.connect(_on_stop)
