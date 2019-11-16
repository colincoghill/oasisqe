VERSION=$(shell git describe --tags)


buildbionic:
	echo "Building ${VERSION} for Ubuntu Bionic"
	vagrant up buildbionic
	vagrant ssh buildbionic -c "mnt/src/build/build-bionic.sh /home/vagrant/mnt /opt/oasisqe/3.9"
	vagrant ssh buildbionic -c "cd /opt/oasisqe; tar -zcvf /home/vagrant/mnt/${VERSION}-bionic.tgz 3.9"
	rm -f /home/vagrant/mnt/oasisqe-bionic.tgz
	ln -s /home/vagrant/mnt/${VERSION}-bionic.tgz /home/vagrant/mnt/oasisqe-bionic.tgz


testbionic:
	echo "Testing on Ubuntu Bionic"
	vagrant up testbionic

teststretch:
	echo "Testing on Ubuntu Stretch"
	vagrant up teststretch

devbionic:
	echo "Building dev environment on Ubuntu Bionic"
	vagrant up devbionic
	vagrant ssh devbionic

devstretch:
	echo "Building dev environment on Debian Stretch"
	vagrant up devstretch
	vagrant ssh devstretch

cleanvm:
	vagrant destroy buildbionic
	vagrant destroy testbionic
	vagrant destroy teststretch
	vagrant destroy devbionic
	vagrant destroy devstretch

