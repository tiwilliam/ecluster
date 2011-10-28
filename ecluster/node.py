import os
import time
import paramiko

class Node():
	def __init__(self, type, id, provider, cluster, instance=None):
		self.id = id
		self.type = type
		self.provider = provider
		self.instance = instance
		self.cluster = cluster

		self.replace = False		
		self.changed = False
		self.created = False
		self.deleted = False

		self.name = '%s%s' % (self.type.name, self.id)
	
	def locate_in_cloud(self):
		if not self.instance and not self.replace:
			# Load instance object if node already exist
			for instance in self.provider.get_running():
				if instance.tags.get('Name') == self.name:
					self.instance = instance
					break

			# Node found in cloud
			if self.instance:
				self.created = True
				self.detect_changes()
		
	def detect_changes(self):
		cloud_groups = []
		local_groups = []
		
		for group in self.instance.groups:
			cloud_groups += [str(group.name)]
		
		cloud_image = self.instance.image_id
		cloud_type = self.instance.instance_type
		cloud_keypair = self.instance.key_name
		
		if self.type.groups:
			local_groups = self.type.groups

		# Find difference between groups
		group_add = list(set(cloud_groups) - set(local_groups))
		group_del = list(set(local_groups) - set(cloud_groups))
		group_total = group_add + group_del
		
		if group_total:
			self.changed = True
		if self.type.keypair != cloud_keypair:
			self.changed = True
		if self.type.image != cloud_image:
			self.changed = True
		if self.type.type != cloud_type:
			self.changed = True
	
	def waitup(self):
		print '%s: booting machine' % self.name
		while True:
			self.instance.update()
			
			if self.instance.state in ['running']:
				break
			
			time.sleep(10)
	
	def bootstrap(self, script):
		user = self.type.user
		keypair = self.type.keypair
		hostname = self.instance.ip_address

		print '%s: bootstrapping' % self.name

		if not os.path.isfile('keypair/%s.pem' % keypair):
			raise BaseException('Error: Cannot find private key: keypair/%s.pem' % keypair)

		if not os.path.isfile('bootstrap/%s' % script):
			raise BaseException('Error: Cannot find bootstrap script: bootstrap/%s' % script)

		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		timeout = 60
		for x in range(0, timeout):
			try:
				ssh.connect(hostname, username=user, key_filename='keypair/%s.pem' % keypair)
				break
			except:
				time.sleep(1)

		transport = ssh.get_transport()

		if not transport.is_authenticated():
			raise BaseException('Error: Cannot authenticate SSH connection')

		sftp = ssh.open_sftp()
		sftp.put('bootstrap/%s' % script, '/tmp/%s' % script)
		sftp.close()

		chan = ssh.get_transport().open_session()
		chan.get_pty()

		chan.exec_command('sudo bash /tmp/%s %s' % (script, self.name))
		ret = chan.recv_exit_status()

		chan.close()
		ssh.close()

		return ret
	
	# Create node in the cloud
	def create(self):
		if not self.instance:
			self.instance = self.provider.create_node(self.cluster, self.name, self.type.image, self.type.type, self.type.keypair, self.type.groups)
			print '%s: created' % self.name
			return True
		else:
			print 'Warning: Node already exists in cloud: %s' % self.name
			return False
	
	# Destroy instance
	def destroy(self):
		if self.instance:
			self.instance.terminate()
			print '%s: destroyed' % self.name
		else:
			print 'Warning: No such node in cloud: %s' % self.name
