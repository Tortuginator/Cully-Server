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

API_KEY = "781CF461BB6606AD28A78E343E0E41767E8B7FEDB4F45556";#ONLY for Internalusage
global gPSI
gPSI = {"PSI":-1,"time":"N/A"}

class FrameTimetable:
	@staticmethod
	def GetCurrentFrame(content):
		content = json.loads(content);

		#Get Each date
		d  = datetime.now()
		d -= dt.timedelta(hours = d.hour,minutes = d.minute, seconds = d.second, microseconds =  d.microsecond)
		n = 0;
		for i in content:
			if not "start" in i or not "stop" in i:
				if n==0:
					n = i["content"];
					break;
				else:
					return [2,"WRONG CONTENT FORMAT"]
			#Start
			strStart = i["start"].split("/")
			diffday = FrameTimetable.dayStrToID(strStart[0]) - d.weekday();
			dayStart = d + dt.timedelta((7 + diffday) % 7)
			tmp_delta = dt.timedelta(minutes = int(strStart[1].split(":")[1]),hours = int(strStart[1].split(":")[0]));
			absoluteStart = dayStart + tmp_delta

			#Stop
			strStop = i["stop"];
			tmp_delta = dt.timedelta(minutes = int(strStop.split(":")[1]),hours = int(strStop.split(":")[0]));
			absoluteStop = d + tmp_delta;

			#Check
			if (datetime.now() >= absoluteStart) and (datetime.now() <= absoluteStop):
				#Found Active time
				return [0,i["content"]];

		#OUT OF LOOP
		if n!=0:
			return [0,n]
		else:
			return [1,"NO ACTIVE OR NORMAL CONTENT FOUND"]

	@staticmethod		
	def dayStrToID(str):
		if str == "Monday":
			ID = 0;
		elif str == "Tuesday":
			ID = 1;
		elif str == "Wednesday":
			ID = 2;
		elif str == "Thursday":
			ID = 3;
		elif str == "Friday":
			ID = 4;
		elif str == "Saturday":
			ID = 5;
		elif str == "Sunday":
			ID = 6;
		else:
			return -1;
		return ID;

class FrameTimer:
	@staticmethod
	def GetFrameIndex(Frames,StartTime):
		#Get Time Difference from START to NOW
		delta = datetime.now() - StartTime
		TimeDifference = int(delta.total_seconds())
		print FrameTimer.GetCycleTime(Frames)
		print TimeDifference
		#Remove Passed Cycles
		inCycleTime = TimeDifference%(FrameTimer.GetCycleTime(Frames))

		#Return Item to the corresponding time
		return FrameTimer.GetItemByTime(Frames,inCycleTime)

	@staticmethod
	def GetItemByTime(Frames,TargetTime):
		tmpTime = 0
		for a,b in enumerate(Frames):
			tmpTime += int(b[1])
			if tmpTime > TargetTime:#when sum of time is larger than the target time
				return int(b[0])

	@staticmethod
	def GetCycleTime(Frames):
		tmp = 0; 
		for FrameID,time in enumerate(Frames):
			tmp +=int(time[1])
		return tmp

