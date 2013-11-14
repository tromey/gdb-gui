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
import gui
from gui.invoker import Invoker
from gui.toplevel import Toplevel
import gui.startup
from gui.startup import in_gdb_thread, in_gtk_thread
import gui.toplevel
import gui.events
import os.path

from gi.repository import Gtk, GtkSource, GObject, Gdk, GdkPixbuf

class BufferManager:
    def __init__(self):
        self.buffers = {}

    def release_buffer(self, buff):
        # FIXME: we should be smart about buffer caching.
        pass

    @in_gtk_thread
    def _set_marks(self, buffer, line_set):
        iter = buffer.get_iter_at_line(0)
        while True:
            if iter.get_line() + 1 in line_set:
                mark = buffer.create_source_mark(None, 'executable', iter)
            if not iter.forward_line():
                break

    @in_gdb_thread
    def _get_lines_update(self, buffer, symtab):
        if hasattr(symtab, 'linetable'):
            line_set = set(symtab.linetable().source_lines())
            gui.startup.send_to_gtk(lambda: self._set_marks(buffer, line_set))

    @in_gtk_thread
    def get_buffer(self, symtab, filename):
        if filename in self.buffers:
            return self.buffers[filename]

        buff = GtkSource.Buffer()
        buff.begin_not_undoable_action()
        try:
            contents = open(filename).read()
        except:
            return None
        buff.set_text(contents)
        buff.end_not_undoable_action()
        buff.set_modified(False)
        buff.filename = filename

        if symtab is not None:
            gdb.post_event(lambda: self._get_lines_update(buff, symtab))

        self.buffers[filename] = buff
        return buff

buffer_manager = BufferManager()

# Return (FRAME, SYMTAB, FILE, LINE) for the selected frame, or, if
# there is no frame, for "main".
@in_gdb_thread
def get_current_location():
    try:
        frame = gdb.selected_frame()
        sal = frame.find_sal()
        symtab = sal.symtab
        filename = symtab.fullname()
        lineno = sal.line
    except gdb.error:
        # FIXME: should use the static location as set by list etc.
        # No frame - try 'main'.
        try:
            frame = None
            sym = gdb.lookup_global_symbol('main')
            lineno = sym.line
            symtab = sym.symtab
            filename = symtab.fullname()
        except gdb.error:
            # Perhaps no symbol file.
            return (None, None, None, None)
        except AttributeError:
            return (None, None, None, None)
    return (frame, symtab, filename, lineno)

class LRUHandler:
    def __init__(self):
        self.windows = []

    @in_gdb_thread
    def on_event(self, *args):
        (frame, symtab, filename, lineno) = get_current_location()
        if filename is not None:
            gui.startup.send_to_gtk(lambda: self.show_source(frame,
                                                             symtab,
                                                             filename,
                                                             lineno))

    @in_gdb_thread
    def _connect_events(self):
        # FIXME - we need an event for "selected frame changed".
        # ... and thread-changed
        # really just pre-prompt would be good enough
        gdb.events.stop.connect(self.on_event)
        gui.events.frame_changed.connect(self.on_event)

    @in_gdb_thread
    def _disconnect_events(self):
        gdb.events.stop.disconnect(self.on_event)
        gui.event.frame_changed.disconnect(self.on_event)

    @in_gtk_thread
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

    @in_gtk_thread
    def show_source(self, frame, symtab, srcfile, srcline):
        w = self.pick_window(frame)
        # LRU policy.
        self.windows.remove(w)
        self.windows.append(w)
        w.frame = frame
        w.show_source(symtab, srcfile, srcline)

    @in_gtk_thread
    def remove(self, window):
        self.windows.remove(window)
        if len(self.windows) == 0:
            gdb.post_event(self._disconnect_events)

    @in_gtk_thread
    def add(self, window):
        self.windows.insert(0, window)
        if len(self.windows) == 1:
            gdb.post_event(self._connect_events)
        # Show something.
        gdb.post_event(lambda: self.on_event(None))

lru_handler = LRUHandler()

class SourceWindow(Toplevel):
    def _get_pixmap(self, filename):
        path = os.path.join(gui.self_dir, filename)
        return GdkPixbuf.Pixbuf.new_from_file(path)

    def __init__(self):
        super(SourceWindow, self).__init__()

        self.frame = None

        self.do_step = Invoker("step")
        self.do_next = Invoker("next")
        self.do_continue = Invoker("continue")
        self.do_finish = Invoker("finish")
        self.do_stop = Invoker("interrupt")

        builder = gui.startup.create_builder('sourcewindow.xml')
        builder.connect_signals(self)
        self.window = builder.get_object("sourcewindow")
        self.view = builder.get_object("view")

        attrs = GtkSource.MarkAttributes()
        # FIXME: really we want a little green dot...
        attrs.set_pixbuf(self._get_pixmap('icons/countpoint-marker.png'))
        self.view.set_mark_attributes('executable', attrs, 0)

        attrs = GtkSource.MarkAttributes()
        attrs.set_pixbuf(self._get_pixmap('icons/breakpoint-marker.png'))
        self.view.set_mark_attributes('breakpoint', attrs, 1)

        lru_handler.add(self)

        self.window.show()

    def deleted(self, widget, event):
        lru_handler.remove(self)

    def line_mark_activated(self, view, textiter, event):
        if event.type != Gdk.EventType.BUTTON_PRESS:
            return
        if event.button.get_button()[1] != 1:
            return
        fun = Invoker("break %s:%d" % (self.view.get_buffer().filename,
                                       textiter.get_line() + 1))
        fun()

    def _do_scroll(self, buff, srcline):
        buff.place_cursor(buff.get_iter_at_line(srcline))
        self.view.scroll_mark_onscreen(buff.get_insert())
        return False

    def show_source(self, symtab, srcfile, srcline):
        buff = buffer_manager.get_buffer(symtab, srcfile)
        if buff is not None:
            old_buffer = self.view.get_buffer()
            self.view.set_buffer(buff)
            buffer_manager.release_buffer(old_buffer)
            GObject.idle_add(self._do_scroll, buff, srcline - 1)
            # self.view.scroll_to_iter(buff.get_iter_at_line(srcline), 0.0)
