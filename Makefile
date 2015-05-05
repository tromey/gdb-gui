all: gdb-gui.py gui/fix_signals.so
	@:

gdb-gui.py: gdb-gui.py.in
	sed -e "s,HERE,`pwd`," < gdb-gui.py.in > gdb-gui.py

gui/fix_signals.so: gui/fix-signals.c
	gcc -shared -fPIC -g -o gui/fix_signals.so gui/fix-signals.c `pkg-config --cflags python` `pkg-config --libs python`

clean:
	-rm gdb-gui.py gui/fix_signals.so

hack-gdbinit:
	if test -f $$HOME/.gdbinit && `grep -q gdb-gui $$HOME/.gdbinit`; then \
	  :; \
	else \
	  echo "source `pwd`/gdb-gui.py" >> $$HOME/.gdbinit; \
	fi
