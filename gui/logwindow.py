# Copyright (C) 2013, 2015, 2023 Tom Tromey <tom@tromey.com>

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

# Log window.

import functools

import gui.startup
import gui.toplevel
from gui.startup import in_gtk_thread

default_log_window = None


class LogWindow(gui.toplevel.Toplevel):
    def __init__(self):
        global default_log_window
        if default_log_window is not None:
            default_log_window.default = ""
        default_log_window = self
        # For the window title.
        self.default = " [Default]"
        super(LogWindow, self).__init__("log")

    @in_gtk_thread
    def gtk_initialize(self):
        builder = gui.startup.create_builder("logwindow.xml")
        builder.connect_signals(self)

        self.window = builder.get_object("logwindow")
        self.view = builder.get_object("textview")
        self.view.modify_font(gui.params.font_manager.get_font())
        self.buffer = builder.get_object("buffer")

    # @in_gtk_thread
    # def set_font(self, font):
    #     self.view.modify_font(Pango.FontDescription(font_name))

    @in_gtk_thread
    def deleted(self, *args):
        global default_log_window
        if default_log_window == self:
            default_log_window = None
            for window in gui.toplevel.state.windows():
                if isinstance(window, LogWindow):
                    default_log_window = window
                    window.default = " [Default]"
                    window.update_title()
                    break

    def _append(self, text):
        self.buffer.insert_at_cursor(text)
        self.view.scroll_mark_onscreen(self.buffer.get_insert())

    def append(self, text):
        gui.startup.send_to_gtk(functools.partial(self._append, text))

    @in_gtk_thread
    def set_font(self, pango_font):
        self.view.modify_font(pango_font)
