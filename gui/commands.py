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
import gui.startup
import gui.source
import gui.logwindow
import gui.toplevel
import gui.dprintf
import gui.events
import gui.display
import re
from gui.startup import in_gtk_thread

class GuiCommand(gdb.Command):
    def __init__(self):
        super(GuiCommand, self).__init__('gui', gdb.COMMAND_SUPPORT,
                                         prefix = True)

class GuiSourceCommand(gdb.Command):
    """Create a new source window.
    Usage: gui source
    This creates a new source window in the GUI.  Any number of source
    windows can be created."""

    def __init__(self):
        super(GuiSourceCommand, self).__init__('gui source',
                                               gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        gui.source.SourceWindow()

class GuiLogWindowCommand(gdb.Command):
    """Create a new log window.
    Usage: gui log
    This creates a new "log" window in the GUI.  A log window is used
    to display output from "gui print", "gui printf", "gui output",
    and "gui dprintf".

    Multiple log windows can be created and output can be directed to
    a given instance using the "@" syntax, like:

        gui printf @5 "hello\n"
    """

    def __init__(self):
        super(GuiLogWindowCommand, self).__init__('gui log',
                                                  gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        window = gui.logwindow.LogWindow()
        print "Created log window %d; now the default" % window.number

class GuiPrintBase(gdb.Command):
    def __init__(self, command):
        super(GuiPrintBase, self).__init__('gui ' + command,
                                           gdb.COMMAND_SUPPORT)
        self.command = command

    # Given ARG, return a pair (WINDOW, NEW_ARG).
    def _parse_arg(self, arg, do_default = True):
        arg = arg.strip()
        match = re.match('@(\\d+)\\s+(.*)$', arg)
        if match is not None:
            winno = int(match.group(1))
            arg = match.group(2)
            window = gui.toplevel.state.get(winno)
            if window is None:
                raise gdb.GdbError('could not find window %d' % winno)
            if not isinstance(window, gui.logwindow.LogWindow):
                raise gdb.GdbError('window %d is not a log window' % winno)
        elif do_default:
            window = gui.logwindow.default_log_window
            if window is None:
                raise gdb.GdbError('no default log window')
        else:
            window = None
        return (window, arg)

    def invoke(self, arg, from_tty):
        (window, arg) = self._parse_arg(arg)
        text = gdb.execute(self.command + ' ' + arg, from_tty, True)
        window.append(text)

class GuiPrintCommand(GuiPrintBase):
    def __init__(self):
        super(GuiPrintCommand, self).__init__('print')

class GuiOutputCommand(GuiPrintBase):
    def __init__(self):
        super(GuiOutputCommand, self).__init__('output')

class GuiPrintfCommand(GuiPrintBase):
    def __init__(self):
        super(GuiPrintfCommand, self).__init__('printf')

class GuiDprintfCommand(GuiPrintBase):
    def __init__(self):
        super(GuiDprintfCommand, self).__init__('dprintf')

    def invoke(self, arg, from_tty):
        (window, arg) = self._parse_arg(arg, False)
        orig_arg = arg
        (ignore, arg) = gdb.decode_line(arg)
        if arg is None:
            raise gdb.GdbError("no printf arguments to 'gui dprintf'")
        arg = arg.strip()
        if not arg.startswith(','):
            raise gdb.GdbError("comma expected after linespec")
        arg = arg[1:]
        spec = arg[0 : -len(arg)]
        DPrintfBreakpoint(spec, window, arg)

class GuiDisplayCommand(gdb.Command):
    """FIXME"""

    def __init__(self):
        super(GuiDisplayCommand, self).__init__('gui display',
                                                gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        gui.display.DisplayWindow(arg)

    def complete(self, text, word):
        # FIXME, see
        # https://sourceware.org/bugzilla/show_bug.cgi?id=13077
        return None

class InfoWindowsCommand(gdb.Command):
    def __init__(self):
        super(InfoWindowsCommand, self).__init__('info windows',
                                                 gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        gui.toplevel.state.display()

class DeleteWindowsCommand(gdb.Command):
    def __init__(self):
        super(DeleteWindowsCommand, self).__init__('delete window',
                                                   gdb.COMMAND_SUPPORT)

    def invoke(self, arg, from_tty):
        self.dont_repeat()
        winno = int(arg)
        window = gui.toplevel.state.get(winno)
        if window is not None:
            window.destroy()

GuiCommand()
GuiSourceCommand()
GuiLogWindowCommand()
GuiPrintCommand()
GuiOutputCommand()
GuiPrintfCommand()
GuiDisplayCommand()
InfoWindowsCommand()
DeleteWindowsCommand()

_can_override = False

# A temporary test to see if you have a gdb that supports this.
class TestCommand(gdb.Command):
    """A temporary test command created for the GUI.
    This does nothing, the GUI startup code uses it to see if
    your copy of gdb has some command-overriding support."""

    def __init__(self, set_it):
        super(TestCommand, self).__init__('maint gui-test', gdb.COMMAND_DATA)
        self.set_it = set_it

    def invoke(self, arg, from_tty):
        if self.set_it:
            global _can_override
            _can_override = True
        else:
            try:
                super(TestCommand, self).invoke(arg, from_tty)
            except:
                pass

TestCommand(True)
TestCommand(False).invoke('', 0)

if _can_override:
    class Overrider(gdb.Command):
        def __init__(self, name, event):
            super(Overrider, self).__init__(name, gdb.COMMAND_DATA)
            self.event = event

        def invoke(self, arg, from_tty):
            super(Overrider, self).invoke(arg, from_tty)
            self.event.post()

    Overrider('up', gui.events.frame_changed)
    Overrider('down', gui.events.frame_changed)
    Overrider('frame', gui.events.frame_changed)
