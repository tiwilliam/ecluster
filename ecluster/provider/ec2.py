import boto
import time

class Provider():
	def __init__(self, cluster, **kargs):
		self.cluster = cluster
		
		if 'key' and 'secret' in kargs:
			self.access_key = kargs['key']
			self.secret_key = kargs['secret']
		else:
			raise BaseException('Error: EC2 need key and secret as argument to Cluster')
	
	def get_running(self):
		instances = []
		try:
			conn = boto.connect_ec2(self.access_key, self.secret_key)
			for reservation in conn.get_all_instances():
				for instance in reservation.instances:
					if instance.state in ['running', 'pending'] and instance.tags.get('Cluster') == self.cluster:
						instances += [instance]
		except boto.exception.EC2ResponseError, e:
			raise BaseException('Error: %s' % e.error_message)
		
		return instances
		
	def get_groups(self):
		try:
			conn = boto.connect_ec2(self.access_key, self.secret_key)
			sgs = conn.get_all_security_groups()
		except boto.exception.EC2ResponseError, e:
			raise BaseException('Error: %s' % e.error_code)

		return sgs
	
	def create_node(self, cluster, name, image, type, keypair=None, groups=None):
		key_list = []
		group_list = []

		try:
			conn = boto.connect_ec2(self.access_key, self.secret_key)
			images = conn.get_all_images([image])
		
			# Get keys from cloud
			for key in conn.get_all_key_pairs():
				key_list += [str(key.name)]
		
			# Get security groups from cloud
			for group in conn.get_all_security_groups():
				group_list += [str(group.name)]
		
			# Check if all key pairs we have in config exists
			if keypair not in key_list:
				raise BaseException('Error: keypair does not exist in cloud: %s' % keypair)

			# Check if all groups we have in config exists
			for group in groups:
				if group not in group_list:
					raise BaseException('Error: security group does not exist in cloud: %s' % group)
		
			image = images[0]

			reservation = image.run(instance_type=type,key_name=keypair,security_group_ids=groups)
			instance = reservation.instances[0]

			# boto have no way to check status of a reservations and
			# there seems to be a race-condition here
			retry_timeout = 10
			for timeout in range(1, retry_timeout + 1):
				try:
					time.sleep(1)
					instance.add_tag('Name', name)
					instance.add_tag('Cluster', cluster)
					break
				except:
					print 'Failed to set tags on instance - sleeping one second'
					continue
		except boto.exception.EC2ResponseError, e:
			raise BaseException('Error: %s' % e.error_message)
		
		return instance
