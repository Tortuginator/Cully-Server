import urllib2
import sys
from icalendar import Calendar
from datetime import datetime
import json

class calendar:
	@staticmethod
	def StrToArr(input,truedate = True):
		cal = Calendar.from_ical(input)
		evtList = []
		for i in cal.walk():
		    if i.name == 'VEVENT':
		        newEvt = { 'editable' : False, 'allDay' : False }
		        if i.get('summary') != None:
		        	newEvt['Summary'] = str(i.get('summary').encode('ascii', 'ignore'))
		        if i.get('location') != None:
		        	newEvt['Location'] = str(i.get('location').encode('ascii', 'ignore'))
		        newEvt['DtStart'] = i.get('dtstart').dt.isoformat()
		        if truedate is True:
		        	if not ":" in newEvt['DtStart']:
		        		newEvt['DtStart'] = datetime.strptime(newEvt['DtStart'], '%Y-%m-%d')
		        	else:
		        		newEvt['DtStart'] = datetime.strptime(newEvt['DtStart'], '%Y-%m-%dT%H:%M:00')
		        try:
		        	newEvt['DtEnd'] = i.get('dtend').dt.isoformat()
		        	if truedate is True:
				        if not ":" in newEvt['DtEnd']:
				        	newEvt['DtEnd'] = datetime.strptime(newEvt['DtEnd'], '%Y-%m-%d')
				        else:
				        	newEvt['DtEnd'] = datetime.strptime(newEvt['DtEnd'], '%Y-%m-%dT%H:%M:00')
		        except Exception,e:
		        	pass
		        evtList.append(newEvt)
		return evtList

	@staticmethod
	def ReformStr(input):
		cal = Calendar.from_ical(input)
		evtList = []
		 
		for i in cal.walk():
		    if i.name == 'VEVENT':
		        newEvt = { 'editable' : False, 'allDay' : False }
		        newEvt['title'] = i.get('summary')
		        newEvt['start'] = i.get('dtstart').dt.isoformat()
		        try:
		        	newEvt['end'] = i.get('dtend').dt.isoformat()
		        except Exception,e:
		        	pass
		        if i.get('location'):
		            newEvt['url'] = i.get('location')
		        evtList.append(newEvt)
		 
		return json.dumps(evtList)
