
Vagrant.configure(2) do |config|


  # fresh Ubuntu Bionic, install dependencies, install OASIS and config, ready to be packed
  # up for distribution
  config.vm.define "buildbionic" do |buildbionic|
      buildbionic.vm.box = "ubuntu/bionic64"
      buildbionic.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    buildbionic.vm.network :forwarded_port, guest: 80, host: 8084
    buildbionic.vm.network :forwarded_port, guest: 5432, host: 5444
    buildbionic.vm.network :private_network, ip: "192.168.35.14"
    buildbionic.vm.synced_folder ".", "/opt/oasisqe/src"
    buildbionic.vm.provision "buildbionic", type: "shell", path: "src/build/provision_buildbionic.sh"
  end

  # Ubuntu 18.04 LTS
  config.vm.define "devbionic" do |devbionic|
      devbionic.vm.box = "ubuntu/bionic64"
      devbionic.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    devbionic.vm.network :forwarded_port, guest: 80, host: 8082
    devbionic.vm.network :forwarded_port, guest: 5432, host: 5442
    devbionic.vm.network :private_network, ip: "192.168.35.12"
    devbionic.vm.synced_folder ".", "/opt/oasisqe/src"
    devbionic.vm.provision "devbionic", type: "shell", path: "src/build/provision_devbionic.sh"
  end

  # Debian 9.5 stable
  config.vm.define "devstretch" do |devstretch|
      devstretch.vm.box = "debian/contrib-stretch64" # contrib- has guest additions for synced_folder
      devstretch.vm.provider "libvirt" do |v|
      v.name = "dev"
      v.memory = 2048
      v.cpus = 2
    end
    devstretch.vm.network :forwarded_port, guest: 80, host: 8083
    devstretch.vm.network :forwarded_port, guest: 5432, host: 5443
    devstretch.vm.network :private_network, ip: "192.168.35.13"
    devstretch.vm.synced_folder ".", "/opt/oasisqe/src"
    devstretch.vm.provision "devstretch", type: "shell", path: "src/build/provision_devstretch.sh"
  end

  config.vm.define "testbionic" do |testbionic|
    testbionic.vm.box = "ubuntu/bionic64"
    testbionic.vm.provider "libvirt" do |v|
      v.name = "testbionic"
      v.memory = 2024
      v.cpus = 2
    end
    testbionic.vm.network :forwarded_port, guest: 80, host: 8086
    testbionic.vm.network :forwarded_port, guest: 5432, host: 5446
    testbionic.vm.network :private_network, ip: "192.168.35.16"
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
    teststretch.vm.network :forwarded_port, guest: 80, host: 8087
    teststretch.vm.network :forwarded_port, guest: 5432, host: 5447
    teststretch.vm.network :private_network, ip: "192.168.35.17"
    teststretch.vm.synced_folder ".", "/opt/oasisqe/src"
    teststretch.vm.provision "test", type: "shell", path: "src/build/provision_teststretch.sh"
  end

end
