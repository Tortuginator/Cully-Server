import traceback 	
import sys
import thread
import requests
import json

class report():
	@staticmethod
	def do(data,ref):
		#DEF
		token = "gessdisplayx001"

		#THREAD
		type_, value_, traceback_ = sys.exc_info()
		trace = traceback.format_exception(type_, value_, traceback_)
		print trace
		thread.start_new_thread(report.Request,(token,trace,ref,data))

	@staticmethod
	def Request(token,message,ref,variables):
		import requests
		innerdata = {"data":json.dumps({"message":message,"ref":ref,"variables":variables})}
		print innerdata
		r = requests.post("https://errorreport.herokuapp.com/API/v1.0/" + token + "/report/new", data=innerdata)
		print "Error report:",(r.status_code, r.reason)

		try:
			p = r.json();
			print p["message"]
		except:
			pass