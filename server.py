import socket
import thread
import json
import os
import MySQLdb
import datetime
from os import listdir
from os.path import isfile, join
import logging
import modules
import sys
import HerokuReporter

def decode_parameters(url):
	if not "?" in url:return;
	params = url.split("?")

	if "&" in url:
		sub_params = params[1].split("&")
	else:
		sub_params = {params[1]}
	p = dict()
	for a in sub_params:
		if "=" in a:
			b = a.split("="); p[b[0]] = b[1];
	return p


def handle_DisplayUpdate(parameter):
	try:
		global D_storage
		#ALGORITHM COPYRIGHT FELIX FRIEDBERGER 2015/2016 DO NOT DISTRIBUTE FREELY
		try:
			A_mysql = MySQLdb.Connection(Configuration["MYSQL"]["Host"], Configuration["MYSQL"]["Username"], Configuration["MYSQL"]["Password"], Configuration["MYSQL"]["Database"])
		except Exception, e:
			logging.error(e);
			raise Exception('handle_DisplayUpdate() Failed to connect to the MYSQL database', Configuration);

		#CHECK if device exists
		A_mysql_cur = A_mysql.cursor()
		A_mysql_cur.execute("SELECT * FROM m_push WHERE device = %s", (parameter["d"], ))
		if not A_mysql_cur.rowcount == 1:
			return [2, "UNREGISTERED DEVICE"];

		DB_Device = A_mysql_cur.fetchone()#device, current,content, current_time, next_time, current_sub, push_command
		DB_Device = modules.validate.pushToArry(DB_Device);

		#Setup Cycle Time
		if not parameter["d"] in D_storage:
			D_storage[parameter["d"]] = dict();
			D_storage[parameter["d"]]["time"] = datetime.datetime.now()
			D_storage[parameter["d"]]["content"] = "";

		#PREPARE DATA SOURCE
		content = modules.FrameTimetable.GetCurrentFrame(DB_Device["content"]);
		content = modules.validate.content(content)
		#Reset Start time if the device has new content;
		if content != D_storage[parameter["d"]]["content"]:
			D_storage[parameter["d"]]["time"] = datetime.datetime.now();
			D_storage[parameter["d"]]["content"] = content;

		#Get Frame based on current Time
		CurrentIndexFrame = modules.FrameTimer.GetFrameIndex(content, D_storage[parameter["d"]]["time"])

		A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (CurrentIndexFrame, ))
		if not A_mysql_cur.rowcount == 1:
			raise Exception('The item registered in the contentlist is non-existant', CurrentIndexFrame);

		DB_item = A_mysql_cur.fetchone()
		rt = modules.FrameContent.GenerateFrame(DB_item[2], DB_item[3], DB_item[1], DB_item[0], Configuration, DB_Device["command"]);
		return [1, rt]
	except:
		v = dict();
		try:
			v["D_storage"] = D_storage
		except: pass;
		try:
			v["CurrentIndexFrame"] = CurrentIndexFrame
		except: pass;
		try:
			v["content"] = content
		except: pass;
		try:
			v["DB_Device"] = DB_Device
		except: pass;

		HerokuReporter.report.do(v, "handle_DisplayUpdate(parameter)",sys.exc_info());
		logging.exception("", exc_info=True)
		print "[!][CRITICAL] Unexpected error:", sys.exc_info()
		return [4, "Unexpected error"]

def AppendClientDetails(ident, input = "", registered = 0):
	if not ident in D_Temporary_Clients:
		D_Temporary_Clients[ident] = dict();

	if registered != 0 and (registered is True or registered is False):
		D_Temporary_Clients[ident]["registered"] = registered;

	if input != "":
		tmp = input.split(",");

		for e, d in enumerate(tmp):
			cce = tmp[int(e)].split(">>");

			if (cce[0].replace(" ", "") == "session"):
				if not "clients" in D_Temporary_Clients[ident]:
					D_Temporary_Clients[ident]["clients"] = list();

				if not cce[1] in D_Temporary_Clients[ident]["clients"]:
					D_Temporary_Clients[ident]["clients"].append(cce[1])
			else:
				D_Temporary_Clients[ident][cce[0].replace(" ", "")] = cce[1];

