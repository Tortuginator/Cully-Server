import urllib2
import sys
from icalendar import Calendar
from datetime import datetime,timedelta
from dateutil import rrule
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
				eventrule = i.get("rrule");
				date = None;
				try:
					if eventrule:
						str_rule = '';
						until = '';
						for k, v in eventrule.items():
							if k != "UNTIL":
								str_rule = str_rule + k + '=' + str(v[0]) + ';'
							else:
								until = v

						rule = rrule.rrulestr(str_rule[:-1],dtstart = datetime.strptime(i.get('dtstart').dt.isoformat(), '%Y-%m-%dT%H:%M:00+08:00'))
						date = rule.after(datetime.now()-timedelta(hours = 3))#+3hrs prevents events to "disappear" from the calendar

						#Save event
						newEvt['title'] = i.get('summary')
						newEvt['start'] = date.strftime("%Y-%m-%d %H:%M:%S+08:00")
						if i.get('dtend') != None:
							timediff = datetime.strptime(i.get('dtend').dt.isoformat(), '%Y-%m-%dT%H:%M:00+08:00')-datetime.strptime(i.get('dtstart').dt.isoformat(), '%Y-%m-%dT%H:%M:00+08:00')
							newEvt['end'] = (date + timediff).strftime("%Y-%m-%d %H:%M:%S+08:00")
					else:
						newEvt['title'] = i.get('summary')
						newEvt['start'] = i.get('dtstart').dt.isoformat()
						if i.get('dtend'):
							newEvt['end'] = i.get('dtend').dt.isoformat()
					if i.get('location'):
						newEvt['url'] = i.get('location')
					evtList.append(newEvt)
				except Exception,e:
					pass

		return json.dumps(evtList)