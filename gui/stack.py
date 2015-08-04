# Copyright (C) 2015 Tom Tromey <tom@tromey.com>

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

# Stack view.

import gdb
import gdb.frames
import gdb.FrameDecorator
import gdb.FrameIterator
import gui.updatewindow
import gui.startup
import gui.params

from gui.framecache import FrameCommandInvoker
from gui.startup import in_gdb_thread, in_gtk_thread
from gi.repository import Gtk

def format_frame(frame):
    result = {}
    result["name"] = frame.function()
    result["filename"] = frame.filename()
    result["pc"] = frame.address()
    result["line"] = frame.line()
    elided = frame.elided()
    if elided is not None:
        elided = list(map(format_frame, elided))
    result["elided"] = elided
    # Not quite what we want...
    result["solib"] = gdb.solib_name(frame.address())
    return result
    # FIXME args

class StackWindow(gui.updatewindow.UpdateWindow):
    def __init__(self):
        self.raw = False
        super(StackWindow, self).__init__('stack')
        # Connect events.
        # Update buttons.

    @in_gtk_thread
    def gtk_initialize(self):
        self.do_up = FrameCommandInvoker("up")
        self.do_down = FrameCommandInvoker("down")
        builder = gui.startup.create_builder('stackwindow.xml')
        builder.connect_signals(self)

        self.window = builder.get_object('stackwindow')
        self.view = builder.get_object('view')
        self.text = Gtk.TextBuffer()
        self.view.set_buffer(self.text)
        self.view.modify_font(gui.params.font_manager.get_font())

    @in_gtk_thread
    def _update(self, data):
        self.text.delete(self.text.get_start_iter(), self.text.get_end_iter())
        frame_no = 1
        for frame in data:
            self.text.insert_at_cursor('#%d ' % frame_no)
            frame_no = frame_no + 1
            # Goofball API.
            if isinstance(frame["name"], str):
                self.text.insert_at_cursor(frame["name"])
            else:
                # This is lame but we have no access to minimal
                # symbols.
                self.text.insert_at_cursor("???")
            self.text.insert_at_cursor(" ")
            # FIXME args
            self.text.insert_at_cursor("\n")
            if frame["line"] is not None:
                self.text.insert_at_cursor("  at %s:%d\n" % (frame["filename"],
                                                             frame["line"]))
            if frame["solib"] is not None:
                self.text.insert_at_cursor("  [%s]\n" % frame["solib"])

    @in_gdb_thread
    def on_event(self):
        frame_iter = None
        start_frame = gdb.newest_frame()
        if not self.raw:
            frame_iter = gdb.frames.execute_frame_filters(start_frame, 0, -1)
        if frame_iter is None:
            frame_iter = map(gdb.FrameDecorator.FrameDecorator,
                             gdb.FrameIterator.FrameIterator(start_frame))
        data = list(map(format_frame, frame_iter))
        gui.startup.send_to_gtk(lambda: self._update(data))

    @in_gtk_thread
    def set_font(self, pango_font):
        self.view.modify_font(pango_font)

def show_stack():
    # for now
    StackWindow()
