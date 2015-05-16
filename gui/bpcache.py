# Copyright (C) 2015 Tom Tromey <tom@trolley.com>

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
import gui.events
import gui.adapt

# This maps from (FILENAME,LINE) to a set of breakpoints referencing
# that file/line.  Then we emit events when entries are created or
# destroyed.
_breakpoint_source_map = {}

def _breakpoint_created(bp):
    if bp.location is None:
        return
    gui.adapt.notify_bug(18385)
    (rest, locs) = gdb.decode_line(bp.location)
    if rest is not None:
        # Let's assume we couldn't reparse for some reason.
        return
    for sal in locs:
        if sal.symtab is None:
            continue
        entry = (sal.symtab.fullname(), sal.line)
        if entry not in _breakpoint_source_map:
            _breakpoint_source_map[entry] = set()
        if bp.number not in _breakpoint_source_map[entry]:
            _breakpoint_source_map[entry].add(bp.number)
            gui.events.location_changed.post(entry, True)
        else:
            _breakpoint_source_map[entry].add(bp.number)

def _breakpoint_deleted(bp):
    num = bp.number
    for entry in _breakpoint_source_map:
        if num in _breakpoint_source_map[entry]:
            _breakpoint_source_map[entry].discard(bp.number)
            if len(_breakpoint_source_map[entry]) == 0:
                gui.events.location_changed.post(entry, False)

def any_breakpoint_at(filename, lineno):
    entry = (filename, lineno)
    if entry not in _breakpoint_source_map:
        return False
    return len(_breakpoint_source_map[entry]) > 0

if not hasattr(gdb.events, 'breakpoint_created'):
    gui.adapt.notify_bug(15620)
else:
    gdb.events.breakpoint_created.connect(_breakpoint_created)
    gdb.events.breakpoint_deleted.connect(_breakpoint_deleted)
