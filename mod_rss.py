import feedparser

class rss:
	def __init__(self):
		self.data = dict();
		
	def read(self,url):
		try:
				feed = feedparser.parse(url);
		except Exception,e:
			print "[!][RSS] failed to load feed",url
			return dict();
		return feed

	def Render(self,url):

	