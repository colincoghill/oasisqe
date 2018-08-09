VERSION=$(shell git describe --tags)


buildxenial:
	echo "Building ${VERSION} for Ubuntu Xenial"
	vagrant up buildxenial
	vagrant ssh buildxenial -c "mnt/src/build/build-xenial.sh /home/vagrant/mnt /opt/oasisqe/3.9"
	vagrant ssh buildxenial -c "cd /opt/oasisqe; tar -zcvf /home/vagrant/mnt/${VERSION}-xenial.tgz 3.9"
	rm -f /home/vagrant/mnt/oasisqe-xenial.tgz
	ln -s /home/vagrant/mnt/${VERSION}-xenial.tgz /home/vagrant/mnt/oasisqe-xenial.tgz


testxenial:
	echo "Testing on Ubuntu Xenial"
	vagrant up testxenial
	vagrant ssh testxenial

devxenial:
	echo "Building dev environment on Ubuntu Xenial"
	vagrant up devxenial
	vagrant ssh devxenial

devstretch:
	echo "Building dev environment on Debian Stretch"
	vagrant up devstretch
	vagrant ssh devstretch

clean:
	vagrant destroy buildxenial
	vagrant destroy testxenial
	vagrant destroy devxenial
	vagrant destroy devstretch

