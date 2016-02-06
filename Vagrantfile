# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "ubuntu/trusty64"
  config.vm.network :forwarded_port, guest: 80, host: 8080
  config.vm.network :forwarded_port, guest: 5432, host: 5434
  config.vm.network :private_network, ip: "192.168.35.2"
  # config.vm.network :public_network
  config.vm.synced_folder ".", "/opt/oasisqe/3.9"

  config.vm.define "dev" do |dev|
     config.vm.provision "dev", type: "shell", path: "deploy/dev/provision_oasisdev.sh"
  end

  config.vm.define "test" do |test|
     config.vm.provision "test", type: "shell", path: "deploy/dev/provision_oasistest.sh"
  end

  config.vm.provider "virtualbox" do |v|
    v.name = "oasisdev"
    v.memory = 1024
    v.cpus = 2
  end



end
