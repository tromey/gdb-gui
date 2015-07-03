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

# Parameters

import gdb
import gdb.prompt
import gui.startup
import gui.storage
import gui.toplevel

from gui.startup import in_gdb_thread, in_gtk_thread
from gi.repository import GtkSource, Pango

class _SetBase(gdb.Command):
    """Generic command for modifying GUI settings."""

    def __init__(self):
        super(_SetBase, self).__init__('set gui', gdb.COMMAND_NONE,
                                       prefix = True)

class _SetTitleBase(gdb.Command):
    """Generic command for modifying GUI window titles."""

    def __init__(self):
        super(_SetTitleBase, self).__init__('set gui title', gdb.COMMAND_NONE,
                                            prefix = True)

class _ShowBase(gdb.Command):
    """Generic command for showing GUI settings."""

    def __init__(self):
        super(_ShowBase, self).__init__('show gui', gdb.COMMAND_NONE,
                                        prefix = True)

class _ShowTitleBase(gdb.Command):
    """Generic command for showing GUI window titles."""

    def __init__(self):
        super(_ShowTitleBase, self).__init__('show gui title', gdb.COMMAND_NONE,
                                             prefix = True)

# Like gdb.Parameter, but has a default and automatically handles
# storage.
class _StoredParameter(gdb.Parameter):
    # NAME_FORMAT is like "%s" - NAME is substituted.
    # To construct the parameter name, "gui " is prefixed.
    def __init__(self, name_format, name, default, c_class, p_kind, *args):
        full_name = 'gui ' + name_format % name
        self.storage_name = '-'.join((name_format % name).split(' '))
        storage = gui.storage.storage_manager
        super(_StoredParameter, self).__init__(full_name, c_class, p_kind,
                                               *args)
        if p_kind is gdb.PARAM_BOOLEAN:
            val = storage.getboolean(self.storage_name)
        elif p_kind is gdb.PARAM_STRING or p_kind is gdb.PARAM_ENUM:
            val = storage.get(self.storage_name)
        elif p_kind is gdb.PARAM_ZINTEGER:
            val = storage.getint(self.storage_name)
        else:
            raise Error("missing case in gdb gui code")
        # Don't record the first setting.
        self.storage = None
        if val is None:
            val = default
        if val is not None:
            self.value = val
        # Start saving changes.
        self.storage = storage
        self.name = name

    @in_gdb_thread
    def get_set_string(self):
        if self.storage is not None:
            self.storage.set(self.storage_name, self.value)
        return ""

class _Theme(_StoredParameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set the source window theme."
    show_doc = "Show the source window theme."

    def __init__(self):
        self.manager = GtkSource.StyleSchemeManager.get_default()
        super(_Theme, self).__init__('%s', 'theme', None,
                                     gdb.COMMAND_NONE, gdb.PARAM_ENUM,
                                     # Probably the wrong thread.
                                     self.manager.get_scheme_ids())

    @in_gdb_thread
    def set_buffer_manager(self, b):
        self.buffer_manager = b

    @in_gtk_thread
    def get_scheme(self):
        # Sorta racy
        return self.manager.get_scheme(self.value)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The current theme is: " + self.value

    @in_gdb_thread
    def get_set_string(self):
        super(_Theme, self).get_set_string()
        self.buffer_manager.change_theme()
        return ""

class _Font(_StoredParameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set the source window font."
    show_doc = "Show the source window font."

    def __init__(self):
        self.manager = GtkSource.StyleSchemeManager.get_default()
        super(_Font, self).__init__('%s', 'font', 'monospace',
                                    gdb.COMMAND_NONE, gdb.PARAM_STRING)

    @in_gtk_thread
    def get_font(self):
        # Sorta racy
        return Pango.FontDescription(self.value)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The current font is: " + self.value

    @in_gdb_thread
    def get_set_string(self):
        gui.toplevel.state.set_font(self.value)
        super(_Font, self).get_set_string()
        return ""

title_params = {}

class _Title(_StoredParameter):
    # Silly gdb requirement.
    ""

    def __init__(self, name, default):
        title_params[name] = self
        self.name = name
        self.set_doc = "Set the %s window title format." % self.name
        self.show_doc = "Show the %s window title format." % self.name
        self.manager = GtkSource.StyleSchemeManager.get_default()
        super(_Title, self).__init__('title %s', name, default,
                                     gdb.COMMAND_NONE, gdb.PARAM_STRING)
        val = self.storage.get('title-%s' % name)
        if val is not None:
            self.value = val
        else:
            self.value = default

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The current title format for the %s is: %s" % (self.name,
                                                               self.value)

    @in_gdb_thread
    def get_set_string(self):
        super(_Title, self).get_set_string()
        gui.toplevel.state.update_titles()
        return ""

class _Missing(_StoredParameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set whether to mention missing gdb features."
    show_doc = "Show whether to mention missing gdb features."

    def __init__(self):
        super(_Missing, self).__init__('%s', 'mention-missing', True,
                                       gdb.COMMAND_NONE, gdb.PARAM_BOOLEAN)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        if self.value:
            v = "on"
        else:
            v = "off"
        return "Whether to warn about missing gdb features: " + v

class _Lines(_StoredParameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set whether to display line numbers in the source window."
    show_doc = "Show whether to display line numbers in the source window."

    def __init__(self):
        super(_Lines, self).__init__('%s', 'line-numbers', False,
                                     gdb.COMMAND_NONE, gdb.PARAM_BOOLEAN)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The current title format for the %s is: %s" % (self.name,
                                                               self.value)

    @in_gdb_thread
    def get_set_string(self):
        super(_Lines, self).get_set_string()
        gui.toplevel.state.set_line_numbers(self.value)
        return ""

class _Lines(_StoredParameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set whether to display line numbers in the source window."
    show_doc = "Show whether to display line numbers in the source window."

    def __init__(self):
        super(_Lines, self).__init__('%s', 'line-numbers', False,
                                     gdb.COMMAND_NONE, gdb.PARAM_BOOLEAN)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "Whether to display line numbers in the source window is: %s" % self.value

    @in_gdb_thread
    def get_set_string(self):
        super(_Lines, self).get_set_string()
        gui.toplevel.state.set_line_numbers(self.value)
        return ""

class _Tabs(_StoredParameter):
    # Silly gdb requirement.
    ""

    set_doc = "Set width of tabs in the source window."
    show_doc = "Show width of tabs in the source window."

    def __init__(self):
        super(_Tabs, self).__init__('%s', 'tab-width', 8,
                                    gdb.COMMAND_NONE, gdb.PARAM_ZINTEGER)

    @in_gdb_thread
    def get_show_string(self, pvalue):
        return "The tab width in the source window is: %d" % self.value

    @in_gdb_thread
    def get_set_string(self):
        super(_Tabs, self).get_set_string()
        gui.toplevel.state.set_tab_width(self.value)
        return ""


_SetBase()
_SetTitleBase()
_ShowBase()
_ShowTitleBase()
source_theme = _Theme()
font_manager = _Font()

_Title('source', '\\W{basename} [GDB Source @\\W{number}]')
_Title('display', '\\W{command} [GDB Display @\\W{number}]')
_Title('log', '[GDB Log @\\W{number}]\\W{default}')
_Title('stack', '[GDB Stack @\\W{number}]')

warn_missing = _Missing()
line_numbers = _Lines()
tab_width = _Tabs()
