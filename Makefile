all: SourceMe.py gui/fix_signals.so
	@:

SourceMe.py: SourceMe.py.in
	sed -e "s,HERE,`pwd`," < SourceMe.py.in > SourceMe.py

gui/fix_signals.so: gui/fix-signals.c
	gcc -shared -fPIC -g -o gui/fix_signals.so gui/fix-signals.c `pkg-config --cflags python` `pkg-config --libs python`

clean:
	-rm SourceMe.py gui/fix_signals.so
