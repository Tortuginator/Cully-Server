import urllib2
import xmltodict
import math
import sys
import json
#SINGAPORE PSI LEVELS
API_KEY = sys.argv[1];

def GetDataAirQ():
    file = urllib2.urlopen('http://www.nea.gov.sg/api/WebAPI?dataset=psi_update&keyref=' + API_KEY)
    data = file.read()
    file.close()
    data = xmltodict.parse(data)
    return data;

def GetPSI(data):
	data = GetDataAirQ();
	return data["channel"]["item"]["region"][1]["record"]["reading"][0]["@value"];

#TAXI SYSTEM
def GetCoordinates(data):
	return data["geoJson"]["features"][0]["coordinates"];

def GetDataTaxi():
    #TCP client
	req = urllib2.Request("https://data.gov.sg/realtime-api/transport/taxiAvailability", headers={'User-Agent' : "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0"}) 
	con = urllib2.urlopen(req)
	return json.loads(con.read());

def isInRadius(data,radi):
	count = 0;
	for geo in data:
		lng = 103.7913314 - geo[0];
		lng = math.pow(lng, 2);
		lat = 1.345609 - geo[1];
		lat = math.pow(lat, 2);
		rtn = math.sqrt(lat + lng)
		if rtn < radi:
			count = count + 1;
	return count;

def AvailableTaxisInRadius(radi):
	data = GetDataTaxi();
	data = GetCoordinates(data);
	print isInRadius(data,radi);
