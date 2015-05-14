# Copyright (C) 2012, 2013, 2015 Tom Tromey <tom@tromey.com>

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
import gui.updatewindow
from gui.invoker import Invoker
import gui.startup
from gui.startup import in_gdb_thread, in_gtk_thread
import gui.toplevel
import gui.events
import os.path
import gui.gdbutil
import gui.params
import gui.bpcache

from gi.repository import Gtk, GtkSource, GObject, Gdk, GdkPixbuf, Pango

class BufferManager:
    def __init__(self):
        self.buffers = {}
        self.lang_manager = None
        gui.params.source_theme.set_buffer_manager(self)
        gui.events.location_changed.connect(self._location_changed)

    def release_buffer(self, buff):
        # FIXME: we should be smart about buffer caching.
        pass

    @in_gtk_thread
    def _set_marks(self, buffer, line_set):
        iter = buffer.get_iter_at_line(0)
        while True:
            line = iter.get_line() + 1
            if line in line_set:
                buffer.create_source_mark(None, 'executable', iter)
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

        if not self.lang_manager:
            self.lang_manager = GtkSource.LanguageManager.get_default()

        buff = GtkSource.Buffer()
        if filename:
            buff.set_language(self.lang_manager.guess_language(filename))
        buff.set_style_scheme(gui.params.source_theme.get_scheme())
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

    @in_gtk_thread
    def _do_change_theme(self):
        new_scheme = gui.params.source_theme.get_scheme()
        for filename in self.buffers:
            self.buffers[filename].set_style_scheme(new_scheme)

    @in_gdb_thread
    def change_theme(self):
        gui.startup.send_to_gtk(self._do_change_theme)

    @in_gtk_thread
    def update_breakpoint_location(self, sal, is_set):
        if is_set:
            category = 'breakpoint'
        else:
            category = 'executable'
        [fullname, line] = sal
        if fullname in self.buffers:
            buffer = self.buffers[fullname]
            iter = buffer.get_iter_at_line(line - 1)
            buffer.remove_source_marks(iter, iter)
            buffer.create_source_mark(None, category, iter)

    @in_gdb_thread
    def _location_changed(self, loc, is_set):
        gui.startup.send_to_gtk(lambda: self.update_breakpoint_location(loc,
                                                                        is_set))

buffer_manager = BufferManager()

# Return (FRAME, SYMTAB, FILE, LINE) for the selected frame, or, if
# there is no frame, for "main".
@in_gdb_thread
def get_current_location():
    try:
        frame = gdb.selected_frame()
        sal = frame.find_sal()
        symtab = sal.symtab
        if symtab is not None:
            filename = symtab.fullname()
        else:
            filename = None
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
        self.work_location = None

    # What a lame name.
    @in_gdb_thread
    def show_source_gdb(self, frame, symtab, srcfile, srcline):
        if len(self.windows) == 0:
            self.work_location = (frame, symtab, srcfile, srcline)
            SourceWindow()
        gui.startup.send_to_gtk(lambda: self.show_source(frame,
                                                         symtab,
                                                         srcfile,
                                                         srcline))

    @in_gdb_thread
    def new_source_window(self):
        self.work_location = get_current_location()
        SourceWindow()

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
        if self.work_location is not None:
            (frame, symtab, filename, lineno) = self.work_location
            self.work_location = None
            gui.startup.send_to_gtk(lambda: self.show_source(frame,
                                                             symtab,
                                                             filename,
                                                             lineno))

lru_handler = LRUHandler()

BUTTON_NAMES = ["step", "next", "continue", "finish", "stop", "up", "down"]

class SourceWindow(gui.updatewindow.UpdateWindow):
    def _get_pixmap(self, filename):
        path = os.path.join(gui.self_dir, filename)
        return GdkPixbuf.Pixbuf.new_from_file(path)

    def __init__(self):
        super(SourceWindow, self).__init__('source')
        gdb.events.cont.connect(self._on_cont_event)
        # Update the buttons.
        self.on_event()

    @in_gtk_thread
    def gtk_initialize(self):
        self.frame = None

        self.do_step = Invoker("step")
        self.do_next = Invoker("next")
        self.do_continue = Invoker("continue")
        self.do_finish = Invoker("finish")
        self.do_stop = Invoker("interrupt")
        self.do_up = Invoker("up")
        self.do_down = Invoker("down")

        builder = gui.startup.create_builder('sourcewindow.xml')
        builder.connect_signals(self)
        self.window = builder.get_object("sourcewindow")
        self.view = builder.get_object("view")

        # Maybe there is a cleaner way?
        self.buttons = {}
        for name in BUTTON_NAMES:
            self.buttons[name] = builder.get_object(name)

        self.view.modify_font(gui.params.font_manager.get_font())
        self.view.set_show_line_numbers(gui.params.line_numbers.value)
        self.view.set_tab_width(gui.params.tab_width.value)

        attrs = GtkSource.MarkAttributes()
        attrs.set_pixbuf(self._get_pixmap('icons/ok.png'))
        self.view.set_mark_attributes('executable', attrs, 0)

        attrs = GtkSource.MarkAttributes()
        attrs.set_pixbuf(self._get_pixmap('icons/breakpoint-marker.png'))
        self.view.set_mark_attributes('breakpoint', attrs, 1)

        lru_handler.add(self)

    @in_gtk_thread
    def _update_buttons(self, running):
        for button in BUTTON_NAMES:
            if button is "stop":
                self.buttons[button].set_sensitive(running)
            else:
                self.buttons[button].set_sensitive(not running)

    @in_gdb_thread
    def on_event(self):
        running = gui.gdbutil.is_running()
        gui.startup.send_to_gtk(lambda: self._update_buttons(running))

    @in_gdb_thread
    def _on_cont_event(self, event):
        self.on_event()

    @in_gdb_thread
    def _disconnect_cont_event(self):
        gdb.events.cont.disconnect(self._on_cont_event)

    def deleted(self, *args):
        lru_handler.remove(self)
        gdb.post_event(self._disconnect_cont_event)
        super(SourceWindow, self).deleted()

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
            self.fullname = srcfile
            self.basename = os.path.basename(srcfile)
            self.update_title()
            buffer_manager.release_buffer(old_buffer)
            GObject.idle_add(self._do_scroll, buff, srcline - 1)
            # self.view.scroll_to_iter(buff.get_iter_at_line(srcline), 0.0)

    @in_gtk_thread
    def set_font(self, pango_font):
        self.view.modify_font(pango_font)

    @in_gtk_thread
    def set_line_numbers(self, want_lines):
        self.view.set_show_line_numbers(want_lines)

    @in_gtk_thread
    def set_tab_width(self, width):
        self.view.set_tab_width(width)
