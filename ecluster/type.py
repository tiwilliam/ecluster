class Type():
	def __init__(self, name):
		self.name = name
		self.nodes = 1
		self.image = None
		self.type = None
		self.keypair = None
		self.user = 'ec2-user'
		self.bootstrap = None
		self.groups = []
	
	def validate(self):
		if not self.name:
			print 'Error: No name specified, cannot create type: %s' % self.name
			return 0

		if not self.image:
			print 'Error: No image specified, cannot create type: %s' % self.name
			return 0
		
		if not self.type:
			print 'Error: No type specified, cannot create type: %s' % self.name
			return 0
		
		return 1
		
	def override(self, type):
		if not self.image:
			self.image = type.image
		
		if not self.type:
			self.type = type.type
			
		if not self.keypair:
			self.keypair = type.keypair

		if not self.bootstrap:
			self.bootstrap = type.bootstrap
			
		return 0
