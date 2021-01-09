---
title: notes after creating a fuel plugin
date: 2019-01-17 10:15:12
tags:
  - fuel-plugin
  - openstack
  - puppet
categories: 
  - openstack
---



# 关于

这篇文章是我做一个内部 knowledge sharing准备的文档，介绍了如何基于MIranis fuel的平台开发一个fuel plugin，我用了一个死了的项目 nova-docker作为实际的例子。

# Build a fuel plugin from scrash

> **Live demo:**
>
> Let's try to build a fuel plugin enables nova-docker
>
> Code put here: https://github.com/wey-gu/fuel-plugin-nova-docker

## Create fuel plugin for `nova-docker`

**Steps needed:**

- Step 1 Installation packages
  - install nova-docker
  - install dependency (docker)
- Step 2 configuration
  - configuration on nova compute
  - configuration on nova controller

<!--more-->

### [Step 0] Initiate the project

```bash
$ ~ fpb --create nova_docker
Plugin is created
$ ~ fpb --build nova_docker
Plugin is built
$ ~ cd nova_docker
$ nova_docker ls
bond_config.yaml         network_roles.yaml     node_roles.yaml                     tasks.yaml
components.yaml          metadata.yaml          pre_build_hook                      volumes.yaml
deployment_scripts       LICENSE  #pack buit--> nova_docker-1.0-1.0.0-1.noarch.rpm
$ nova_docker git init
Initialized empty Git repository in ~/nova_docker/.git/
```

Let's exclude the nova-docker binary file from our git base.

```bash
$ nova_docker git:(master) cat .gitignore
.tox
.build
*.pyc
*.rpm
```

```bash
$ nova_docker git:(master) tree -L 2
.
├── bond_config.yaml
├── components.yaml
├── deployment_scripts
│   └── deploy.sh
├── deployment_tasks.yaml
├── environment_config.yaml
├── LICENSE
├── metadata.yaml
├── network_roles.yaml
├── nic_config.yaml
├── node_config.yaml
├── node_roles.yaml
├── pre_build_hook
├── README.md
├── repositories
│   ├── centos
│   └── ubuntu
├── tasks.yaml
└── volumes.yaml
```



### [Step 1] Installation packages

#### `nova-docker`

- ensure needed packages included in plugin
- code to install packages

##### >> Fetch the `nova-docker` source code

