# Installation Guide

> ref https://docs.openstack.org/install-guide

Ubuntu was chosen as host OS.

[TOC]



## Security

> ref: https://docs.openstack.org/install-guide/environment-security.html


```
$ openssl rand -hex 10
```

## Host networking

> ref: https://docs.openstack.org/install-guide/environment-networking.html

> ref: https://help.ubuntu.com/lts/serverguide/network-configuration.html


The example architectures assume use of the following networks:

- Management on 10.0.0.0/24 with gateway 10.0.0.1

  This network requires a gateway to provide Internet access to all nodes for administrative purposes such as package installation, security updates, DNS, and NTP.

- Provider on 203.0.113.0/24 with gateway 203.0.113.1

  This network requires a gateway to provide Internet access to instances in your OpenStack environment.

### My network solution



```
Net0:
	Network name: VirtualBox  host-only Ethernet Adapter
	Purpose: administrator / management network
	IP block: 10.20.0.0/24
	DHCP: disable
	Linux device: eth0

Net1:
	Network name: VirtualBox  host-only Ethernet Adapter#2
	Purpose: Provider network
	DHCP: disable
	IP block: 172.16.0.0/24
	Linux device: eth1

Net2：
	Network name: VirtualBox  host-only Ethernet Adapter#3
	Purpose: Storage network
	DHCP: disable
	IP block: 192.168.199.0/24
	Linux device: eth2

Net3：
	Network name: VirtualBox  Bridged
	Purpose: Internet
	DHCP: enable
	IP block: 192.168.199.0/24
	Linux device: eth3
```





Edit the `/etc/network/interfaces` file to contain the following:

Replace `INTERFACE_NAME` with the actual interface name. For example, *eth1* or *ens224*.

```bash
# The provider network interface
auto INTERFACE_NAME
iface INTERFACE_NAME inet manual
up ip link set dev $IFACE up
down ip link set dev $IFACE down
```



## Base Machine 

- download image from https://launchpad.net/ubuntu/+mirror/mirrors.neusoft.edu.cn-release


- Change root password

  ```
  $ sudo su
  # passwd
  ```

  ​

- Allow root ssh with password

  ``` 
  # vi /etc/ssh/sshd_config 

  PermitRootLogin yes
  ```

- Check nic names

  ``` 
  root@ubuntu:~# dmesg | grep rename
  [    2.799294] e1000 0000:00:09.0 enp0s9: renamed from eth2
  [    2.800192] e1000 0000:00:0a.0 enp0s10: renamed from eth3
  [    2.801072] e1000 0000:00:08.0 enp0s8: renamed from eth1
  [    2.804067] e1000 0000:00:03.0 enp0s3: renamed from eth0
  ```

- configure management network as a dummy one

  ```
  # vi /etc/network/interfaces
  auto enp0s3
  iface enp0s3 inet static
  address 10.20.0.11
  netmask 255.255.255.0
  gateway 10.20.0.1
  ```

- NTP

  - install chrony

    ```
    install chrony
    ```

  - Edit the `/etc/chrony/chrony.conf` file and add, change, or remove these keys as necessary for your environment:

    ```
    allow 10.20.0.0/24
    ```

  - restart service

    ```
    # service chrony restart
    ```

- Install OpenStack packages

  > ref : https://docs.openstack.org/install-guide/environment-packages.html

  Enable the OpenStack repository

  ```
  # apt install software-properties-common
  # add-apt-repository cloud-archive:ocata
  ```

  Upgrade the packages on all nodes:

  > Set apt proxy before doing that will help save your life
  >
  > ```
  > # vi /etc/apt/apt.conf.d/90proxy
  > Acquire::http::Proxy "http://www-proxy.exu.ericsson.se:8080";
  > Acquire::https::Proxy "http://www-proxy.exu.ericsson.se:8080";
  > ```

  ```
  # apt update && apt dist-upgrade -y
  ```

  Install the OpenStack client:

  ```
  # apt install python-openstackclient -y
  ```

  ​

  ​

## Controller actions

