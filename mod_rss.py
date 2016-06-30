import feedparser
import re
from HTMLParser import HTMLParser
from lxml import html
class rss:
	@staticmethod
	def read(url):
		try:
				feed = feedparser.parse(url);
		except Exception,e:
			print "[!][RSS] failed to load feed",url
			return dict();
		return feed

	@staticmethod
	def fromHTML(input):
		parser = HTMLParser()
		return parser.unescape(re.sub('<[^<]+?>', '', input))

	@staticmethod
	def HTMLimg(input):
		parser = html.fromstring(input)
		return parser.xpath('//img/@src')

	