from ecluster.type import Type

class TypeList():
	def __init__(self):
		self.types = []
	
	def add_type(self, type):
		self.types += [type]
		
	def get_type_by_name(self, str):
		for type in self.types:
			if type.name == str:
				return type
		return None