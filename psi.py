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
		data = xmltodict.parse(data)
		return data;
	except Exception, e:
		return None;

def GetPSI():
	try:
		data = GetDataAirQ();
		if data == None: raise Exception("Data could not be decoded/recived")
		return {"psi":data["channel"]["item"]["region"][1]["record"]["reading"][0]["@value"],"date":data["channel"]["item"]["region"][1]["record"]["@timestamp"]};
	except Exception,e:
		return {"psi":"N/A","date":"N/A"}

def PSIAutoUpdate(location):
	pNow = GetPSI();
	pLast = pNow["psi"];
	dLast = pNow["date"];
	PSIWrite(location,pLast);
	while 1:
		tNow  = dt.datetime.now()
		tNow -= dt.timedelta(minutes = tNow.minute, seconds = tNow.second, microseconds =  tNow.microsecond)
		tNow += dt.timedelta(hours = 1,minutes = 1)
		print "[+][PSI-timer] retrieve PSI @ ",tNow.strftime("%H:%M")
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
							break;
						else:
							print "[+][PSI-timer] Forcing update loop"
							time.sleep(2*60)#2 Minutes loop (2*60)
			else:
				pLast = pNow;
		PSIWrite(location,pLast);
		print "[+][PSI-timer] Updated PSI"
def PSIWrite(location,psi):
	input = {"PSI":psi,"time":dt.datetime.now().strftime("%H:%M")}
	with open(location, 'w') as the_file:
		the_file.write(json.dumps(input))

