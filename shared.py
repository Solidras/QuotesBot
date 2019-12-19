async def load_characters():
	c = {}
	f = open('characters.txt', 'r')
	for line in f.readlines():
		character,url = line.split(',')
		c[character] = url
	f.close()
	return c