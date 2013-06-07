all: SourceMe.py
	cd gui && $(MAKE)

SourceMe.py: SourceMe.py.in
	sed -e "s,HERE,$(pwd)," < SourceMe.py.in > SourceMe.py
