def load(provider, name, **kargs):
	try:
		if provider == 'ec2':
			from ec2 import Provider
			return Provider(name, **kargs)
	
		print 'Error: no such provider: %s' % provider
		return False
	except BaseException, e:
		print e