class FrameContent:
	@staticmethod
	def GenerateFrame(Itype,Icontent,Iname,Iid,Configuration,Ext_Command):
		dPSI = FrameContent.ReadPSI()
		try:
			psi_value = int(dPSI["PSI"]);
			psi_time = str(dPSI["time"]);
		except Exception,e:
			psi_value = int(-1);
			psi_time = "N/A"

		produced = {"content":FrameContent.HTMLframe(Itype,Icontent,Iid,Configuration),"id":Iid,"type":Itype,"name":Iname,"enabled":"1","PSI":{"Int":psi_value,"time":psi_time}}
		if Ext_Command != "" and Configuration["Server"]["Command"] == True and Ext_Command != "NULL":#decide if there is to be a command included
			produced["command"] = Ext_Command
		return produced

	@staticmethod
	def InternalError(Detail = None):
		if Detail == None:Detail = "Undefined";
		logging.critical("Sending Internal Error - " + Detail);
		return {"content":'<div style="position: absolute;top: 50%;left: 50%;width:300px;height:500px;transform: translate(-50%, -50%);border-radius:5px;background-color:red"><div style="margin: 0 auto;border-radius:50%;border:10px solid white;width:150px;height:150px;margin-top:15px;"><div style="background-color:white;height:20px;width:100px;margin: 0 auto;margin-top:65px;"></div></div><center style="color:white;"><h1 style="color:white;">Internal Error</h1></center></div>',"id":-1,"type":0,"name":"Error","debug-detail":Detail}

	@staticmethod
	def InternalVisibleError(Detail = None):
		if Detail ==None:Detail = "Undefined";
		logging.critical("Sending Internal Error - " + Detail);
		return {"content":'<div style="position: absolute;top: 50%;left: 50%;width:300px;height:500px;transform: translate(-50%, -50%);border-radius:5px;background-color:red"><div style="margin: 0 auto;border-radius:50%;border:10px solid white;width:150px;height:150px;margin-top:15px;"><div style="background-color:white;height:20px;width:100px;margin: 0 auto;margin-top:65px;"></div></div><center style="color:white;"><h1 style="color:white;">Internal Error</h1><p style="width:80%;margin:0 auto;color:white;">' + Detail + '</p></center></div>',"id":-1,"type":0,"name":"Error","debug-detail":Detail}

	@staticmethod
	def HTMLframe(Itype,Icontent,ID,Configuration):
		return pages.GetPage(Itype,Icontent,ID,Configuration)

	@staticmethod
	def ReadPSI():
		try:
			dPSI = gPSI
		except Exception,e:
			raise
			logging.error(e);
			dPSI = {"PSI":-1,"time":0}
			print "FAILED to read and/or decode the PSI file/value"
		return dPSI
class validate:
	@staticmethod
	def pushToArry(input):#device,current,content,current_time,next_time,current_sub,push_command
		ret = dict();
		ret["name"] = input[0]
		ret["content"] = input[2]
		ret["command"] = input[6]
		return ret;

	@staticmethod
	def content(c):
		if ":" not in c:
			return [1,"WRONG FORMAT"]
		c = c.split("|");
		#Correct Split
		t = list();
		for i in c:
			if ":" in i:
				s = i.split(":");
				if s[0] != "" and s[1] != "":t.append([s[0],s[1]]);

		#if only one item exists
		if len(t) == 1:
			t.append(t[0]);
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
			return {"psi":data["channel"]["item"]["region"][1]["record"]["reading"][0]["@value"],"date":data["channel"]["item"]["region"][1]["record"]["@timestamp"]};
		except Exception,e:
			print "[!][PSI] a error occured:",str(e)
			logging.error(e);
			return {"psi":-1,"date":0}

	@staticmethod
	def PSIAutoUpdate():
		try:
			pNow = psi.Get();
			pLast = pNow["psi"];
			dLast = pNow["date"];
			psi.Write(pLast);
			print "[+][PSI] Updated @",pLast,"24-hrs"

			tDouble  = dt.datetime.now()
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
						print "[+][PSI] Updated @",t_PSI,"24-hrs"
						print "[+][PSI] Leaving PRE routine"
						break;

			while 1:
				tNow  = dt.datetime.now()
				tNow -= dt.timedelta(minutes = tNow.minute, seconds = tNow.second, microseconds =  tNow.microsecond)

				tNow += dt.timedelta(hours = 0,minutes = 59,seconds = 30)#prevent that the timer will not be triggered in time and as result will not update (1hr cycle)
				print "[+][PSI] retrieve @ ",tNow.strftime("%H:%M")
				while dt.datetime.now() < tNow:
					time.sleep(20);#Check every 20 seconds

				if dt.datetime.now() >= tNow:
					pNow = psi.Get();
					if pNow["psi"] == pLast:
						if pNow["date"] == dLast:
							while 1:
								pTPY= psi.Get();
								if pTPY["date"] != dLast:
									dLast = pTPY["date"];
									pLast = pTPY["psi"];
									logging.info(pTPY);
									break;#exit unlimited loop
								else:
									print "[+][PSI] Forcing update loop"
									time.sleep(30)#2 Minutes loop (30) seconds
					else:
						pLast = pNow;
				psi.Write(pLast);
				print "[+][PSI] Updated @",pLast,"24-hrs"
				logging.info("New PSI value:" + pLast);
		except Exception,e:
			logging.error(e);
			print e;
			raise;

	@staticmethod
	def Write(psi):
		global gPSI
		gPSI = {"PSI":psi,"time":dt.datetime.now().strftime("%H:%M")}
