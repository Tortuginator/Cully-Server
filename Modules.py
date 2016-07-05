from datetime import datetime
import pages
import json
import urllib2
import xmltodict
import math
import sys
import json
import time
import logging
import datetime as dt
import mod_calendar
import threading
import HerokuReporter

API_KEY = "781CF461BB6606AD28A78E343E0E41767E8B7FEDB4F45556";#ONLY for Internalusage
global gPSI
gPSI = {"PSI":-1, "time":"N/A"}

class CalendarUpdater:
	def __init__(self):
		self.data = dict();
		self.updates = dict();

	def GetCalendar(self,url):
		if url in self.data:
			if dt.datetime.now() > self.updates[url]:
				self.updates[url] = dt.datetime.now() + dt.timedelta(minutes = 10)
				threading.Thread(target=self.UpdateCalendar,args=(url,)).start()
			return self.data[url];
		else:
			self.data[url] = json.dumps({});
			self.updates[url] = dt.datetime.now() + dt.timedelta(minutes = 10)
			threading.Thread(target=self.UpdateCalendar,args=(url,)).start()
			return self.data[url];

	def UpdateCalendar(self,url):
		try:
			logging.info(url)
			urlcontent = urllib2.urlopen(url, timeout=20).read()
		except Exception,e:
			print "[!][CALENDAR] Failed to download calendar data"
			self.data[url] = json.dumps({});
		self.data[url] = mod_calendar.calendar.ReformStr(urlcontent)
class FrameTimetable:
	@staticmethod
	def GetCurrentFrame(content):
		content = json.loads(content);

		#Get Each date
		d  = datetime.now()
		d -= dt.timedelta(hours = d.hour, minutes = d.minute, seconds = d.second, microseconds =  d.microsecond)
		n = 0;
		for i in content:
			if not "start" in i or not "stop" in i:
				if n == 0:
					if not "content" in i:continue;
					n = i
					continue
			#Start
			if not "/" in i["start"]:
				raise Exception('GetCurrentFrame failed to read time')
			if not ":" in i["start"] and not ":" in i["stop"]:
				raise Exception('GetCurrentFrame invalid time format')
			strStart = i["start"].split("/")
			today = FrameTimetable.dayStrToID(strStart[0])
			if today == -1:raise Exception('GetCurrentFrame => dayStrToID failed to determine the id of the day');
			diffday = today - d.weekday()
			dayStart = d + dt.timedelta((7 + diffday) % 7)
			tmp_delta = dt.timedelta(minutes = int(strStart[1].split(":")[1]), hours = int(strStart[1].split(":")[0]))
			absoluteStart = dayStart + tmp_delta

			#Stop
			strStop = i["stop"];
			tmp_delta = dt.timedelta(minutes = int(strStop.split(":")[1]), hours = int(strStop.split(":")[0]))
			absoluteStop = d + tmp_delta

			#Check
			if (datetime.now() >= absoluteStart) and (datetime.now() <= absoluteStop):
				#Found Active time
				if "ticker" in i:
					return [i["content"],i["ticker"]]
				return [i["content"],0]

		#OUT OF LOOP
		if n!=0:
			if "ticker" in n:
				return [n["content"],n["ticker"]]
			return [n["content"],0]
		else:
			raise Exception('GetCurrentFrame has found no active or standart content preset')

	@staticmethod		
	def dayStrToID(str):
		if str == "Monday":
			ID = 0
		elif str == "Tuesday":
			ID = 1
		elif str == "Wednesday":
			ID = 2
		elif str == "Thursday":
			ID = 3
		elif str == "Friday":
			ID = 4
		elif str == "Saturday":
			ID = 5
		elif str == "Sunday":
			ID = 6
		else:
			return -1
		return ID

class FrameTimer:
	@staticmethod
	def GetFrameIndex(Frames, StartTime):
		delta = datetime.now() - StartTime
		TimeDifference = int(delta.total_seconds())
		inCycleTime = TimeDifference%(FrameTimer.GetCycleTime(Frames))
		return FrameTimer.GetItemByTime(Frames, inCycleTime)

	@staticmethod
	def GetItemByTime(Frames, TargetTime):
		tmpTime = 0
		for a, b in enumerate(Frames):
			tmpTime += int(b[1])
			if tmpTime > TargetTime:#when sum of time is larger than the target time
				return int(b[0])

	@staticmethod
	def GetCycleTime(Frames):
		tmp = 0; 
		for FrameID, time in enumerate(Frames):
			tmp +=int(time[1])
		return tmp

