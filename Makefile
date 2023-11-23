# This is passed to pkg-config to determine which python to use.  It
# has to match your gdb.
all: gdb-gui.py
	@:

gdb-gui.py: gdb-gui.py.in
	sed -e "s,HERE,`pwd`," < gdb-gui.py.in > gdb-gui.py

clean:
	-rm gdb-gui.py

hack-gdbinit: all
	if test -f $$HOME/.gdbinit && `grep -q gdb-gui $$HOME/.gdbinit`; then \
	  :; \
	else \
	  echo "source `pwd`/gdb-gui.py" >> $$HOME/.gdbinit; \
	fi
