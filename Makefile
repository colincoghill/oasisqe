SRC=/opt/oasisqe/3.9

build:  src/Pipfile.lock
	mkdir -p build
	cp src/build.sh build
	cd build; sh build.sh ${SRC}

clean:  build
	rm -r build
