# Copyright (C) 2015, 2023 Tom Tromey <tom@tromey.com>

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

# Little gdb utilities.

import gdb
import gdb.prompt

from gui.startup import in_gdb_thread

gui_prompt_substitutions = dict(gdb.prompt.prompt_substitutions)

_current_window_for_prompt = None


def _prompt_window(attr):
    if _current_window_for_prompt is None:
        return ""
    if attr is None:
        return ""
    if not hasattr(_current_window_for_prompt, attr):
        return None
    return str(getattr(_current_window_for_prompt, attr))


gui_prompt_substitutions["W"] = _prompt_window


# GDB's API should do this...
def substitute_prompt_with_window(prompt, window):
    global _current_window_for_prompt
    global gui_prompt_substitutions
    save = gdb.prompt.prompt_substitutions
    _current_window_for_prompt = window
    gdb.prompt.prompt_substitutions = gui_prompt_substitutions
    try:
        result = gdb.prompt.substitute_prompt(prompt)
    finally:
        gdb.prompt.prompt_substitutions = save
        _current_window_for_prompt = None
    return result


# GDB's API should do this...
def prompt_help_with_window(window):
    global _current_window_for_prompt
    global gui_prompt_substitutions
    save = gdb.prompt.prompt_substitutions
    _current_window_for_prompt = window
    gdb.prompt.prompt_substitutions = gui_prompt_substitutions
    try:
        result = gdb.prompt.prompt_help()
    finally:
        gdb.prompt.prompt_substitutions = save
        _current_window_for_prompt = None
    return result


@in_gdb_thread
def is_running():
    """Return True if the inferior is running."""
    # This seems good enough for now.
    # We can deal with scheduler locking and the rest later.
    if gdb.selected_thread() and gdb.selected_thread().is_running():
        return True
    return False
