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

# Storage management.

from gi.repository import GLib
import os
import errno
import ConfigParser
import atexit

class StorageManager:
    def __init__(self):
        self.dir = os.path.join(GLib.get_user_config_dir(), 'gdb')
        self.file = os.path.join(self.dir, 'settings')
        try:
            os.mkdir(self.dir, 0700)
        except OSError as exc:
            if exc.errno is not errno.EEXIST:
                self.file = None
        self.config = ConfigParser.RawConfigParser()
        if self.file is not None:
            self.config.read(self.file)
        if not self.config.has_section('general'):
            self.config.add_section('general')
        atexit.register(self.write)

    def get(self, name):
        if self.config.has_option('general', name):
            return self.config.get('general', name)
        return None

    def set(self, name, value):
        self.config.set('general', name, value)

    def write(self):
        with open(self.file, 'wb') as save_file:
            self.config.write(save_file)

storage_manager = StorageManager()
