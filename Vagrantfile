
Vagrant.configure(2) do |config|

  config.vm.define "devxenial" do |devxenial|
      devxenial.vm.box = "ubuntu/xenial64"
      devxenial.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    devxenial.vm.network :forwarded_port, guest: 80, host: 8082
    devxenial.vm.network :forwarded_port, guest: 5432, host: 5436
    devxenial.vm.network :private_network, ip: "192.168.35.2"
    devxenial.vm.synced_folder ".", "/opt/oasisqe/src"
    devxenial.vm.provision "devxenial", type: "shell", path: "src/scripts/provision_oasisdev_xenial.sh"
  end

  config.vm.define "buildxenial" do |build|
    build.vm.box = "ubuntu/xenial64"
    build.vm.synced_folder ".", "/home/vagrant/mnt"
    build.vm.provider "libvirt" do |v|
      v.name = "buildxenial"
      v.memory = 2048
      v.cpus = 4
    end
    build.vm.provision "build", type: "shell", path: "src/scripts/provision_xenial.sh"
  end

  config.vm.define "testxenial" do |testxenial|
    testxenial.vm.box = "ubuntu/xenial64"
    testxenial.vm.provider "libvirt" do |v|
      v.name = "testxenial"
      v.memory = 2024
      v.cpus = 2
    end
    testxenial.vm.network :forwarded_port, guest: 80, host: 8083
    testxenial.vm.network :forwarded_port, guest: 5432, host: 5437
    testxenial.vm.network :private_network, ip: "192.168.35.5"
    testxenial.vm.synced_folder ".", "/home/vagrant/mnt"
    testxenial.vm.provision "test", type: "shell", path: "src/scripts/test_xenial.sh"
  end

end
