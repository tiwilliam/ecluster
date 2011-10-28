#!/bin/bash

hostname=$1

if [ -z $hostname ]; then
	echo "usage: $0 <hostname>"
	exit 1
fi

# Set hostname
sed -i '/HOSTNAME/d' /etc/sysconfig/network
echo "HOSTNAME=$hostname" >> /etc/sysconfig/network
hostname $hostname

# Install and run puppet
yum -y install puppet
puppetd --test --server=127.0.0.1
