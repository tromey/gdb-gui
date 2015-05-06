## Overview

This is gdb-gui, a GUI for gdb.  This GUI differs from existing gdb
GUIs in a few ways:

* It runs in-process.

* It is written in Python.

* It is intended to interoperate well with the CLI.
  You can pick and choose which windows you want to see, and you can
  still do whatever you like in the terminal.

* It is totally incomplete.

## Installing

To get started, install the prerequisites.  You'll need a
Python-enabled gdb, PyGObject, and PyGktSourceView.  (And maybe more
-- if you trip across something, let me know.)  You'll need the Python
development package to compile the small C module that is included
here.

On Fedora I think this suffices:

```
sudo yum install gdb python-devel gtksourceview3 pygobject3
```

Now type `make` to build the needed shared library.

The simplest way to make the GUI always be available is to then use:

```
make hack-gdbinit
```

This will edit your `~/.gdbinit` to `source` the appropriate file.  If
you don't want to do this, you can just source the `gdb-gui.py` file
from gdb at any time.

## Using the GUI

This package adds a new `gui` command and various subcommands to gdb.
It also adds some new `set gui` parameters.

A simple command to try is `gui source`, which pops up a source
window.  The source window will automatically track your progress when
debugging.  You can make multiple source windows; they will be reused
in an LRU fashion.  You can set the theme, font, and title format of
source windows using the appropriate `set gui` commands.

## Hacking

If you want to hack on this, you will need Glade to edit the UI
elements.  For Fedora 18, you'll need a special hack to make the
gtksourceview widget visible to Glade.
