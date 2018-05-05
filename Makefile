SRC=/opt/oasisqe/3.9
VERSION=$(shell git describe --tags)

build:  src/Pipfile.lock
	echo "Building " ${VERSION}
	mkdir -p build
	cp src/build.sh build
	cd build; sh build.sh ${SRC}
	tar -zcvf ${VERSION}.tgz build
	

clean:  build
	rm -r build
