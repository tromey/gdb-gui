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

# Source view.

import gdb
import gui.startup
import gtksourceview2 as gtksourceview
import gtk

class BufferManager:
    def __init__(self):
        self.buffers = {}

    def release_buffer(self, buff):
        # FIXME: we should be smart about buffer caching.
        pass

    def get_buffer(self, filename):
        if filename in self.buffers:
            return self.buffers[filename]

        buff = gtksourceview.Buffer()
        buff.begin_not_undoable_action()
        try:
            contents = open(filename).read()
        except:
            return None
        buff.set_text(contents)
        buff.end_not_undoable_action()
        buff.set_modified(False)

        self.buffers[filename] = buff
        return buff

buffer_manager = BufferManager()

# Return (FILE, LINE) for the selected frame, or, if there is no
# frame, for "main".  If there is no symbol file, return (None, None)
# instead.
def get_current_location():
    try:
        frame = gdb.selected_frame()
        sal = frame.find_sal()
        filename = sal.symtab.fullname()
        lineno = sal.line
    except gdb.error:
        # FIXME: should use the static location as set by list etc.
        # No frame - try 'main'.
        try:
            frame = None
            sym = gdb.lookup_global_symbol('main')
            lineno = sym.line
            filename = sym.symtab.fullname()
        except gdb.error:
            # Perhaps no symbol file.
            return (None, None, None)
        except AttributeError:
            return (None, None, None)
    return (frame, filename, lineno)

class LRUHandler:
    def __init__(self):
        self.windows = []

    #
    # These functions must run in the gdb thread.
    #

    def on_event(self, event):
        (frame, filename, lineno) = get_current_location()
        if filename is not None:
            gui.startup.send_to_gtk(lambda: self.show_source(frame,
                                                             filename,
                                                             lineno))

    def _connect_events(self):
        # FIXME - we need an event for "selected frame changed".
        # ... and thread-changed
        # really just pre-prompt would be good enough
        gdb.events.stop.connect(self.on_event)

    def _disconnect_events(self):
        gdb.events.stop.disconnect(self.on_event)

    #
    # These functions must run in the Gtk thread.
    #

    def pick_window(self, frame):
        # If a window is showing FRAME, use it.
        # Otherwise, if a window has no frame, use that.
        # Otherwise, use the first window.
        no_frame = None
        for w in self.windows:
            # Perhaps this is technically not ok.
            # We should document thread-safety a bit better.
            # Or just fix it up.
            if frame == w.frame:
                return w
            if w.frame is None and no_frame is None:
                no_frame = w
        if no_frame is not None:
            return no_frame
        return self.windows[0]

    def show_source(self, frame, srcfile, srcline):
        w = self.pick_window(frame)
        # LRU policy.
        self.windows.remove(w)
        self.windows.append(w)
        w.frame = frame
        w.show_source(srcfile, srcline)

    def remove(self, window):
        self.windows.remove(window)
        if len(self.windows) == 0:
            gui.startup.send_to_gtk(self._disconnect_events)

    def add(self, window):
        self.windows.insert(0, window)
        if len(self.windows) == 1:
            gui.startup.send_to_gtk(self._connect_events)
        # Show something.
        gui.startup.send_to_gtk(lambda: self.on_event(None))

lru_handler = LRUHandler()

class SourceWindow:
    def __init__(self):
        self.frame = None

        # FIXME: set the size
        # stuff in margins
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_border_width(0)
        self.window.set_title('GDB Source')

        vbox = gtk.VBox(0, False)
        swin = gtk.ScrolledWindow()
        self.view = gtksourceview.View()
        self.view.set_editable(False)
        self.view.set_cursor_visible(False)
        self.view.set_highlight_current_line(True)
        self.window.add(vbox)
        vbox.pack_start(swin, True, True, 0)
        swin.add(self.view)

        vbox.show_all()

        self.window.connect("delete-event", self.deleted)
        lru_handler.add(self)

        self.window.show()

    def deleted(self, widget, event):
        lru_handler.remove(self)

    def _do_scroll(self, buff, srcline):
        buff.place_cursor(buff.get_iter_at_line(srcline))
        self.view.scroll_mark_onscreen(buff.get_insert())
        return False

    def show_source(self, srcfile, srcline):
        buff = buffer_manager.get_buffer(srcfile)
        if buff is not None:
            old_buffer = self.view.get_buffer()
            self.view.set_buffer(buff)
            buffer_manager.release_buffer(old_buffer)
            gtk.idle_add(self._do_scroll, buff, srcline - 1)
            # self.view.scroll_to_iter(buff.get_iter_at_line(srcline), 0.0)
