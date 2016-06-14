import datetime
class calendar:
	@staticmethod
	def StrToArr(input):
		pre = input.split("BEGIN:VEVENT");
		after = list();
		for i in pre:
			after.append(i.split("END:VEVENT")[0])
			final = list();
		for i in after:
			a = i.splitlines()
			final.append(dict())
			c=len(final)-1
			for b in a:
				if b.startswith("DESCRIPTION"):
					final[c]["Description"] = b.replace("DESCRIPTION:","");
				if b.startswith("SUMMARY"):
					final[c]["Summary"] = b.replace("SUMMARY:","");
				if b.startswith("LOCATION"):
					final[c]["Location"] = b.replace("LOCATION:","");
				if b.startswith("DTSTART"):
					final[c]["DtStart"] = b.replace("DTSTART:","");
					if "DTSTART;VALUE=DATE:" in final[c]["DtStart"]:
						final[c]["DtStart"] = datetime.datetime.strptime(final[c]["DtStart"].replace("DTSTART;VALUE=DATE:",""), '%Y%m%d')
					else:
						final[c]["DtStart"] = datetime.datetime.strptime(final[c]["DtStart"], '%Y%m%dT%H%M00')
				if b.startswith("DTEND"):
					final[c]["DtEnd"] = b.replace("DTEND:","");
					final[c]["DtEnd"] = datetime.datetime.strptime(final[c]["DtEnd"], '%Y%m%dT%H%M00')
		for i,e in enumerate(final):
			if len(e) == 0:
				del final[i]
		return final
