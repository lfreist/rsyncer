NAME = PyRsync

.PHONY = all build install uninstall clean

all: build install clean

build:
	python3 setup.py sdist bdist_wheel

install:
	python3 -m pip install ../$(NAME)

uninstall:
	python3 -m pip uninstall $(NAME) -y

clean:
	rm -r build
	rm -r $(NAME).egg-info