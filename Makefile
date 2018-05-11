VERSION=$(shell git describe --tags)


build-xenial:
	echo "Building ${VERSION} for Ubuntu Xenial"
	vagrant up buildxenial
	vagrant ssh buildxenial -c "mnt/src/build/build-xenial.sh /home/vagrant/mnt /home/vagrant/${VERSION}"
	vagrant ssh buildxenial -c "tar -zcvf mnt/${VERSION}-xenial.tgz ${VERSION}"
	rm -f oasis-xenial.tgz
	ln -s ${VERSION}-xenial.tgz oasisqe-xenial.tgz


test-xenial:
	echo "Testing on Ubuntu Xenial"
	vagrant up testxenial
	vagrant ssh testxenial


clean:
	vagrant destroy buildxenial
	vagrant destroy testxenial

