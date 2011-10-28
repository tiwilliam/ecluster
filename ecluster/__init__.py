import re
import sys
import boto
import provider

from ecluster.type import Type
from ecluster.typelist import TypeList
from ecluster.nodelist import NodeList

class Cluster():
	def __init__(self, service, name, **kargs):
		self.name = name
		self.type = Type('default')
		self.provider = provider.load(service, name, **kargs)
		
		if not self.provider: sys.exit(1)
		
		self.typelist = TypeList()
		self.nodelist = NodeList(self.name, self.provider)
		
		self.cmds = ['status', 'sync']
		
	def read_manifest(self):
		for type in self.typelist.types:
			for n in range(1, type.nodes + 1):
				try:
					self.nodelist.add_node(type)
				except BaseException, e:
					print e
					sys.exit(1)
		
		# Find nodes that exist in cloud by not in config - delete them
		for instance in self.provider.get_running():
			if not self.nodelist.instance_in_list(instance):
				namematch = re.match('([A-Za-z]+)([0-9]+)', instance.tags.get('Name')).groups()
				if len(namematch) == 2:
					type = self.typelist.get_type_by_name(namematch[0])
					nodeid = namematch[1]

					# If type is deleted in local conf we create a dummy type
					# just for deleting the node in cloud
					if not type:
						type = Type(namematch[0])
						self.typelist.add_type(type)

					self.nodelist.add_node(type, deleted=True, instance=instance, nodeid=nodeid)
	
	# Entrypoint for all commands
	def run(self, types):
		for type in types:
			# Override with global values
			type.override(self.type)
			
			if type.validate():
				self.typelist.add_type(type)
		
		# Execute command
		if len(sys.argv) > 1:
			# Check if it's a valid command
			if sys.argv[1] in self.cmds:
				self.read_manifest()
				
				# Execute requested command
				eval('self.%s()' % sys.argv[1])
			else:
				self.help()
		else:
			self.help()
	
	# Print all commands
	def help(self):
		print 'Commands: %s' % self.cmds
		
	def pretty_print(self, node):
		status = 'ok'
		
		if node.deleted:
			status = 'del'
		elif not node.created:
			status = 'new'
		if node.changed:
			status = 'chg'

		if node.type.type:
			type = node.type
		else:
			node.type.type = 'unknown'

		print ' %s %s %s' % (status.ljust(6), node.name.ljust(10), node.type.type.ljust(10))
	
	# List configuration and cloud nodes
	def status(self):
		if self.nodelist.needsync():
			print '[ %s ] [ sync needed ]' % self.name
		else:
			print '[ %s ]' % self.name

		if len(self.nodelist.nodes):
			for node in self.nodelist.nodes:
				self.pretty_print(node)
		else:
			print ' no nodes configured'
	
	def sync(self):
		# Make copy of list
		nodes = list(self.nodelist.nodes)
		
		# Mark changed nodes as deleted and add new ones
		for node in nodes:
			if not node.deleted and node.changed:
				node.deleted = True
				self.nodelist.add_node(node.type, nodeid=node.id)
		
		# Create new nodes
		for node in self.nodelist.nodes:
			if not node.created and not node.deleted:
				try:
					node.create()
				except BaseException, e:
					print e
					print 'Error: aborting sync'
					sys.exit(1)

		for node in self.nodelist.nodes:
			if not node.created and not node.deleted:
				node.waitup()

				if node.type.bootstrap:
					try:
						node.bootstrap(node.type.bootstrap)
					except BaseException, e:
						print e
						print 'Error: failed to bootstrap %s' % node.name
		
		# Delete nodes we have marked to delete
		for node in self.nodelist.nodes:
			if node.deleted:
				node.destroy()
		
		return
