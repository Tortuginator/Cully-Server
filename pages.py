#Import
from datetime import datetime
from datetime import timedelta
import os
import sys
import json
import linecache
import logging
from os import listdir
from operator import attrgetter
from os.path import isfile, join
import mod_calendar
import mod_rss
import urllib2
import threading
global Calendars
Calendars = list();

global UpdateCalT
UpdateCalT = datetime.now()

global font
font = "Open Sans";#"MS-Comic sans" not allowed to be used "Open sans" recommanded
global ticker_storage
global ticker_timer
global ticker_interval
global ticker_current
ticker_storage = "loading"
ticker_timer = datetime.now()
ticker_interval = 6
ticker_current = 0
global ItemStorage
ItemStorage = dict()

def UpdateCalendar(link):
	returncalendar = dict(); returncalendar["Today"] = list(); returncalendar["Tomorrow"] = list(); returncalendar["day3"] = list(); returncalendar["day4"] = list(); returncalendar["day5"] = list();
	try:
		output = urllib2.urlopen(link, timeout=4).read()
		finalcalendar = mod_calendar.calendar.StrToArr(output);
	except Exception,e:
		print "[!][CRITICAL] Unexpected error:", sys.exc_info()
		logging.exception("", exc_info=True)
		return returncalendar
		
	morning = datetime.now()
	morning -= timedelta(hours = morning.hour, minutes = morning.minute, seconds = morning.second, microseconds =  morning.microsecond)
	for i in finalcalendar:
		if not "DtStart" in i:
			break
		d = (i["DtStart"]-morning).days
		if d == 0:
			returncalendar["Today"].append(i)
		if d == 1:
			returncalendar["Tomorrow"].append(i)
		if d == 2:
			returncalendar["day3"].append(i)
		if d == 3:
			returncalendar["day4"].append(i)
		if d == 4:
			returncalendar["day5"].append(i)
	returncalendar['Tomorrow'] = sorted(returncalendar['Tomorrow'], key=lambda k: k['DtStart'])
	returncalendar['Today'] = sorted(returncalendar['Today'], key=lambda k: k['DtStart'])
	returncalendar['day3'] = sorted(returncalendar['day3'], key=lambda k: k['DtStart'])
	returncalendar['day4'] = sorted(returncalendar['day4'], key=lambda k: k['DtStart'])
	returncalendar['day5'] = sorted(returncalendar['day5'], key=lambda k: k['DtStart'])
	return returncalendar;

