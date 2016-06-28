import traceback 	
import sys
import threading
import requests
import json

class report():
	@staticmethod
	def do(data, ref, execnfo):
		#DEF
		token = "gessdisplayx001"

		#THREAD
		type_, value_, traceback_ = execnfo
		trace = traceback.format_exception(type_, value_, traceback_)
		print "[!][Reporter] Preparing new report"
		t = threading.Thread(target=report.Request,args=(token, trace, ref, data))
		#t.start();

	@staticmethod
	def Request(token, message, ref, variables):
		print "[!][Reporter] Generating Report"
		import requests
		innerdata = {"data":json.dumps({"message":message, "ref":ref.encode('ascii', 'ignore'), "variables":variables},encoding='latin1',ensure_ascii=False)}
		innerdata["data"] = innerdata["data"].encode('ascii', 'ignore')
		r = requests.post("https://errorreport.herokuapp.com/API/v1.0/" + token + "/report/new", data=innerdata)
		print "[!][Reporter] Error report status:", (r.status_code, r.reason)

		try:
			p = r.json();
			print p["message"]
		except:
			pass