class FrameContent:
	@staticmethod
	def GenerateFrame(Itype, Icontent, Iname, Iid, Configuration, Ext_Command,ticker = False):
		dPSI = FrameContent.ReadPSI()
		try:
			psi_value = int(dPSI["PSI"])
			psi_time = str(dPSI["time"])
		except Exception, e:
			psi_value = int(-1);
			psi_time = "N/A"

		produced = {"content":FrameContent.HTMLframe(Itype, Icontent, Iid, Configuration,ticker = ticker), "id": Iid, "type": Itype, "name": Iname, "enabled": "1","ticker":1, "PSI":{"Int": psi_value, "time": psi_time}}
		if Ext_Command != "" and Configuration["Server"]["Command"] == True and Ext_Command != "NULL":#decide if there is to be a command included
			produced["command"] = Ext_Command
		return produced

	@staticmethod
	def InternalError(Detail = None):
		if Detail == None:Detail = "Undefined";
		logging.critical("Sending Internal Error - " + Detail)
		return {"content":'<div style="position: absolute;top: 50%;left: 50%;width:300px;height:500px;transform: translate(-50%, -50%);border-radius:5px;background-color:red"><div style="margin: 0 auto;border-radius:50%;border:10px solid white;width:150px;height:150px;margin-top:15px;"><div style="background-color:white;height:20px;width:100px;margin: 0 auto;margin-top:65px;"></div></div><center style="color:white;"><h1 style="color:white;">Internal Error</h1></center></div>',"id":-1,"type":0,"name":"Error","debug-detail":Detail}

	@staticmethod
	def InternalVisibleError(Detail = None):
		if Detail == None:Detail = "Undefined";
		logging.critical("Sending Internal Error - " + Detail)
		return {"content":'<div style="position: absolute;top: 50%;left: 50%;width:300px;height:500px;transform: translate(-50%, -50%);border-radius:5px;background-color:red"><div style="margin: 0 auto;border-radius:50%;border:10px solid white;width:150px;height:150px;margin-top:15px;"><div style="background-color:white;height:20px;width:100px;margin: 0 auto;margin-top:65px;"></div></div><center style="color:white;"><h1 style="color:white;">Internal Error</h1><p style="width:80%;margin:0 auto;color:white;">' + Detail + '</p></center></div>',"id":-1,"type":0,"name":"Error","debug-detail":Detail}

	@staticmethod
	def HTMLframe(Itype, Icontent, ID, Configuration,ticker = False):
		return pages.GetPage(Itype, Icontent, ID, Configuration,ticker = ticker)

	@staticmethod
	def ReadPSI():
		try:
			dPSI = gPSI
		except Exception, e:
			logging.error(e)
			dPSI = {"PSI": -1, "time": 0}
			print "[!][WARNING] FAILED to read and/or decode the PSI values"
		return dPSI

class validate:
	@staticmethod
	def pushToArry(input):#device, current, content, current_time, next_time, current_sub, push_command
		ret = dict();
		ret["name"] = input[0]
		ret["content"] = input[2]
		ret["command"] = input[6]
		return ret;

	@staticmethod
	def content(c):
		if ":" not in c: raise Exception('content() the content given does not fit the requirements: ":"', c);
		if "|" not in c and len(c) >= 4:
			c =  "|" + c + "|"

		#Correct Split
		t = list();
		for i in c.split("|"):
			if ":" in i:
				s = i.split(":")
				if s[0] != "" and s[1] != "":t.append([s[0], s[1]])

		#if only one item exists
		if len(t) == 1: t.append(t[0]);
		return t
class psi:
	#SINGAPORE PSI LEVELS
	@staticmethod
	def GetDataAirQ():
		try:
			logging.info("Updating PSI");
			if API_KEY == None: return None;
			file = urllib2.urlopen('http://www.nea.gov.sg/api/WebAPI?dataset=psi_update&keyref=' + API_KEY)
			data = file.read()
			file.close()
			return xmltodict.parse(data);
		except Exception, e:
			logging.error(e);
			return None;

	@staticmethod
	def Get():
		try:
			data = psi.GetDataAirQ();
			if data == None: raise Exception("Data could not be decoded/recived")
			return {"psi":data["channel"]["item"]["region"][1]["record"]["reading"][0]["@value"], "date":data["channel"]["item"]["region"][1]["record"]["@timestamp"]}
		except Exception, e:
			print "[!][WARNING][PSI] Unexpected error:", sys.exc_info()[0]
			logging.error(e);
			return {"psi":-1, "date":"N/A"}

	@staticmethod
	def PSIAutoUpdate():
		try:
			pNow = psi.Get();
			pLast = pNow["psi"];
			dLast = pNow["date"];
			psi.Write(pLast);
			print "[+][PSI] Updated @", pLast, "24-hrs"

			tDouble = dt.datetime.now()
			tDouble -= dt.timedelta(minutes = tDouble.minute, seconds = tDouble.second, microseconds =  tDouble.microsecond)

			tPrev = dt.datetime.now();
			tPrev -= dt.timedelta(minutes = 11)

			if tDouble >= tPrev:
				print "[+][PSI] Entering PRE routine"
				tDouble += dt.timedelta(minutes = 11)
				while 1:
					time.sleep(20);#Check every 20 seconds
					if tDouble <= dt.datetime.now():
						t_PSI = psi.Get()
						logging.info(t_PSI);
						psi.Write(t_PSI["psi"]);
						print "[+][PSI] Leaving PRE routine"
						break

			while 1:
				tNow = dt.datetime.now()
				tNow -= dt.timedelta(minutes = tNow.minute, seconds = tNow.second, microseconds =  tNow.microsecond)

				tNow += dt.timedelta(hours = 0, minutes = 59, seconds = 30)#prevent that the timer will not be triggered in time and as result will not update (1hr cycle)
				print "[+][PSI] retrieve @", tNow.strftime("%H:%M")
				while dt.datetime.now() < tNow:
					time.sleep(20);

				if dt.datetime.now() >= tNow:
					pNow = psi.Get();
					if pNow["psi"] == pLast:
						if pNow["date"] == dLast:
							while 1:
								pTPY = psi.Get()
								if pTPY["date"] != dLast:
									dLast = pTPY["date"]
									pLast = pTPY["psi"]
									logging.info(pTPY)
									break;#exit unlimited loop
								else:
									print "[+][PSI] Forcing update loop"
									time.sleep(30)#2 Minutes loop (30) seconds
					else:
						pLast = pNow;
						psi.Write(pLast);
						print "[+][PSI] Updated @", pLast, "24-hrs"
						logging.info("Updated PSI: " + pLast)
		except Exception, e:
			logging.error(e);
			HerokuReporter.report.do({}, "PSIAutoUpdate()",sys.exc_info())
			print "[!][CRITICAL][PSI] Unexpected error:", sys.exc_info()[0]

	@staticmethod
	def Write(psi):
		global gPSI
		gPSI = {"PSI":psi, "time":dt.datetime.now().strftime("%H:%M")}
