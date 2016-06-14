import feedparser

class rss:
	def read(url):
		feed = feedparser.parse(url);
		