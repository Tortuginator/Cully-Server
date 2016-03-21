import urllib2
import xmltodict
import math
import sys
import json
import time
import datetime as dt
API_KEY = "781CF461BB6606AD28A78E343E0E41767E8B7FEDB4F45556";#ONLY for Internalusage

#SINGAPORE PSI LEVELS
def GetDataAirQ():
	try:
		if API_KEY == None: return None;
		file = urllib2.urlopen('http://www.nea.gov.sg/api/WebAPI?dataset=psi_update&keyref=' + API_KEY)
		data = file.read()
		file.close()
		return xmltodict.parse(data);
	except Exception, e:
		return None;

def GetPSI():
	try:
		data = GetDataAirQ();
		if data == None: raise Exception("Data could not be decoded/recived")
		return {"psi":data["channel"]["item"]["region"][1]["record"]["reading"][0]["@value"],"date":data["channel"]["item"]["region"][1]["record"]["@timestamp"]};
	except Exception,e:
		print "[!][PSI] a error occured:",e.strerror
		return {"psi":"N/A","date":"N/A"}

def PSIAutoUpdate(location):
	pNow = GetPSI();
	pLast = pNow["psi"];
	dLast = pNow["date"];
	PSIWrite(location,pLast);
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
				t_PSI = GetPSI()
				PSIWrite(location,t_PSI["psi"]);
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
			pNow = GetPSI();
			if pNow["psi"] == pLast:
				if pNow["date"] == dLast:
					while 1:
						pTPY= GetPSI();
						if pTPY["date"] != dLast:
							dLast = pTPY["date"];
							pLast = pTPY["psi"];
							break;#exit unlimited loop
						else:
							print "[+][PSI] Forcing update loop"
							time.sleep(30)#2 Minutes loop (30) seconds
			else:
				pLast = pNow;
		PSIWrite(location,pLast);
		print "[+][PSI] Updated @",pLast,"24-hrs"

def PSIWrite(location,psi):
	input = {"PSI":psi,"time":dt.datetime.now().strftime("%H:%M")}
	with open(location, 'w') as the_file:
		the_file.write(json.dumps(input))