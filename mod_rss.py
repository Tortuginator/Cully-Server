import feedparser

class rss:
	@staticmethod
	def read(url):
		try:
				feed = feedparser.parse(url);
		except Exception,e:
			print "[!][RSS] failed to load feed",url
			return dict();
		return feed


	