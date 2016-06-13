import urllib2
from icalendar import Calendar
import pytz

def GeneratePreview(Content):
	ICALf = urllib2.urlopen(Content).read()
	ical=Calendar.from_ical(ICALf)
	for vevent in ical.subcomponents:
		if vevent.name != "VEVENT":
			continue
		title = str(vevent.get('SUMMARY'))
		description = str(vevent.get('DESCRIPTION'))
		location = str(vevent.get('LOCATION'))
		start = vevent.get('DTSTART').dt      # a datetime
		end = vevent.get('DTEND').dt        # a datetime

print GeneratePreview("http://www.gess.sg/calendar/page_604.ics");