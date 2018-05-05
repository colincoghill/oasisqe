# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "ubuntu/xenial64"

  config.vm.synced_folder ".", "/opt/oasisqe/3.9"

  config.vm.define "devxenial" do |devxenial|
      config.vm.box = "ubuntu/xenial64"
      config.vm.provider "virtualbox" do |v|
      v.name = "devxenial"
      v.memory = 2048
      v.cpus = 2
    end
    config.vm.network :forwarded_port, guest: 80, host: 8082
    config.vm.network :forwarded_port, guest: 5432, host: 5436
    config.vm.network :private_network, ip: "192.168.35.4"
    config.vm.provision "devxenial", type: "shell", path: "src/scripts/provision_oasisdev_xenial.sh"
  end

  config.vm.define "build" do |build|
    config.vm.box = "ubuntu/xenial64"
    config.vm.provider "virtualbox" do |v|
      v.name = "oasisbuild"
      v.memory = 2048
      v.cpus = 4
    end
    config.vm.provision "build", type: "shell", path: "src/scripts/provision_oasisbuild_xenial.sh"
  end


  config.vm.define "testtrusty" do |test|
    config.vm.box = "ubuntu/trusty64"
    config.vm.provider "virtualbox" do |v|
      v.name = "oasistest"
      v.memory = 1024
      v.cpus = 2
    end
    config.vm.network :forwarded_port, guest: 80, host: 8083
    config.vm.network :forwarded_port, guest: 5432, host: 5437
    config.vm.network :private_network, ip: "192.168.35.2"
    config.vm.provision "test", type: "shell", path: "src/scripts/provision_oasistest_trusty.sh"
  end


end
