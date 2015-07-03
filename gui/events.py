# Copyright (C) 2013, 2015 Tom Tromey <tom@tromey.com>

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

class _Event(object):
    def __init__(self):
        self.funcs = []

    def connect(self, callback):
        self.funcs.append(callback)

    def disconnect(self, callback):
        self.funcs.remove(callback)

    def post(self, *args, **kwargs):
        for fun in self.funcs:
            fun(*args, **kwargs)

frame_changed = _Event()
location_changed = _Event()
