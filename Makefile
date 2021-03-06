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

testbionic:
	echo "Testing on Ubuntu Bionic"
	vagrant up testbionic

teststretch:
	echo "Testing on Ubuntu Stretch"
	vagrant up teststretch

testtrusty:
	echo "Testing on Ubuntu Trusty"
	vagrant up testtrusty

devxenial:
	echo "Building dev environment on Ubuntu Xenial"
	vagrant up devxenial
	vagrant ssh devxenial

devbionic:
	echo "Building dev environment on Ubuntu Bionic"
	vagrant up devbionic
	vagrant ssh devbionic

devstretch:
	echo "Building dev environment on Debian Stretch"
	vagrant up devstretch
	vagrant ssh devstretch

devtrusty:
	echo "Building dev environment on Ubuntu Trusty"
	vagrant up devtrusty
	vagrant ssh devtrusty

cleanvm:
	vagrant destroy buildxenial
	vagrant destroy testxenial
	vagrant destroy testbionic
	vagrant destroy testtrusty
	vagrant destroy teststretch
	vagrant destroy devxenial
	vagrant destroy devbionic
	vagrant destroy devstretch
	vagrant destroy devtrusty