### management network eth0 (enp0s3)

```
# vi /etc/network/interfaces

auto enp0s3
iface enp0s3 inet static
address 10.20.0.10
netmask 255.255.255.0
gateway 10.20.0.1

# ifup enp0s3
```

### SQL database

Install package

```
# apt install mariadb-server python-pymysql -y
```

Create and edit the `/etc/mysql/mariadb.conf.d/99-openstack.cnf` file and complete the following actions:

> Create a `[mysqld]` section, and set the `bind-address` key to the management IP address of the controller node to enable access by other nodes via the management network. Set additional keys to enable useful options and the UTF-8 character set:

```
[mysqld]
bind-address = 10.20.0.10

default-storage-engine = innodb
innodb_file_per_table = on
max_connections = 4096
collation-server = utf8_general_ci
character-set-server = utf8
```

restart database service

```
# service mysql restart
```

Secure the database service by running the `mysql_secure_installation` script. In particular, choose a suitable password for the database `root` account:

```
# mysql_secure_installation
```

### Message queue

Install the package:

```
# apt install rabbitmq-server
```

Add the `openstack` user:

```
# rabbitmqctl add_user openstack RABBIT_PASS

Creating user "openstack" ...

```

Replace `RABBIT_PASS` with a suitable password.

Permit configuration, write, and read access for the `openstack` user:

```
# rabbitmqctl set_permissions openstack ".*" ".*" ".*"

Setting permissions for user "openstack" in vhost "/" ...
```

### Memcached

Install the packages:

```
# apt install memcached python-memcache
```

Edit the `/etc/memcached.conf` file and configure the service to use the management IP address of the controller node. This is to enable access by other nodes via the management network:

```
-l 10.20.0.10
```

> Change the existing line that had `-l 127.0.0.1`.

Restart the Memcached service:

```
# service memcached restart
```

## Compute actions

- configure NTP by editing `/etc/chrony/chrony.conf`

  ```
  server 10.20.0.10 iburst
  ```





## Keystone installation

> ref: https://docs.openstack.org/newton/install-guide-ubuntu/keystone.html

Before you configure the OpenStack Identity service, you must create a database and an administration token.

To create the database, complete the following actions:

- Use the database access client to connect to the database server as the `root` user:

  ```
  $ mysql -u root -p

  ```

  In 16.04 LTS local access need no user/psw

  ```
  # mysql
  ```

  ​

- Create the `keystone` database:

  ```
  mysql> CREATE DATABASE keystone;
  ```

- Grant proper access to the `keystone` database:

  ```
  mysql> GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' \
    IDENTIFIED BY 'KEYSTONE_DBPASS';
  mysql> GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'%' \
    IDENTIFIED BY 'KEYSTONE_DBPASS';
  ```

  Replace `KEYSTONE_DBPASS` with a suitable password.

- Exit the database access client.

Run the following command to install the packages:

```
# apt install keystone -y
```

1. Edit the `/etc/keystone/keystone.conf` file and complete the following actions:

   - In the `[database]` section, configure database access:

     ```
     [database]
     ...
     connection = mysql+pymysql://keystone:KEYSTONE_DBPASS@controller/keystone
     ```

     Replace `KEYSTONE_DBPASS` with the password you chose for the database.

     Comment out or remove any other `connection` options in the `[database]` section.

   - In the `[token]` section, configure the Fernet token provider:

     ```
     [token]
     ...
     provider = fernet
     ```

2. Populate the Identity service database:

   ```
   # su -s /bin/sh -c "keystone-manage db_sync" keystone
   ```

3. Initialize Fernet key repositories:

   ```
   # keystone-manage fernet_setup --keystone-user keystone --keystone-group keystone
   # keystone-manage credential_setup --keystone-user keystone --keystone-group keystone
   ```

4. Bootstrap the Identity service:

   ```
   # keystone-manage bootstrap --bootstrap-password ADMIN_PASS \
     --bootstrap-admin-url http://controller:35357/v3/ \
     --bootstrap-internal-url http://controller:35357/v3/ \
     --bootstrap-public-url http://controller:5000/v3/ \
     --bootstrap-region-id RegionOne
   ```

   Replace `ADMIN_PASS` with a suitable password for an administrative user.