#Functions
def PrintError(Address, Content, ID):
	ErrorImage = "error.jpg";
	ErrorBackground = "#f3f4f4";
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-color:' + ErrorBackground + ';"><img src="' + Address + '' + ErrorImage + '" style=" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintFullframeImage(Address, Content, ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;width:100%;height:100%;background-color:black;"><img style="position: absolute;top: 0;bottom: 0;left: 0;right: 0;width: 100%;margin: auto;" src="' + Address + 'img/items/' + Content + '">'

def PrintCostumHTML(Address, Content, ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;">\n%s\n' % (Content)

def PrintCenteredImage(Address, Content, ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-color:black;"><img src="' + Address + 'img/items/' + Content + '" style =" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintYoutube(Address, Content, ID):
	return "<body style = 'font-family:" + font +"!important;margin:0px;padding:0px;background-color:black;'><iframe id='playerId' type='text/html' width='100%' height='100%' src='http://www.youtube.com/embed/" + Content + "?enablejsapi=1&rel=0&playsinline=0&autoplay=1&html5=1' frameborder='0' allowfullscreen>";

def PrintCalendar(Address, Content, ID):
	global UpdateCalT
	global Calendars
	if datetime.now() > UpdateCalT:
		UpdateCalT = datetime.now() + timedelta(minutes = 180);
		Calendars = [];

	if not ID in Calendars:
		Calendars.append(ID);
		ItemStorage[ID]["items"] = UpdateCalendar(Content);
	if not "items" in ItemStorage[ID]:
		ItemStorage[ID]["items"] = UpdateCalendar(Content);

	output = '<body style="font-family:' + font +'!important;margin:0px;padding:0px;background-color:#008742;"><center><p style="margin:0px;margin-bottom:30px;margin-top:60px;width:100%;font-size:96px;color:white;font-weight:700;">Upcoming events</p></center>';
	if len(ItemStorage[ID]["items"]["Today"]) != 0:
		output += '<div style="background-color:white;width:900px;padding-left:50px;padding-bottom:15px;margin: 0 auto;"><p style="color:#008742;margin-bottom:20px;font-size:40px;font-weight:700;font-family:open sans;text-transform:uppercase;padding-bottom:0px;margin-bottom:0px;margin-top:30px;">TODAY</p>';
		for i in ItemStorage[ID]["items"]["Today"]:
			if "DtEnd" in i:
				EndItem = ' - ' + i["DtEnd"].strftime("%H:%M");
			else:
				EndItem = '<p color="gray" style="display:inline;color:gray;"> - 00:00</p>';
			output += '<div style="color:#008742;font-size:20px;font-weight:500;font-family:open sans!important;margin-top:5px;"><div style="background-color:gray;color:white;border-radius:3px;padding:1px 5px;display:inline-block;">' + i["DtStart"].strftime("%H:%M") + EndItem + '</div> ' + i["Summary"] +  '</div>';
		output += '</div>';

	if len(ItemStorage[ID]["items"]["Tomorrow"]) != 0:
		output +='<div style="background-color:white;width:900px;padding-left:50px;padding-bottom:15px;margin: 0 auto;"><p style="color:#008742;font-size:40px;font-weight:700;font-family:open sans;text-transform:uppercase;padding-bottom:0px;margin-bottom:0px;margin-top:30px;">' + (datetime.now() + timedelta(+1)).strftime('%A') + '</p>';
		for i in ItemStorage[ID]["items"]["Tomorrow"]:
			if "DtEnd" in i:
				EndItem = ' - ' + i["DtEnd"].strftime("%H:%M");
			else:
				EndItem = '<p color="gray" style="display:inline;color:gray;"> - 00:00</p>';
			output += '<div style="color:#008742;font-size:20px;font-weight:500;font-family:open sans!important;margin-top:5px;"><div style="background-color:gray;color:white;border-radius:3px;padding:1px 5px;display:inline-block;">' + i["DtStart"].strftime("%H:%M") + EndItem + '</div> ' + i["Summary"] +  '</div>';	
		output += '</div>';

	if len(ItemStorage[ID]["items"]["day3"]) != 0:
		output +='<div style="background-color:white;width:900px;padding-left:50px;padding-bottom:15px;margin: 0 auto;"><p style="color:#008742;font-size:40px;font-weight:700;font-family:open sans;text-transform:uppercase;padding-bottom:0px;margin-bottom:0px;margin-top:30px;">' + (datetime.now() + timedelta(+2)).strftime('%A') + '</p>';
		for i in ItemStorage[ID]["items"]["day3"]:
			if "DtEnd" in i:
				EndItem = ' - ' + i["DtEnd"].strftime("%H:%M");
			else:
				EndItem = '<p color="gray" style="display:inline;color:gray;"> - 00:00</p>';
			output += '<div style="color:#008742;font-size:20px;font-weight:500;font-family:open sans!important;margin-top:5px;"><div style="background-color:gray;color:white;border-radius:3px;padding:1px 5px;display:inline-block;">' + i["DtStart"].strftime("%H:%M") + EndItem + '</div> ' + i["Summary"] +  '</div>';	
		output += '</div>';

	if len(ItemStorage[ID]["items"]["day4"]) != 0:
		output +='<div style="background-color:white;width:900px;padding-left:50px;padding-bottom:15px;margin: 0 auto;"><p style="color:#008742;font-size:40px;font-weight:700;font-family:open sans;text-transform:uppercase;padding-bottom:0px;margin-bottom:0px;margin-top:30px;">' + (datetime.now() + timedelta(+3)).strftime('%A') + '</p>';
		for i in ItemStorage[ID]["items"]["day4"]:
			if "DtEnd" in i:
				EndItem = ' - ' + i["DtEnd"].strftime("%H:%M");
			else:
				EndItem = '<p color="gray" style="display:inline;color:gray;"> - 00:00</p>';
			output += '<div style="color:#008742;font-size:20px;font-weight:500;font-family:open sans!important;margin-top:5px;"><div style="background-color:gray;color:white;border-radius:3px;padding:1px 5px;display:inline-block;">' + i["DtStart"].strftime("%H:%M") + EndItem + '</div> ' + i["Summary"] +  '</div>';	
		output += '</div>';

	if len(ItemStorage[ID]["items"]["day5"]) != 0:
		output +='<div style="background-color:white;width:900px;padding-left:50px;padding-bottom:15px;margin: 0 auto;"><p style="color:#008742;font-size:40px;font-weight:700;font-family:open sans;text-transform:uppercase;padding-bottom:0px;margin-bottom:0px;margin-top:30px;">' + (datetime.now() + timedelta(+4)).strftime('%A') + '</p>';
		for i in ItemStorage[ID]["items"]["day5"]:
			if "DtEnd" in i:
				EndItem = ' - ' + i["DtEnd"].strftime("%H:%M");
			else:
				EndItem = '<p color="gray" style="display:inline;color:gray;"> - 00:00</p>';
			output += '<div style="color:#008742;font-size:20px;font-weight:500;font-family:open sans!important;margin-top:5px;"><div style="background-color:gray;color:white;border-radius:3px;padding:1px 5px;display:inline-block;">' + i["DtStart"].strftime("%H:%M") + EndItem + '</div> ' + i["Summary"] +  '</div>';	
		output += '</div>';
	return output;

def PrintSlideshowImage(Address, Content, ID):
	SlideshowFrameTime = int(Content.split(";")[1])
	StorageLocation = lConfig["Server"]["Storage"] +  "\\slideshows\\" + Content.split(";")[0]

	if os.path.isdir(StorageLocation):
		files = [f for f in listdir(StorageLocation) if isfile(join(StorageLocation, f))];

		#Calculate Current item:
		if not "date" in ItemStorage[ID]:
			ItemStorage[ID]["date"] = datetime.now();

		now = datetime.now()
		delta = now - ItemStorage[ID]["date"]
		TimeDifference = int(delta.total_seconds())
		TimeUnits = TimeDifference%(SlideshowFrameTime*len(files))	#Remove Fully Passed frame cycles
		TimeUnits = TimeUnits - (TimeUnits%SlideshowFrameTime)		#Remove the current time in frame
		TimeUnits = TimeUnits / SlideshowFrameTime					#Convert the full seconds to the Frame ID

	else:
		logging.error("Failed to load Slideshow Image var = " + StorageLocation);
		return None
	return '<body style = "font-family:' + font +'!important;background-color:black;margin:0px;padding:0px;"><img src="' + Address + 'img/slideshows/' + Content.split(";")[0] + '/' + files[TimeUnits] + '" style ="max-height: 100%;max-width: 100%;position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintFullIFrame(Address,Content,ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;">\n<iframe src="' + Content + '" style="position:fixed; top:0px; left:0px; bottom:0px; right:0px; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999998;">Your browser doesn\'t support iframes</iframe>';

def PrintRoomCalendar(Address,Content,ID):
	return '<body style = "font-family:Open Sans!important;margin:0px;padding:0px;background-color:white;"><!--CALENDARINIT--><div id="roomname"><p id="text">' + Content.split("|")[0] + '</p></div><div id="roomcal"></div><lnk id="b64ical" style="display:none;">' + Content.split("|")[1] + '</lnk>';

def PrintRSS(Address,Content,ID):
	return "";



#DO NOT EDIT
#Backbone functions for server call and input
def GetBackbone(innerHTML, debug,ticker = True,type = -1):
	if (innerHTML == None): innerHTML = "";
	typefaceCSS = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,300" rel="stylesheet" type="text/css"><link rel="stylesheet" type="text/css" href="../assets/breakingNews.css"><link rel="stylesheet" href="../assets/fullcalendar.min.css" /><link rel="stylesheet" href="../assets/calendar.css" />';
	htmlCSS = "font-family: '" + font + "', sans-serif !important;"
	if debug == True:
		debugHTML = '<div style="background-color:black;color:white;position:fixed;top:50px;left:50px;padding:5px;text-align:center;font-size:25;">Developermode <p style="display:inline;color:green;">Active</p> | Connection <p style="display:inline;color:green;">Active</p></div>\n<div id="debug_lower" style="background-color:black;color:white;position:fixed;bottom:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>\n<div id="debug_upper" style="background-color:black;color:white;position:fixed;top:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>\n<div id="special_frame" style=""></div>';
	else:
		debugHTML = '<div id="debug_lower" style="display:none;"></div>\n<div id="debug_upper" style="display:none;"></div>\n<div id="special_frame" style=""></div>';
	if ticker is True and type != 11:
		ticker = """<div id="bbcticker" style='z-index:9999;width: 100%;position:fixed;bottom:0px;left:0px;'><div id="bn1" style="padding:0; margin:0; font-family:Open Sans; font-size:30px;" class="breakingNews bn-bordernone bn-red"><div class="bn-title" style="width: auto;"><h2 style="display: inline-block;">BBC News</h2><span></span></div><ul style=""><li style="display: block; width: 100%;"><a href="" target="_blank">""" + GetTicker() + """</a></li></ul></div></div>""";
	else:
		ticker = "";
	return typefaceCSS + "\n" + "<html style=\"" + htmlCSS + "\">\n" + innerHTML + "\n</body>\n" + ticker + "\n" + debugHTML +  "\n</html>";

def GetPage(Type, Content, ID, Configuration):
	try:
		debug = Configuration["Server"]["Debug"]
		global lConfig
		lConfig = Configuration

		functions = {'0': PrintError, '2': PrintCostumHTML, '3': PrintCostumHTML, '4': PrintFullframeImage, '5': PrintCenteredImage, '6': PrintSlideshowImage, '7': PrintCalendar, '8': PrintFullIFrame, '9': PrintYoutube,'10':PrintRSS,'11':PrintRoomCalendar};#add your customized functions here 'ID',FuntionName || '0' is predefined error
		Type = int(Type);
		if not ID in ItemStorage:
			ItemStorage[ID] = dict();

		if str(Type) in functions:
			return GetBackbone(functions[str(Type)](Configuration["ADDR"], Content, ID),debug, type = int(Type));
		else:
			return GetBackbone(functions['0'](Configuration["ADDR"], Content, ID), debug, type = int(Type))
	except Exception,e:
		print "[!][CRITICAL] Unexpected error:", sys.exc_info()
		logging.exception("", exc_info=True)

def GetTicker():
	url = "http://feeds.bbci.co.uk/news/rss.xml?edition=int";
	limit = 15;#max number of newsitems displayed in one cycle
	global ticker_timer
	global ticker_current
	global ticker_storage
	global ticker_interval

	if datetime.now() > ticker_timer:
		ticker_timer = datetime.now() + timedelta(seconds = ticker_interval);
		if ticker_storage == "loading":
			t = threading.Thread(target=ThreadGetRSS,args=(url,)).start()
			return "[LOADING FEED]"
		if len(ticker_storage)-1 == ticker_current:
			ticker_current = -1;
			t = threading.Thread(target=ThreadGetRSS,args=(url,)).start()
		ticker_current +=1;
	return ticker_storage[ticker_current];

def ThreadGetRSS(url):
	print "[*][TICKER] Loading RSS feed"
	global ticker_storage
	data = mod_rss.rss.read(url);
	ticker = list()
	for i in data.entries:
		if len(ticker) < 15:
			ticker.append(i.title)
	ticker_storage = ticker;
