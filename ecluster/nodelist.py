from ecluster.node import Node

class NodeList():
	def __init__(self, name, provider):
		self.name = name
		self.nodes = []
		self.provider = provider
	
	# Give next index number for type
	def num_type(self, type, deleted=False):
		num = 1
		
		for node in self.nodes:
			if deleted:
				# Count only deleted nodes
				if node.type == type and node.deleted:
					num += 1
			else:
				if node.type == type and not node.deleted:
					num += 1
		
		return num
	
	def add_node(self, type, deleted=False, nodeid=None, instance=None):
		if not nodeid:
			nodeid = self.num_type(type)

		node = Node(type, nodeid, self.provider, self.name)

		# We have some nodes to be deleted
		if self.num_type(type, deleted=True) > 1:
			node.replace = True
		
		if instance:
			node.instance = instance
		else:
			node.locate_in_cloud()

		node.deleted = deleted
		
		self.nodes += [node]

	def get_node_names(self):
		ret = []
		for node in self.nodes:
			ret += [str(node.name)]
		return ret
		
	def get_instance_ids(self):
		ret = []
		for node in self.nodes:
			if node.instance:
				ret += [str(node.instance.id)]
		return ret

	def needsync(self):
		for node in self.nodes:
			if node.changed:
				return True
			if node.deleted:
				return True
			if not node.created:
				return True
		return False
		
	def instance_in_list(self, instance):
		local_ids = self.get_instance_ids()
		if not instance.id in local_ids:
			return False

		return True
