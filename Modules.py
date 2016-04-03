from datetime import datetime
import pages
import json
import urllib2
import xmltodict
import math
import sys
import json
import time
import datetime as dt

API_KEY = "781CF461BB6606AD28A78E343E0E41767E8B7FEDB4F45556";#ONLY for Internalusage
global gPSI
gPSI = {"PSI":-1,"time":0}

class FrameTimer:
	@staticmethod
	def GetFrameIndex(Frames,StartTime):
		#Get Time Difference from START to NOW
		now = datetime.now()
		delta = now - StartTime
		TimeDifference = int(delta.total_seconds())

		#Remove Passed Cycles
		inCycleTime = TimeDifference%(FrameTimer.GetCycleTime(Frames))
		
		#Only for Debug
		print FrameTimer.GetCycleTime(Frames),inCycleTime
		print "Corresponding item",FrameTimer.GetItemByTime(Frames,inCycleTime)
		
		#Return Item to the corresponding time
		return FrameTimer.GetItemByTime(Frames,inCycleTime)

	@staticmethod
	def GetItemByTime(Frames,TargetTime):
		tmpTime = 0
		for frameID,time in enumerate(Frames):
			tmpTime += int(time)
			if tmpTime > TargetTime:#when sum of time is larger than the target time
				return int(frameID)

	@staticmethod
	def GetCycleTime(Frames):
		tmp = 0; 
		for FrameID,time in enumerate(Frames):
			tmp +=int(time)
		return tmp

class FrameContent:
	@staticmethod
	def GenerateFrame(Itype,Icontent,Iname,Iid,Configuration,Ext_Command):
		dPSI = FrameContent.ReadPSI()
		produced = {"content":FrameContent.HTMLframe(Itype,Icontent,Iid,Configuration),"id":Iid,"type":Itype,"name":Iname,"PSI":{"Int":int(dPSI["PSI"]),"time":str(dPSI["time"])}}
		if Ext_Command != "" and Configuration["Server"]["Command"] == True and Ext_Command != "NULL":#decide if there is to be a command included
			produced["command"] = Ext_Command
		return produced

	@staticmethod
	def InternalError(Detail = None):
		return {"content":"<center><h1>Internal Server Error</h1></center>","id":-1,"type":0,"name":"Error","debug-detail":Detail}


	@staticmethod
	def HTMLframe(Itype,Icontent,ID,Configuration):
		return pages.GetPage(Itype,Icontent,ID,Configuration)

	@staticmethod
	def ReadPSI():
		try:
			print gPSI
			dPSI = gPSI
		except Exception,e:
			raise
			dPSI = {"PSI":-1,"time":0}
			print "FAILED to read and/or decode the PSI file/value"
		return dPSI

class psi:
	#SINGAPORE PSI LEVELS
	@staticmethod
	def GetDataAirQ():
		try:
			if API_KEY == None: return None;
			file = urllib2.urlopen('http://www.nea.gov.sg/api/WebAPI?dataset=psi_update&keyref=' + API_KEY)
			data = file.read()
			file.close()
			return xmltodict.parse(data);
		except Exception, e:
			return None;

	@staticmethod
	def Get():
		try:
			data = psi.GetDataAirQ();
			if data == None: raise Exception("Data could not be decoded/recived")
			return {"psi":data["channel"]["item"]["region"][1]["record"]["reading"][0]["@value"],"date":data["channel"]["item"]["region"][1]["record"]["@timestamp"]};
		except Exception,e:
			print "[!][PSI] a error occured:",e.strerror
			return {"psi":"N/A","date":"N/A"}

	@staticmethod
	def PSIAutoUpdate():
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
								break;#exit unlimited loop
							else:
								print "[+][PSI] Forcing update loop"
								time.sleep(30)#2 Minutes loop (30) seconds
				else:
					pLast = pNow;
			psi.Write(pLast);
			print "[+][PSI] Updated @",pLast,"24-hrs"

	@staticmethod
	def Write(psi):
		global gPSI
		gPSI = {"PSI":psi,"time":dt.datetime.now().strftime("%H:%M")}