### Configure the Apache HTTP server

1. Edit the `/etc/apache2/apache2.conf` file and configure the `ServerName` option to reference the controller node:

   ```
   ServerName controller

   ```

### Finalize the installation

1. Restart the Apache service and remove the default SQLite database:

   ```
   # service apache2 restart
   # rm -f /var/lib/keystone/keystone.db
   ```


1. Configure the administrative account

   ```
   $ export OS_USERNAME=admin
   $ export OS_PASSWORD=ADMIN_PASS
   $ export OS_PROJECT_NAME=admin
   $ export OS_USER_DOMAIN_NAME=Default
   $ export OS_PROJECT_DOMAIN_NAME=Default
   $ export OS_AUTH_URL=http://controller:35357/v3
   $ export OS_IDENTITY_API_VERSION=3
   ```

   Replace `ADMIN_PASS` with the password used in the `keystone-manage bootstrap` command from the section called [Install and configure](https://docs.openstack.org/newton/install-guide-ubuntu/keystone-install.html#keystone-install).

### Create a domain, projects, users, and roles

The Identity service provides authentication services for each OpenStack service. The authentication service uses a combination of [domains](https://docs.openstack.org/newton/install-guide-ubuntu/common/glossary.html#term-domain), [projects](https://docs.openstack.org/newton/install-guide-ubuntu/common/glossary.html#term-project), [users](https://docs.openstack.org/newton/install-guide-ubuntu/common/glossary.html#term-user), and [roles](https://docs.openstack.org/newton/install-guide-ubuntu/common/glossary.html#term-role).

1. This guide uses a service project that contains a unique user for each service that you add to your environment. Create the `service` project:

   ```
   $ openstack project create --domain default \
     --description "Service Project" service

   +-------------+----------------------------------+
   | Field       | Value                            |
   +-------------+----------------------------------+
   | description | Service Project                  |
   | domain_id   | default                          |
   | enabled     | True                             |
   | id          | 24ac7f19cd944f4cba1d77469b2a73ed |
   | is_domain   | False                            |
   | name        | service                          |
   | parent_id   | default                          |
   +-------------+----------------------------------+
   ```

2. Regular (non-admin) tasks should use an unprivileged project and user. As an example, this guide creates the `demo` project and user.

   - Create the `demo` project:

     ```
     $ openstack project create --domain default \
       --description "Demo Project" demo

     +-------------+----------------------------------+
     | Field       | Value                            |
     +-------------+----------------------------------+
     | description | Demo Project                     |
     | domain_id   | default                          |
     | enabled     | True                             |
     | id          | 231ad6e7ebba47d6a1e57e1cc07ae446 |
     | is_domain   | False                            |
     | name        | demo                             |
     | parent_id   | default                          |
     +-------------+----------------------------------+
     ```

     Do not repeat this step when creating additional users for this project.

   - Create the `demo` user:

     ```
     $ openstack user create --domain default \
       --password-prompt demo

     User Password:
     Repeat User Password:
     +---------------------+----------------------------------+
     | Field               | Value                            |
     +---------------------+----------------------------------+
     | domain_id           | default                          |
     | enabled             | True                             |
     | id                  | aeda23aa78f44e859900e22c24817832 |
     | name                | demo                             |
     | password_expires_at | None                             |
     +---------------------+----------------------------------+
     ```

   - Create the `user` role:

     ```
     $ openstack role create user

     +-----------+----------------------------------+
     | Field     | Value                            |
     +-----------+----------------------------------+
     | domain_id | None                             |
     | id        | 997ce8d05fc143ac97d83fdfb5998552 |
     | name      | user                             |
     +-----------+----------------------------------+
     ```

   - Add the `user` role to the `demo` project and user:

     ```
     $ openstack role add --project demo --user demo user
     ```

### Verify operation

For security reasons, disable the temporary authentication token mechanism:

Edit the `/etc/keystone/keystone-paste.ini` file and remove `admin_token_auth` from the `[pipeline:public_api]`, `[pipeline:admin_api]`, and `[pipeline:api_v3]` sections.

Unset the temporary `OS_AUTH_URL` and `OS_PASSWORD` environment variable:

```
$ unset OS_AUTH_URL OS_PASSWORD
```

As the `admin` user, request an authentication token:

```
$ openstack --os-auth-url http://controller:35357/v3 \
  --os-project-domain-name Default --os-user-domain-name Default \
  --os-project-name admin --os-username admin token issue

Password:
+------------+-----------------------------------------------------------------+
| Field      | Value                                                           |
+------------+-----------------------------------------------------------------+
| expires    | 2017-08-12T20:14:07.056119Z                                     |
| id         | gAAAAABWvi7_B8kKQD9wdXac8MoZiQldmjEO643d-e_j-XXq9AmIegIbA7UHGPv |
|            | atnN21qtOMjCFWX7BReJEQnVOAj3nclRQgAYRsfSU_MrsuWb4EDtnjU7HEpoBb4 |
|            | o6ozsA_NmFWEpLeKy0uNn_WeKbAhYygrsmQGA49dclHVnz-OMVLiyM9ws       |
| project_id | 343d245e850143a096806dfaefa9afdc                                |
| user_id    | ac3377633149401296f6c0d92d79dc16                                |
+------------+-----------------------------------------------------------------+
```



This command uses the password for the `admin` user. As we gave above it's `ADMIN_PASS`.

As the `demo` user, request an authentication token:

```
$ openstack --os-auth-url http://controller:5000/v3 \
  --os-project-domain-name Default --os-user-domain-name Default \
  --os-project-name demo --os-username demo token issue

Password:
+------------+-----------------------------------------------------------------+
| Field      | Value                                                           |
+------------+-----------------------------------------------------------------+
| expires    | 2017-08-12T20:15:39.014479Z                                     |
| id         | gAAAAABWvi9bsh7vkiby5BpCCnc-JkbGhm9wH3fabS_cY7uabOubesi-Me6IGWW |
|            | yQqNegDDZ5jw7grI26vvgy1J5nCVwZ_zFRqPiz_qhbq29mgbQLglbkq6FQvzBRQ |
|            | JcOzq3uwhzNxszJWmzGC7rJE_H0A_a3UFhqv8M4zMRYSbS2YF0MyFmp_U       |
| project_id | ed0b60bf607743088218b0a533d5943f                                |
| user_id    | 58126687cbcc4888bfa9ab73a2256f27                                |
+------------+-----------------------------------------------------------------+
```



> This command uses the password for the `demo` user and API port 5000 which only allows regular (non-admin) access to the Identity service API.



### Create OpenStack client environment scripts

The previous section used a combination of environment variables and command options to interact with the Identity service via the`openstack` client. To increase efficiency of client operations, OpenStack supports simple client environment scripts also known as OpenRC files. These scripts typically contain common options for all clients, but also support unique options. For more information, see the [OpenStack End User Guide](http://docs.openstack.org/user-guide/common/cli_set_environment_variables_using_openstack_rc.html).

#### Creating the scripts

Create client environment scripts for the `admin` and `demo` projects and users. Future portions of this guide reference these scripts to load appropriate credentials for client operations.

1. Edit the `admin-openrc` file and add the following content:

   ```
   export OS_PROJECT_DOMAIN_NAME=Default
   export OS_USER_DOMAIN_NAME=Default
   export OS_PROJECT_NAME=admin
   export OS_USERNAME=admin
   export OS_PASSWORD=ADMIN_PASS
   export OS_AUTH_URL=http://controller:35357/v3
   export OS_IDENTITY_API_VERSION=3
   export OS_IMAGE_API_VERSION=2

   ```

   Replace `ADMIN_PASS` with the password you chose for the `admin` user in the Identity service.

2. Edit the `demo-openrc` file and add the following content:

   ```
   export OS_PROJECT_DOMAIN_NAME=Default
   export OS_USER_DOMAIN_NAME=Default
   export OS_PROJECT_NAME=demo
   export OS_USERNAME=demo
   export OS_PASSWORD=demo
   export OS_AUTH_URL=http://controller:5000/v3
   export OS_IDENTITY_API_VERSION=3
   export OS_IMAGE_API_VERSION=2
   ```

   Replace `OS_PASSWORD=demo` with the password you chose for the `demo` user in the Identity service.

#### Using the scripts

To run clients as a specific project and user, you can simply load the associated client environment script prior to running them. For example:

1. Load the `admin-openrc` file to populate environment variables with the location of the Identity service and the `admin` project and user credentials:

   ```
   $ . admin-openrc
   ```

2. Request an authentication token:

   ```
   root@ubuntu:~# openstack token issue --max-width 70
   +------------+-------------------------------------------------------+
   | Field      | Value                                                 |
   +------------+-------------------------------------------------------+
   | expires    | 2017-08-23T14:00:10+0000                              |
   | id         | gAAAAABZnXxaKuuwh9Kw-dbY1mSn8LeNNQMKmIj2EW8jyjO0NSy5H |
   |            | QPno4Tj6NqqSkumKhRZW8lPS1nZC2pm5fCuH5XMtVfJTu89RX6Sba |
   |            | -vSv-OZl5uHvRY4KOK03WH15Dnp1XbWN97xY8tR_kAhc-69       |
   |            | -WvDe1DLS6vKr-bKbYDVXLqlLshE8E                        |
   | project_id | 78c9c849237649a3a8c4526167427589                      |
   | user_id    | d8efd16c30904a7992010abe4bdb9a2b                      |
   +------------+-------------------------------------------------------+
   ```

## Glance installation

ref: https://docs.openstack.org/newton/install-guide-ubuntu/glance.html

For simplicity, this guide describes configuring the Image service to use the `file` back end, which uploads and stores in a directory on the controller node hosting the Image service. By default, this directory is `/var/lib/glance/images/`.

Before you proceed, ensure that the controller node has at least several gigabytes of space available in this directory. Keep in mind that since the `file` back end is often local to a controller node, it is not typically suitable for a multi-node glance deployment.

For information on requirements for other back ends, see [Configuration Reference](http://docs.openstack.org/newton/config-reference/image.html).

### Install and configure

This section describes how to install and configure the Image service, code-named glance, on the controller node. For simplicity, this configuration stores images on the local file system.

### Prerequisites

Before you install and configure the Image service, you must create a database, service credentials, and API endpoints.

1. To create the database, complete these steps:

   - Use the database access client to connect to the database server as the `root` user:

     ```
     $ mysql -u root -p
     ```

   - Create the `glance` database:

     ```
     mysql> CREATE DATABASE glance;
     ```

   - Grant proper access to the `glance` database:

     ```
     mysql> GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'localhost' \
       IDENTIFIED BY 'GLANCE_DBPASS';
     mysql> GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'%' \
       IDENTIFIED BY 'GLANCE_DBPASS';
     ```

     Replace `GLANCE_DBPASS` with a suitable password.

   - Exit the database access client.

2. Source the `admin` credentials to gain access to admin-only CLI commands:

   ```
   $ . admin-openrc

   ```

3. To create the service credentials, complete these steps:

   - Create the `glance` user:

     ```
     $ openstack user create --domain default --password-prompt glance

     User Password:
     Repeat User Password:
     +---------------------+----------------------------------+
     | Field               | Value                            |
     +---------------------+----------------------------------+
     | domain_id           | default                          |
     | enabled             | True                             |
     | id                  | 3f4e777c4062483ab8d9edd7dff829df |
     | name                | glance                           |
     | password_expires_at | None                             |
     +---------------------+----------------------------------+
     ```

   - Add the `admin` role to the `glance` user and `service` project:

     ```
     $ openstack role add --project service --user glance admin
     ```

     This command provides no output.

   - Create the `glance` service entity:

     ```
     $ openstack service create --name glance \
       --description "OpenStack Image" image

     +-------------+----------------------------------+
     | Field       | Value                            |
     +-------------+----------------------------------+
     | description | OpenStack Image                  |
     | enabled     | True                             |
     | id          | 8c2c7f1b9b5049ea9e63757b5533e6d2 |
     | name        | glance                           |
     | type        | image                            |
     +-------------+----------------------------------+
     ```

4. Create the Image service API endpoints:

   ```
   $ openstack endpoint create --region RegionOne \
     image public http://controller:9292

   +--------------+----------------------------------+
   | Field        | Value                            |
   +--------------+----------------------------------+
   | enabled      | True                             |
   | id           | 340be3625e9b4239a6415d034e98aace |
   | interface    | public                           |
   | region       | RegionOne                        |
   | region_id    | RegionOne                        |
   | service_id   | 8c2c7f1b9b5049ea9e63757b5533e6d2 |
   | service_name | glance                           |
   | service_type | image                            |
   | url          | http://controller:9292           |
   +--------------+----------------------------------+

   $ openstack endpoint create --region RegionOne \
     image internal http://controller:9292

   +--------------+----------------------------------+
   | Field        | Value                            |
   +--------------+----------------------------------+
   | enabled      | True                             |
   | id           | a6e4b153c2ae4c919eccfdbb7dceb5d2 |
   | interface    | internal                         |
   | region       | RegionOne                        |
   | region_id    | RegionOne                        |
   | service_id   | 8c2c7f1b9b5049ea9e63757b5533e6d2 |
   | service_name | glance                           |
   | service_type | image                            |
   | url          | http://controller:9292           |
   +--------------+----------------------------------+

   $ openstack endpoint create --region RegionOne \
     image admin http://controller:9292

   +--------------+----------------------------------+
   | Field        | Value                            |
   +--------------+----------------------------------+
   | enabled      | True                             |
   | id           | 0c37ed58103f4300a84ff125a539032d |
   | interface    | admin                            |
   | region       | RegionOne                        |
   | region_id    | RegionOne                        |
   | service_id   | 8c2c7f1b9b5049ea9e63757b5533e6d2 |
   | service_name | glance                           |
   | service_type | image                            |
   | url          | http://controller:9292           |
   +--------------+----------------------------------+
   ```

### Install and configure components

Install the packages:

```
# apt install glance -y
```

1. Edit the `/etc/glance/glance-api.conf` file and complete the following actions:

   - In the `[database]` section, configure database access:

     ```
     [database]
     ...
     connection = mysql+pymysql://glance:GLANCE_DBPASS@controller/glance
     ```

     Replace `GLANCE_DBPASS` with the password you chose for the Image service database.

   - In the `[keystone_authtoken]` and `[paste_deploy]` sections, configure Identity service access:

     ```
     [keystone_authtoken]
     ...
     auth_uri = http://controller:5000
     auth_url = http://controller:35357
     memcached_servers = controller:11211
     auth_type = password
     project_domain_name = Default
     user_domain_name = Default
     project_name = service
     username = glance
     password = glance

     [paste_deploy]
     ...
     flavor = keystone
     ```

     Replace `password = glance` with the password you chose for the `glance` user in the Identity service.

     ​

     Comment out or remove any other options in the `[keystone_authtoken]` section.

   - In the `[glance_store]` section, configure the local file system store and location of image files:

     ```
     [glance_store]
     ...
     stores = file,http
     default_store = file
     filesystem_store_datadir = /var/lib/glance/images/
     ```

2. Edit the `/etc/glance/glance-registry.conf` file and complete the following actions:

   - In the `[database]` section, configure database access:

     ```
     [database]
     ...
     connection = mysql+pymysql://glance:GLANCE_DBPASS@controller/glance
     ```

     Replace `GLANCE_DBPASS` with the password you chose for the Image service database.

   - In the `[keystone_authtoken]` and `[paste_deploy]` sections, configure Identity service access:

     ```
     [keystone_authtoken]
     ...
     auth_uri = http://controller:5000
     auth_url = http://controller:35357
     memcached_servers = controller:11211
     auth_type = password
     project_domain_name = Default
     user_domain_name = Default
     project_name = service
     username = glance
     password = glance

     [paste_deploy]
     ...
     flavor = keystone
     ```

     Replace `password = glance` with the password you chose for the `glance` user in the Identity service.

     Comment out or remove any other options in the `[keystone_authtoken]` section.

Populate the Image service database:

```
# su -s /bin/sh -c "glance-manage db_sync" glance
```

Ignore any deprecation messages in this output.

### Finalize installation

Restart the Image services:

```
# service glance-registry restart
# service glance-api restart
```

### Verify operation

Verify operation of the Image service using [CirrOS](http://launchpad.net/cirros), a small Linux image that helps you test your OpenStack deployment.

For more information about how to download and build images, see [OpenStack Virtual Machine Image Guide](http://docs.openstack.org/image-guide/). For information about how to manage images, see the [OpenStack End User Guide](http://docs.openstack.org/user-guide/common/cli-manage-images.html).



1. Source the `admin` credentials to gain access to admin-only CLI commands:

   ```
   $ . admin-openrc
   ```

2. Download the source image:

   ```
   $ wget http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img
   ```

   > tip: add proxy to improve speed in office network
   >
   > ```
   > $ export http_proxy=http://www-proxy.exu.ericsson.se:8080
   >
   > // after wget
   >
   > $ unset http_proxy
   > ```

   Install `wget` if your distribution does not include it.

3. Upload the image to the Image service using the [QCOW2](https://docs.openstack.org/newton/install-guide-ubuntu/common/glossary.html#term-qemu-copy-on-write-2-qcow2) disk format, [bare](https://docs.openstack.org/newton/install-guide-ubuntu/common/glossary.html#term-bare) container format, and public visibility so all projects can access it:

   ```
   $ openstack image create "cirros" \
     --file cirros-0.3.4-x86_64-disk.img \
     --disk-format qcow2 --container-format bare \
     --public

   +------------------+------------------------------------------------------+
   | Field            | Value                                                |
   +------------------+------------------------------------------------------+
   | checksum         | 133eae9fb1c98f45894a4e60d8736619                     |
   | container_format | bare                                                 |
   | created_at       | 2015-03-26T16:52:10Z                                 |
   | disk_format      | qcow2                                                |
   | file             | /v2/images/cc5c6982-4910-471e-b864-1098015901b5/file |
   | id               | cc5c6982-4910-471e-b864-1098015901b5                 |
   | min_disk         | 0                                                    |
   | min_ram          | 0                                                    |
   | name             | cirros                                               |
   | owner            | ae7a98326b9c455588edd2656d723b9d                     |
   | protected        | False                                                |
   | schema           | /v2/schemas/image                                    |
   | size             | 13200896                                             |
   | status           | active                                               |
   | tags             |                                                      |
   | updated_at       | 2015-03-26T16:52:10Z                                 |
   | virtual_size     | None                                                 |
   | visibility       | public                                               |
   +------------------+------------------------------------------------------+
   ```

   For information about the **openstack image create** parameters, see [Create or update an image (glance)](http://docs.openstack.org/user-guide/common/cli-manage-images.html#create-or-update-an-image-glance) in the `OpenStack UserGuide`.

   For information about disk and container formats for images, see [Disk and container formats for images](http://docs.openstack.org/image-guide/image-formats.html) in the `OpenStack VirtualMachine Image Guide`.

   ​

   OpenStack generates IDs dynamically, so you will see different values in the example command output.

4. Confirm upload of the image and validate attributes:

   ```
   $ openstack image list

   +--------------------------------------+--------+--------+
   | ID                                   | Name   | Status |
   +--------------------------------------+--------+--------+
   | 38047887-61a7-41ea-9b49-27987d5e8bb9 | cirros | active |
   +--------------------------------------+--------+--------+
   ```