def handle_command(headers, soc):
	global D_Temporary_Clients
	global D_time_reset
	global D_stat_resync
	global D_resync
	global D_resync_times
	local_resync = False;
	p = decode_parameters(headers["Path"]);
	if ("d" in p) and ("c" in p):
		if p["c"] == "GET": #GET Display
			#Reset the Client list each minute
			if D_time_reset <= datetime.datetime.now():
				D_time_reset = datetime.datetime.now();
				D_time_reset += datetime.timedelta(minutes = 0.95);
				print "[*][API] Next Output Reset at " + D_time_reset.strftime("%Y-%m-%d %H:%M:%S")
				D_Temporary_Clients = dict();

			if "x-config" in headers and "x-resolution" in headers:
				AppendClientDetails(str(p["d"]), input = headers["x-config"] + ",resolution>>" + headers["x-resolution"])
				if "session" in headers["x-config"]:
					t_session = headers["x-config"].split("session>>")[1].split(",")[0];
					t_interval = headers["x-config"].split("interval>>")[1].split(",")[0];
					logging.info("API GET request for device: " + t_session);
					if str(p["d"]) in D_Temporary_Clients and t_session in D_stat_resync:

						if "clients" in D_Temporary_Clients[str(p["d"])]:
							local_resync = True;
							del D_stat_resync[D_stat_resync.index(t_session)]
							print "[*][SYNC] Syncronizing #" + str(p["d"]);

			#Handle ReSYNC
			if D_resync <= datetime.datetime.now():
				logging.info("Automatic Syncronization Trigger");
				ResetSync();

			#Calculate Display Update
			t = handle_DisplayUpdate(p);
			if t == None:return None;

			if t[0] == 1:
				if "x-config" in headers and "x-resolution" in headers and str(p["d"]) in D_Temporary_Clients:
					AppendClientDetails(str(p["d"]), registered = True);

				if local_resync is True:
					tmp_d = datetime.datetime.now();
					if not str(p["d"]) in D_resync_times:
						D_resync_times[str(p["d"])] = (int(tmp_d.second) + int(t_interval)+ int(t_interval))*1000 + tmp_d.microsecond/1000;
					t[1]["resync"] = D_resync_times[str(p["d"])];

				return json.dumps(t[1])

			elif t[0] == 2:
				if "x-config" in headers and "x-resolution" in headers and str(p["d"]) in D_Temporary_Clients:
					AppendClientDetails(str(p["d"]), registered = False);
				return json.dumps(modules.FrameContent.InternalVisibleError("The ID of this device is not setup/configured: " + p["d"]));
			
			return json.dumps(modules.FrameContent.InternalError("Display Update function returned NONE-object"));
		else: #UNKNOWN Command
			return None;
	else:
		return None;
		
def ResetSync():
	global D_Temporary_Clients
	global D_time_reset
	global D_stat_resync
	global D_resync
	global D_resync_times
	D_resync = datetime.datetime.now();
	D_resync += datetime.timedelta(minutes = 2.8);
	print "[+][SYNC] Next Syncronization at " + D_resync.strftime("%Y-%m-%d %H:%M:%S")
	logging.info("Syncronizing Clients");
	D_stat_resync = list();
	D_resync_times = dict();
	for c in D_Temporary_Clients:
		if D_Temporary_Clients[c]["clients"] > 1:
			print "[+][SYNC] preparing for Syncronization"
			for i in D_Temporary_Clients[c]["clients"]:
				D_stat_resync.append(i)

def generatepacket(type, data, stored = False):
	if stored is True:
		return 'HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\n' + 'Cache-Control:max-age=31536000' + '\n' + 'Access-Control-Allow-Headers:x-config,x-resolution' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data
	
	else:
		return 'HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\nCache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Access-Control-Allow-Headers:x-config,x-resolution' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data

def senddata(data, type, cl, stored = False):
	cl.send(generatepacket(type, data, stored))

def senderror(cl, detail = None):
	print "[!][WARNING] Error send:", detail
	senddata(json.dumps(modules.FrameContent.InternalError(detail)), "Content-type: application/json", cl);
	
def readdata(file):
	try:
		with open(file, "rb") as image_file:
			return image_file.read();
	except Exception, e:
		print "[!][CRITICAL] Failed to load file: " + file, sys.exc_info()
		logging.exception("Failed to open file: " + file, exc_info=True)
		return ""

def decode_header(raw):
	raw_headers = raw.split("\r\n");headers = dict();
	if raw_headers[0][:3] == "OPT":
		headers["Request"] = "OPT";
	
	else:
		headers["Request"] = "GET";

	headers["Path"] = raw_headers[0].split(" ")[1];
	headers["Version"] = raw_headers[0].split(" ")[2];

	for head in raw_headers:
		if ":" in head:
			tmp = head.split(":");
			headers[tmp[0]] = tmp[1];
		elif len(head) > 1:
			headers["Content"] = head;
	return headers