> fetch the file from github: [url](https://github.com/openstack/nova-docker)

```bash
$ mkdir -p repositories/python && cd repositories/python
$ git clone git@github.com:openstack/nova-docker.git && cd nova-docker
# project was removed, have to checkout to the previous commit of the last master head
$ git checkout HEAD^1
$ git log
commit 034a4842fc1ebba5912e02cff8cd197ae81eb0c3 (HEAD, origin/stable/ocata)
$ git checkout stable/mitaka
```

##### >> Build `nova-docker`

- **option one**, build a python sdist `tar` file

```bash
setup.py sdist
```

> An example of option one

```bash
$ python setup.py sdist
$ tree dist
dist
└── nova-docker-0.0.1.dev275.tar.gz

# easy_install instead of pip to install this source dist tar file will do the job
$ easy_install dist/nova-docker-0.0.1.dev275.tar.gz
```

- **option two**, build a `deb` file

> ref: https://fpm.readthedocs.io/en/latest/

```bash
fpm -v "1:0.0.1" -s python -t deb -n fuel-plugin-nova-docker \
  --python-install-bin /usr/bin \
  --python-install-lib /usr/lib/python2.7/dist-packages/ \
  nova-docker/setup.py
```

> An example of option two

```bash
$ fpm -v "1:0.0.1" -s python -t deb -n fuel-plugin-nova-docker \
  --python-install-bin /usr/bin \
  --python-install-lib /usr/lib/python2.7/dist-packages/ \
  nova-docker/setup.py

Created package {:path=>"fuel-plugin-nova-docker_1:0.0.1_all.deb"}
$ ls
fuel-plugin-nova-docker_1:0.0.1_all.deb  nova-docker
```

##### >> Install `nova-docker`

> with above two options, we could do like this

either `install.pp` with **option one**:

```ruby
exec {'install nova-docker':
  command => 'easy_install /temp/nova-docker*.tar.gz',
  path    => '/bin:/usr/bin:/usr/local/bin',
}
```

or `install.pp` with **option two**:

```ruby
package {'fuel-plugin-nova-docker':
  ensure  => 'installed',
}
```

##### >> Include `nova-docker`

Let's add `nova-docker` as a `submodule` as upstream project instead of putting a binary package.

```bash
$ git submodule add git@github.com:openstack/nova-docker.git repositories/python/nova-docker
```

To ensure this package being built during `fpb --build nova-docker` we should do this via `pre_build_hook`

```bash
#!/bin/bash

# Add here any the actions which are required before plugin build
# like packages building, packages downloading from mirrors and so on.
# The script should return 0 if there were no errors.
cd repositories/python
git submodule update --init --recursive
cd nova-docker; git checkout stable/mitaka; cd ..
fpm -v "1:0.0.1" -s python \
  -t deb \
  -n fuel-plugin-nova-docker \
  --python-install-bin /usr/bin \
  --python-install-lib /usr/lib/python2.7/dist-packages/ \
  nova-docker/setup.py
mv *.deb ../ubuntu
```

Verify it via a plugin build.

```bash
$ ~ fpb --build nova_docker
Plugin is built
$ ~ cd nova_docker
$ nova_docker git:(master) ls repositories/ubuntu
fuel-plugin-nova-docker_1:0.0.1_all.deb
```

Let's exclude the nova-docker binary file from the repository.

```bash
$ nova_docker git:(master) cat .gitignore
.tox
.build
*.pyc
*.rpm
repositories/ubuntu/fuel-plugin-nova-docker*.deb
```

#### `docker`

> As we are working on mos 9.0, which is Ubuntu 14.04, the ubuntu build docker is named `docker.io` in repository.

below lines could be enough:

```ruby
package {'docker.io':
  ensure  => 'installed',
} ->
exec {'add nova to docker group':
  command => 'usermod -aG docker nova',
  path    => '/bin:/usr/bin:/usr/local/bin',
}
```

##### >> debugging puppet code

Save it as `install.pp` , let's verify it like this:

```bash
root@node-1:~# puppet apply --debug ./install.pp
Error: Could not find command 'usermod'
Error: /Stage[main]/Main/Exec[add nova to docker group]/returns: change from notrun to 0 failed: Could not find command 'usermod'

root@node-1:~# which usermod
/usr/sbin/usermod
```

Then we come to know path need to be put with `/usr/sbin`.

```ruby
package {'docker.io':
  ensure  => 'installed',
} ->
exec {'add nova to docker group':
  command => 'usermod -aG docker nova',
  path    => '/bin:/usr/bin:/usr/local/bin:/usr/sbin',
}
```

And now we have a verified `install.pp` :

```bash
package {'fuel-plugin-nova-docker':
  ensure  => 'installed',
} ->
package {'docker.io':
  ensure  => 'installed',
} ->
exec {'add nova to docker group':
  command => 'usermod -aG docker nova',
  path    => '/bin:/usr/bin:/usr/local/bin:/usr/sbin',
} ->
exec {'verify docker installation':
  command => 'su nova -c docker ps',
  path    => '/bin:/usr/bin:/usr/local/bin:/usr/sbin',
}
```



### [Step 2] Configuration

> referring to `nova-docker` README here:  [README.rst](https://github.com/openstack/nova-docker/blob/4923a7d53024e0d476befe3a8b6dd841537569b6/README.rst), we need to do below configuration change:

- In `nova.conf` for `nova-compute`:

  ```bash
  compute_driver=novadocker.virt.docker.DockerDriver
  ```

- In `glance-api.conf`:

  ```bash
  container_formats=ami,ari,aki,bare,ovf,ova,docker
  ```

Then it could be done like below, where `roles_include` is a function from `fuel-library` on ruby function : `library/deployment/puppet/osnailyfacter/spec/functions/roles_include_spec.rb` (source code --> [url](https://github.com/openstack/fuel-library/blob/master/deployment/puppet/osnailyfacter/spec/functions/roles_include_spec.rb))

> referring to project: `fuel-library` https://github.com/openstack/fuel-library

Let's name it as `configure.pp`

```ruby
if roles_include(['compute']){
    nova_config {
      'default/compute_driver':     value => "novadocker.virt.docker.DockerDriver";
    } ->
    exec{"restart nova compute service":
      command => "/usr/sbin/service nova-compute restart",
    }
}

if (roles_include(['controller']) or roles_include(['primary-controller'])){
    glance_api_config {
      'default/container_formats':  value => "ami,ari,aki,bare,ovf,ova,docker";
    } ->
    exec{"restart Glance api service":
      command => "/usr/sbin/service glance-api restart",
    } ->
    exec{"restart Glance glare service":
      command => "/usr/sbin/service glance-glare restart",
    } ->
    exec{"restart Glance registry service":
      command => "/usr/sbin/service glance-registry restart",
    }
}
```

Let's add this condition check on `install.pp` as well.

```ruby
if roles_include(['compute']){
    package {'fuel-plugin-nova-docker':
      ensure  => 'installed',
    } ->
    package {'docker.io':
      ensure  => 'installed',
    } ->
    exec {'add nova to docker group':
      command => 'usermod -aG docker nova',
      path    => '/bin:/usr/bin:/usr/local/bin:/usr/sbin',
    } ->
    exec {'verify docker installation':
      command => 'su nova -c docker ps',
      path    => '/bin:/usr/bin:/usr/local/bin:/usr/sbin',
    }
}
```

### Fuel plugin [file structure]

The scripts entry path is `deployment_scripts`:

```bash
$ nova_docker git:(master) mkdir -p deployment_scripts/puppet/manifests
$ nova_docker git:(master) tree deployment_scripts
deployment_scripts
├── deploy.sh     # dummy script from the fpb template
└── puppet        # we create puppet files here
    └── manifests
```

The scripts were called via tasks in `deployment_tasks.yml` in the whole graph.

##### >> Entry for `nova_docker-install`

Let's compse the  `deployment_tasks.yml`, where we would like our `install.pp` being called during `post_deployment` on `role: compute`:

```yaml
# If you do not want to use task-based deployment that is introduced as experimental
# in fuel v8.0 comment code section below this comment, uncomment two lines below it
# and do the same for tasks below.

- id: nova_docker-install
  type: puppet
  version: 2.0.0
  role: [compute]
  requires: [post_deployment_start]
  required_for: [post_deployment_end]
  parameters:
    puppet_manifest: puppet/manifests/install.pp
    puppet_modules: puppet/modules:/etc/puppet/modules
    timeout: 600
    retries: 3
    interval: 20
```

##### >> Entry for `nova_docker-configure`

Add this part to  `deployment_tasks.yml` for `configure.pp`.

```yaml
- id: nova_docker-configure
  type: puppet
  version: 2.0.0
  role: [primary-controller, controller, compute]
  requires: [post_deployment_start, nova_docker-install]
  cross-depends:
    - name: nova_docker-install
      role: [primary-controller, controller, compute]
  required_for: [post_deployment_end]
  parameters:
    puppet_manifest: puppet/manifests/configure.pp
    puppet_modules: puppet/modules:/etc/puppet/modules
    timeout: 600
    retries: 3
    interval: 20
```



### Metadata change

`metadata.yaml` are changed accordingly

```yaml
homepage: 'https://github.com/wey-gu/fuel-plugin-nova-docker'
is_hotpluggable: true
```

### Debug fuel plugin deployment

### Install plugin

```bash
$ scp ./nova_docker-1.0-1.0.0-1.noarch.rpm fuel:/root/

$ fuel plugins --install /root/nova_docker-1.0-1.0.0-1.noarch.rpm

$ fuel plugins --sync
```

### Check status

```bash
[root@fuel ~]# fuel2 task history show 21 --node 1 2 3 --status ready
+----------------------+----+--------+----------------------------+----------------------------+
| task_name            | id | status | time_start                 | time_end                   |
+----------------------+----+--------+----------------------------+----------------------------+
| upload_configuration | 1  | ready  | 2019-01-20T14:32:42.823654 | 2019-01-20T14:32:43.150434 |
| upload_configuration | 3  | ready  | 2019-01-20T14:32:43.057490 | 2019-01-20T14:32:43.175740 |
| upload_configuration | 2  | ready  | 2019-01-20T14:32:43.125496 | 2019-01-20T14:32:43.201964 |
| setup_repositories   | 3  | ready  | 2019-01-20T14:32:44.480248 | 2019-01-20T14:32:50.491014 |
| setup_repositories   | 2  | ready  | 2019-01-20T14:32:44.548006 | 2019-01-20T14:32:50.522656 |
| setup_repositories   | 1  | ready  | 2019-01-20T14:32:44.409323 | 2019-01-20T14:32:54.502436 |
+----------------------+----+--------+----------------------------+----------------------------+

[root@fuel ~]# fuel plugins
id | name        | version | package_version | releases
---+-------------+---------+-----------------+---------------------------------
1  | nova_docker | 1.0.0   | 5.0.0           | ubuntu (mitaka-9.0, newton-10.0)

[root@fuel ~]# ls -l /var/www/nailgun/plugins/
total 4
drwxr-xr-x. 4 root root 4096 Jan 20 14:32 nova_docker-1.0


```

### Deploy Plugin

Let's do it!

```bash
[root@fuel ~]# fuel node --node 1 2 --task nova_docker-install nova_docker-configure
400 Client Error: Bad Request for url: http://10.20.0.2:8000/api/v1/clusters/1/deploy_tasks/?nodes=1,2 (Tasks nova_docker-install,nova_docker-configure are not present in deployment graph)
```

fuel deployment's entry is the deployement graph, simply install the plugin is not enough, we still need to update the graph:

```bash
[root@fuel ~]# fuel2 graph download -e 1 -a
Tasks were downloaded to /root/cluster_graph.yaml
[root@fuel ~]# vim cluster_graph.yaml

// do changes here

[root@fuel ~]# fuel2 graph upload -e 1  -t default -f cluster_graph.yaml
Deployment graph was uploaded from cluster_graph.yaml
```

`diff /root/cluster_graph.yaml.backup /root/cluster_graph.yaml`

```diff
4988a4989,5015
> - id: nova_docker-install
>   type: puppet
>   version: 2.0.0
>   role: [compute]
>   requires: [post_deployment_start]
>   required_for: [post_deployment_end]
>   parameters:
>     puppet_manifest: puppet/manifests/install.pp
>     puppet_modules: puppet/modules:/etc/puppet/modules
>     timeout: 600
>     retries: 3
>     interval: 20
> - id: nova_docker-configure
>   type: puppet
>   version: 2.0.0
>   role: [primary-controller, controller, compute]
>   requires: [post_deployment_start, nova_docker-install]
>   cross-depends:
>     - name: nova_docker-install
>       role: [primary-controller, controller, compute]
>   required_for: [post_deployment_end]
>   parameters:
>     puppet_manifest: puppet/manifests/configure.pp
>     puppet_modules: puppet/modules:/etc/puppet/modules
>     retries: 3
>     interval: 20
>     timeout: 600
```

Let's retry!

```bash
[root@fuel ~]# fuel node --node 1 2 --task nova_docker-install nova_docker-configure
Started tasks ['nova_docker-install', 'nova_docker-configure'] for nodes nodes [1, 2].
```

Error occuered

### >> debugging plugin deployment

Narrow down the error node: node-2

```bash
[root@fuel ~]# fuel2 task history show 23 --status error
+---------------------+---------+--------+----------------------------+...
| task_name           | node_id | status | time_start                 |...
+---------------------+---------+--------+----------------------------+...
| nova_docker-install | 2       | error  | 2019-01-20T14:56:03.262103 |...
+---------------------+---------+--------+----------------------------+...

[root@fuel ~]# fuel2 node list -c id -c status -c name -c online
+----+------------+--------+--------+
| id | name       | status | online |
+----+------------+--------+--------+
|  3 | cinder     | ready  | True   |
|  1 | controller | ready  | True   |
|  2 | compute    | error  | True   | <----
+----+------------+--------+--------+

```

Get the err from puppet log, this means the plugin was not

```bash
[root@fuel ~]# ssh node-2 "egrep '(err)' /var/log/puppet.log  -A2 | tail"

2019-01-20 14:56:02 +0000 Puppet (err): Could not run: Could not find file puppet/manifests/install.pp
/usr/lib/ruby/vendor_ruby/puppet/application/apply.rb:179:in `main'
/usr/lib/ruby/vendor_ruby/puppet/application/apply.rb:159:in `run_command'
--
2019-01-20 14:56:04 +0000 Puppet (err): Could not run: Could not find file puppet/manifests/install.pp
/usr/lib/ruby/vendor_ruby/puppet/application/apply.rb:179:in `main'
/usr/lib/ruby/vendor_ruby/puppet/application/apply.rb:159:in `run_command'
```

The plugin was not placed

```bash
$ fuel node --node 1 2 3 --tasks upload_configuration plugins_rsync setup_repositories --force
```



# Debug tips

> Some tips were got from days of painful practice...

## fuel plugin update/ distribute

```bash
# not always working
yum -y reinstall --disablerepo='*' /var/www/nailgun/<path>/fuel-plugins/plugin_foo.rpm
yum -y install --disablerepo='*' /var/www/nailgun/<path>/fuel-plugins/plugin_foo.rpm
# obvirously you could do so
rpm -i /var/www/nailgun/<path>/fuel-plugins/plugin_foo.rpm --force
[root@fuel ~]# fuel plugins --sync

[root@fuel ~]# fuel node --node <nodes-id> --tasks upload_configuration setup_repositories plugins_rsync --force

```

> directly calling a `.pp` file on target node

```bash
[node-0]# cd /etc/fuel/plugins/<plugin_foo-1.0>
[node-0]# puppet apply --debug \
    --modulepath=puppet/modules:/etc/puppet/modules:<path_plugin_bar-1.0>/puppet/modules \
    puppet/manifests/plugin_foo_task_01.pp

// or sanity test only without actually executing changes with --noop
[node-0]# puppet apply --debug --noop \
    --modulepath=puppet/modules:/etc/puppet/modules:<path_plugin_bar-1.0>/puppet/modules \
    puppet/manifests/plugin_foo_task_01.pp
```

## task order debugging

The deployment process is a graph.

```bash
[root@fuel ~]# grep ".dot" /var/log/astute/astute.log
:graph_dot_dir: /var/lib/astute/graphs
:graph_dot_dir: /var/lib/astute/graphs
2019-01-18 03:33:46 INFO [26377] Check graph into file /var/lib/astute/graphs/graph-7395c5dc-bd42-40ab-9367-9ec5dc29ff05.dot
# or generate yourself

[root@fuel ~]# fuel graph --env 1 --download > graph.dot
```

Use `graphviz` to read it or even render it as picture file.

```bash
$ brew install graphviz # or apt-get install graphviz
$ dot -Tpng graph.dot -o graph.png
$ brew reinstall graphviz --with-app # mac with GUI
```

> Modify, debug and dry run tasks graph

```bash
[root@fuel ~]# fuel2 graph download -e 1 -a
Tasks were downloaded to /root/cluster_graph.yaml
[root@fuel ~]# vim cluster_graph.yaml

// do changes here

[root@fuel ~]# fuel2 graph upload -e 1  -t default -f cluster_graph.yaml

// quickly check if loop detected --noop is doing the magic
[root@fuel ~]# fuel2 graph execute -e 1 -t default --noop --force

// error example see `foo_task` below: 
"Method task_deploy. Cluster[]: Loop detected! Path: Task[audit_logging_configuration/1], Task[deploy_end/virtual_sync_node], Task[post_deployment_start/virtual_sync_node], Task[foo_task/3], Task[bar_task_0/1], Task[bar_task_2/3], Task[foo_task/3].\nInspect Astute logs for the details"

```

> **Tip: Run a range of tasks**
>
> For testing purposes you might want to run not one task, but a range of them. To do this use the following form of command `fuel node`:

```bash
fuel node --node <node-id> \
  --start <name of the first task> \
  --end <name of the last task> \
[ --skip <list of the tasks that should be skipped> ]
```

## yaql

> ref: 
>
> - https://github.com/openstack/yaql
> - https://github.com/openstack/fuel-web/tree/master/nailgun/nailgun/fuyaql

```bash
[root@fuel ~]# manage.py yaql -c 1
```



#Reference

```bash
[0]: https://docs.openstack.org/fuel-docs/mitaka/devdocs/develop.html   "Fuel Develop Guide"
[1]: https://docs.openstack.org/fuel-docs/newton/plugindocs/fuel-plugin-sdk-guide.html  "F.P. SDK Guide"
[2]: https://wiki.openstack.org/wiki/Fuel_CLI   "Fuel CLI cheatsheet"
[3]: https://goo.gl/BRB6vR  "Fuel plugin handbook"
[4]: https://docs.openstack.org/fuel-docs/mitaka/devdocs/develop/sequence.html  "Fuel Sequence Diagrams"
[5]: https://github.com/openstack/nova-docker/blob/4923a7d53024e0d476befe3a8b6dd841537569b6/README.rst  "nova-docker"
[6]: http://docs.ocselected.org/openstack-manuals/juno/fuel-docs/reference-architecture.html    "Fuel 中文"
[7]: https://docs.mirantis.com/fuel-docs/mitaka/devdocs/develop/modular-architecture.html   "Modular Arch"
[8]: https://wiki.openstack.org/wiki/Fuel/Plugins   "Fuel Plugins Wiki"
[9]: https://wiki.opnfv.org/display/ds/Build+fuel-plugin-opendaylight   "Another Example"
```

[0]: https://docs.openstack.org/fuel-docs/mitaka/devdocs/develop.html	"Fuel Develop Guide"
[1]: https://docs.openstack.org/fuel-docs/newton/plugindocs/fuel-plugin-sdk-guide.html	"F.P. SDK Guide"
[2]: https://wiki.openstack.org/wiki/Fuel_CLI	"Fuel CLI cheatsheet"
[3]: https://goo.gl/BRB6vR	"Fuel plugin handbook"

[4]: https://docs.openstack.org/fuel-docs/mitaka/devdocs/develop/sequence.html	"Fuel Sequence Diagrams"
[5]: https://github.com/openstack/nova-docker/blob/4923a7d53024e0d476befe3a8b6dd841537569b6/README.rst	"nova-docker"
[6]: http://docs.ocselected.org/openstack-manuals/juno/fuel-docs/reference-architecture.html	"Fuel 中文"
[7]: https://docs.mirantis.com/fuel-docs/mitaka/devdocs/develop/modular-architecture.html	"Modular Arch"
[8]: https://wiki.openstack.org/wiki/Fuel/Plugins	"Fuel Plugins Wiki"
[9]: https://wiki.opnfv.org/display/ds/Build+fuel-plugin-opendaylight	"Another Example"

