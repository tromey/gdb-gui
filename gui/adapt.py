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

# Adapt to gdb issues.

import gdb
import gui.params

bugs = {
    13351: """Your gdb can't look up a symbol when the inferior is not running.
This means that you can only view global symbols until you've started
the inferior.""",

    15620: """Your gdb doesn't have a "new breakpoint" event.
This means that the source windows will not show you where
breakpoints have been set.""",

    13598: """Your gdb doesn't have a "before prompt" event.
This means that various windows won't be able to react to
commands like "up" or "down".""",

    18385: """Your gdb doesn't expose locations on a gdb.Breakpoint.
This can be worked around, but maybe not always reliably.
This means that sometimes breakpoints won't display in source windows."""
}

_warning = """See https://sourceware.org/bugzilla/show_bug.cgi?id=%s
for more information."""

_first_report = True

def notify_bug(bugno):
    if not gui.params.warn_missing.value:
        return
    if not (bugno in bugs):
        return
    print "################"
    print bugs[bugno]
    print _warning % bugno
    print ""
    print "You can use 'set gui mention-missing off' to disable this message."
    print "################"
    del bugs[bugno]
