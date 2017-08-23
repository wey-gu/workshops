# Installation Guide

> ref https://docs.openstack.org/install-guide

Ubuntu was chosen as host OS.

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
