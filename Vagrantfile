
Vagrant.configure(2) do |config|

  # Ubuntu 16.04 LTS
  config.vm.define "devxenial" do |devxenial|
      devxenial.vm.box = "ubuntu/xenial64"
      devxenial.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    devxenial.vm.network :forwarded_port, guest: 80, host: 8080
    devxenial.vm.network :forwarded_port, guest: 5432, host: 5435
    devxenial.vm.network :private_network, ip: "192.168.35.2"
    devxenial.vm.synced_folder ".", "/opt/oasisqe/src"
    devxenial.vm.provision "devxenial", type: "shell", path: "src/build/provision_devxenial.sh"
  end

  # Ubuntu 18.04 LTS
  config.vm.define "devbionic" do |devbionic|
      devbionic.vm.box = "ubuntu/bionic64"
      devbionic.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    devbionic.vm.network :forwarded_port, guest: 80, host: 8088
    devbionic.vm.network :forwarded_port, guest: 5432, host: 5438
    devbionic.vm.network :private_network, ip: "192.168.35.8"
    devbionic.vm.synced_folder ".", "/opt/oasisqe/src"
    devbionic.vm.provision "devxenial", type: "shell", path: "src/build/provision_devbionic.sh"
  end

  # Debian 9.5 stable
  config.vm.define "devstretch" do |devstretch|
      devstretch.vm.box = "debian/contrib-stretch64" # contrib- has guest additions for synced_folder
      devstretch.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    devstretch.vm.network :forwarded_port, guest: 80, host: 8081
    devstretch.vm.network :forwarded_port, guest: 5432, host: 5436
    devstretch.vm.network :private_network, ip: "192.168.35.3"
    devstretch.vm.synced_folder ".", "/opt/oasisqe/src"
    devstretch.vm.provision "devstretch", type: "shell", path: "src/build/provision_devstretch.sh"
  end

  # fresh Ubuntu Xenial, install dependencies, install OASIS and config, ready to be packed
  # up for distribution
  config.vm.define "buildxenial" do |buildxenial|
      buildxenial.vm.box = "ubuntu/xenial64"
      buildxenial.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    buildxenial.vm.network :forwarded_port, guest: 80, host: 8082
    buildxenial.vm.network :forwarded_port, guest: 5432, host: 5437
    buildxenial.vm.network :private_network, ip: "192.168.35.4"
    buildxenial.vm.synced_folder ".", "/opt/oasisqe/src"
    buildxenial.vm.provision "buildxenial", type: "shell", path: "src/build/provision_buildxenial.sh"
  end

  config.vm.define "testxenial" do |testxenial|
    testxenial.vm.box = "ubuntu/xenial64"
    testxenial.vm.provider "libvirt" do |v|
      v.name = "testxenial"
      v.memory = 2024
      v.cpus = 2
    end
    testxenial.vm.network :forwarded_port, guest: 80, host: 8083
    testxenial.vm.network :forwarded_port, guest: 5432, host: 5438
    testxenial.vm.network :private_network, ip: "192.168.35.5"
    testxenial.vm.synced_folder ".", "/opt/oasisqe/src"
    testxenial.vm.provision "test", type: "shell", path: "src/build/provision_testxenial.sh"
  end

  config.vm.define "testbionic" do |testbionic|
    testbionic.vm.box = "ubuntu/bionic64"
    testbionic.vm.provider "libvirt" do |v|
      v.name = "testbionic"
      v.memory = 2024
      v.cpus = 2
    end
    testbionic.vm.network :forwarded_port, guest: 80, host: 8089
    testbionic.vm.network :forwarded_port, guest: 5432, host: 5439
    testbionic.vm.network :private_network, ip: "192.168.35.9"
    testbionic.vm.synced_folder ".", "/opt/oasisqe/src"
    testbionic.vm.provision "test", type: "shell", path: "src/build/provision_testbionic.sh"
  end

  config.vm.define "teststretch" do |teststretch|
    teststretch.vm.box = "debian/contrib-stretch64"
    teststretch.vm.provider "libvirt" do |v|
      v.name = "teststretch"
      v.memory = 2024
      v.cpus = 2
    end
    teststretch.vm.network :forwarded_port, guest: 80, host: 8090
    teststretch.vm.network :forwarded_port, guest: 5432, host: 5440
    teststretch.vm.network :private_network, ip: "192.168.35.10"
    teststretch.vm.synced_folder ".", "/opt/oasisqe/src"
    teststretch.vm.provision "test", type: "shell", path: "src/build/provision_teststretch.sh"
  end


end