def handler(clientsocket, clientaddr):
	print "[+][CON] Established " + clientaddr
	logging.info('Thread Initialized ' + str(clientaddr))	
	while 1:
		try:
			rec_data = clientsocket.recv(Configuration["Server"]["Buffer"])#Decode recived Content
			if not rec_data:
				break
			headers = decode_header(rec_data)

			if headers == None: #No decodable Headers eg. Telnet
				senderror(clientsocket, "Failed to deocde headers");
				logging.error("Failed to deocde headers");
				break

			if headers["Path"][:2] == "/?": #parameter page (location undisclosed)
				encoded_string = handle_command(headers, clientsocket)
				if encoded_string == None or encoded_string == "null":
					senderror(clientsocket, "Command FNC returned None or Null => command not found");
				else:
					senddata(encoded_string, "Content-type: application/json", clientsocket);

			elif headers["Path"][:5] == "/img/":#Possible Image detection
				path = headers["Path"];
				path = path.replace("%5C", "\\");
				path = path.replace("/img/", Configuration["Server"]["Storage"]);#clear paths && replace old origin with server official origin

				if os.path.isfile(path):
					senddata(readdata(path), "Content-type: image/png", clientsocket, stored = True)#if file has no ending *.file
				else:
					senderror(clientsocket, "failed to load image");# if booth do not match error response will be send
					logging.error("Internal relay error var=" + path);

			elif headers["Path"][:15] == "/API/UNKclients":
				senddata(json.dumps(D_Temporary_Clients), "Content-type: application/json", clientsocket);

			elif headers["Path"][:15] == "/API/error":
				senddata(json.dumps(headers), "Content-type: application/json", clientsocket);

			elif headers["Path"][:14] == "/API/SyncReset":
				logging.info("Synchronization tiggered by API");
				ResetSync()
				senddata(json.dumps(["ok"]), "Content-type: application/json", clientsocket)#sendimage

			elif headers["Path"][:4] == "/PSI":#Possible PSI REQUEST
				senddata(gPSI, "Content-type: application/json", clientsocket)#sendimage

			else:
				if "error" in headers["Path"]:#autodetect path for 'error' and send error image // image normally only requested by errorpage
					senddata(readdata("error.jpg"), "Content-type: image/png", clientsocket)#send error image
				else:
					senderror(clientsocket, "Internal relay error" )#send error on error page error
					logging.error("Internal relay error. Path/Command not found");

		except Exception, e:
			v = dict();
			try:
				v["rec_data"] = rec_data
			except: pass;
			try:
				v["headers"] = headers
			except: pass;
			try:
				v["encoded_string"] = encoded_string
			except: pass;
			try:
				v["path"] = path
			except: pass;

			HerokuReporter.report.do(v, "handler()",sys.exc_info());
			print "[!][CRITICAL] Unexpected error:", sys.exc_info()
			logging.exception("", exc_info=True)

	print "[-][CON] Closed ", clientaddr, "\n"
	logging.info('Thread Closed ' + str(clientaddr))

def init():
	logging.basicConfig(filename='log' + datetime.datetime.now().strftime("%Y%m%d%H%M") + ".txt", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
	global D_storage
	D_storage = dict();
	global Configuration
	global D_Temporary_Clients
	D_Temporary_Clients = dict()
	global gPSI
	global D_time_reset;
	D_time_reset = datetime.datetime.now()
	global D_resync;
	D_resync = datetime.datetime.now()
	global D_stat_resync
	D_stat_resync = list();
	global D_resync_times
	D_resync_times = dict();

def main(confpath = None):
	global Configuration
	try:
		Fstr = open('config.json')
	except Exception, e:
		logging.exception("failed to open config.json", exc_info=True)
		print "[!][Config] failed to open config.json"

		#Try variable
		if confpath != None:
			try:
				Fstr = open(confpath)
			except Exception,e:
				print "[!][Config] failed to open config.json from var"
				logging.exception("failed to open config.json from var", exc_info=True)

		#Try startargument
		if len(sys.argv) > 1:
			try:
				Fstr = open(sys.argv[1])
			except Exception,e:
				print "[!][Config] failed to open config.json from argument"
				logging.exception("failed to open config.json from argument", exc_info=True)

	try:
		Configuration = json.load(Fstr);
	except Exception, e:
		logging.exception("failed to read config.json. JSON decode failed", exc_info=True)
		print "[!][Config] Failed to load JSON from file config.json"

	try:
		Configuration["ADDR"] = "http://" + str(Configuration["Server"]["PublicAddress"]) + ":" + str(Configuration["Server"]["PublicPort"]) + "/"#INIT CONFIG
		if "TRUE" == Configuration["Server"]["Debug"]: Configuration["Server"]["Debug"] = True;
		if "FALSE" == Configuration["Server"]["Debug"]: Configuration["Server"]["Debug"] = False;
		if "TRUE" == Configuration["Server"]["Command"]: Configuration["Server"]["Command"] = True;
		if "FALSE" == Configuration["Server"]["Command"]: Configuration["Server"]["Command"] = False;

		addr = (Configuration["Server"]["LocalAddress"], Configuration["Server"]["Port"])

		serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversocket.bind(addr)
		serversocket.listen(2)
		thread.start_new_thread(modules.psi.PSIAutoUpdate, ())
		print "***|SERVER started on %s:%s with buffer size %s bytes|***" % (Configuration["Server"]["LocalAddress"], Configuration["Server"]["Port"], Configuration["Server"]["Buffer"]) 
		while 1:
			clientsocket, clientaddr = serversocket.accept()
			thread.start_new_thread(handler, (clientsocket, clientaddr))
		serversocket.close()
	except Exception, e:
		v = dict();
		try:
			v["Configuration"] = Configuration
		except:pass;
		print v
		HerokuReporter.report.do(v, "handler()",sys.exc_info());
		print "[!][CRITICAL] Failed to initialize"
		logging.exception("Failed to initialize", exc_info=True)

if __name__ == "__main__":
	init();
	main();