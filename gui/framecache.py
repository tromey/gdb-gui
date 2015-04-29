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

_last_selected_frame = None

def check_frame():
    global _last_selected_frame
    sel = None
    try:
        sel = gdb.selected_frame()
    except:
        pass
    if _last_selected_frame is not sel:
        _last_selected_frame = sel
        gui.events.frame_changed.post()

# See my gdb branch on github.
if hasattr(gdb.events, 'before_prompt'):
    gdb.events.before_prompt.connect(check_frame)
