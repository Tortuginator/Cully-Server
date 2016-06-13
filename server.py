import socket
import time
import hashlib
import thread
import json
import os
import _mysql
import MySQLdb
import datetime
import math
import __future__
import pages
from os import listdir
from os.path import isfile, join
import logging
import Modules
#SETTINGS
global D_StartTime
global Configuration
D_StartTime = datetime.datetime.now()
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
#FUNCTIONS
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
			b = a.split("=");p[b[0]] = b[1];
	return p

def handle_TimeUpdate(A_mysql_cur,device):
	now = datetime.datetime.now();
	A_mysql_cur.execute("UPDATE m_devices SET m_devices.LastSeen = %s WHERE m_devices.UID = %s", (now.strftime(Configuration["Server"]["TimeFormat"]),device, )) #Force Update

def handle_DisplayUpdate(parameter):
	#ALGORITHM COPYRIGHT FELIX FRIEDBERGER 2015/2016 DO NOT DISTRIBUTE FREELY
	try:
		A_mysql = MySQLdb.Connection(Configuration["MYSQL"]["Host"], Configuration["MYSQL"]["Username"], Configuration["MYSQL"]["Password"],Configuration["MYSQL"]["Database"])
	except Exception, e:
		raise;
		return [0,None];

	#CHECK if device exists
	A_mysql_cur = A_mysql.cursor()
	A_mysql_cur.execute("SELECT * FROM m_push WHERE device = %s", (parameter["d"], ))
	if not A_mysql_cur.rowcount == 1:
		return [2,"UNREGISTERED"];

	display_sql = A_mysql_cur.fetchone()
	handle_TimeUpdate(A_mysql_cur,parameter["d"]);

	if display_sql[2] == "" or "|" not in display_sql[2] or ";" not in display_sql[2]:
		return [0,None];#check if data valid and present

	Ext_Command = display_sql[6];
	if len(str(display_sql[2]).split("|")) <= 1:
		return [0,None];#check if min. 2 items exist


	#PREPARE DATA SOURCE
	TimeFrames = list();
	ItemFrames = list();
	content = str(display_sql[2]).split("|");#split content into frames

	for frame in content:
		if not ";" in frame:frame = frame + ";10";#if not time given replace with 10 seconds
		frame = frame.split(";");
		TimeFrames.append(frame[1])#add to time
		ItemFrames.append(frame[0]);#add to idlist


	now = datetime.datetime.now()

	#Get Frame based on current Time
	CurrentTimeFrame = Modules.FrameTimer.GetFrameIndex(TimeFrames,D_StartTime)

	A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (ItemFrames[CurrentTimeFrame], ))
	if not A_mysql_cur.rowcount == 1:
		A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s WHERE device = %s", (int(CurrentTimeFrame),now.strftime( Configuration["Server"]["TimeFormat"]),str(parameter["d"]), )) #Force Update pn error
		A_mysql.commit()
		return [0,None];#ID does not exist
	display_sql = A_mysql_cur.fetchone()

	return [1,Modules.FrameContent.GenerateFrame(display_sql[2],display_sql[3],display_sql[1],display_sql[0],Configuration,Ext_Command)]

def AppendClientDetails(ident,input = "",registered = 0):
	if not ident in D_Temporary_Clients:
		D_Temporary_Clients[ident] = dict();
	if registered != 0 and (registered == True or registered == False):
		D_Temporary_Clients[ident]["registered"] = registered;
	if input != "":
		tmp = input.split(",");
		for e,d in enumerate(tmp):
			cce = tmp[int(e)].split(">>");
			if "session" == (cce[0].replace(" ","")):
				if not "clients" in D_Temporary_Clients[ident]:
					D_Temporary_Clients[ident]["clients"] = list();
				if not cce[1] in D_Temporary_Clients[ident]["clients"]:
					D_Temporary_Clients[ident]["clients"].append(cce[1])
			else:
				D_Temporary_Clients[ident][cce[0].replace(" ","")] = cce[1];
	

def handle_command(headers,soc):
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
				D_time_reset += datetime.timedelta(minutes = 1);
				D_Temporary_Clients = dict();

			if "x-config" in headers and "x-resolution" in headers:
				AppendClientDetails(str(p["d"]),input = headers["x-config"] + ",resolution>>" + headers["x-resolution"])
				if "session" in headers["x-config"]:
					t_session = headers["x-config"].split("session>>")[1].split(",")[0];
					t_interval = headers["x-config"].split("interval>>")[1].split(",")[0];
					if str(p["d"]) in D_Temporary_Clients and t_session in D_stat_resync:
						if "clients" in D_Temporary_Clients[str(p["d"])]:
							local_resync = True;
							del D_stat_resync[D_stat_resync.index(t_session)]
							print "Resync activated!"

			#Handle ReSYNC
			if D_resync <= datetime.datetime.now():
				D_resync = datetime.datetime.now();
				D_resync += datetime.timedelta(minutes = 4);
				D_stat_resync = list();
				D_resync_times = dict();
				for c in D_Temporary_Clients:
					if D_Temporary_Clients[c]["clients"] > 1:
						print "Updated Resync stats"
						for i in D_Temporary_Clients[c]["clients"]:
							D_stat_resync.append(i)


			#Calculate Display Update
			t = handle_DisplayUpdate(p);

			if t[0] == 1:
				if "x-config" in headers and "x-resolution" in headers and str(p["d"]) in D_Temporary_Clients:
					AppendClientDetails(str(p["d"]),registered = True);
				if local_resync == True:
					tmp_d = datetime.datetime.now();
					if not str(p["d"]) in D_resync_times:
						D_resync_times[str(p["d"])] = (int(tmp_d.second) + int(t_interval)+ int(t_interval))*1000 + tmp_d.microsecond/1000;
					t[1]["resync"] = D_resync_times[str(p["d"])];

				return json.dumps(t[1])
			else:
				if t[0] == 2:
						if "x-config" in headers and "x-resolution" in headers and str(p["d"]) in D_Temporary_Clients:
							AppendClientDetails(str(p["d"]),registered = False);
						return json.dumps(Modules.FrameContent.InternalVisibleError("The ID of this device is not setup/configured: " + p["d"]));
				return json.dumps(Modules.FrameContent.InternalError("Display Update function returned NONE-object"));
		else: #UNKNOWN Command
			return None;
	else:
		return None;
		

def generatepacket(type,data):
	return 'HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\nCache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Access-Control-Allow-Headers:x-config,x-resolution' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data

def senddata(data,type,cl):
	cl.send(generatepacket(type,data))

def senderror(cl,detail = None):
	print "Send JSON Error:",detail
	senddata(json.dumps(Modules.FrameContent.InternalError(detail)),"Content-type: application/json",cl);
	
def readdata(file):
	try:
		with open(file, "rb") as image_file:
			return image_file.read();
	except Exception, e:
		raise
def decode_header(raw):
	try:
		raw_headers = raw.split("\r\n");headers = dict();
		if raw_headers[0][:3] == "GET" or raw_headers[0][:3] == "OPT":
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

	except Exception, e:
		raise;

def handler(clientsocket, clientaddr):
	print "Connection Established " , clientaddr
	logging.info('System Initialized ' + str(clientaddr))	
	while 1:
		rec_data = clientsocket.recv(Configuration["Server"]["Buffer"])#Decode recived Content
		if not rec_data:
			break
		try:
			headers = decode_header(rec_data)

			if headers == None: #No decodable Headers eg. Telnet
				senderror(clientsocket,"Failed to deocde the headers");
				break;

			if headers["Path"][:2] == "/?": #parameter page (location undisclosed)
				encoded_string = handle_command(headers,clientsocket)
				if encoded_string == None or encoded_string == "null":
					senderror(clientsocket,"Command FNC returned None or Null, meaning, command not found");
				else:
					senddata(encoded_string,"Content-type: application/json",clientsocket);

			elif headers["Path"][:5] == "/img/":#Possible Image detection
				path = headers["Path"];
				path = path.replace("%5C","\\");
				path = path.replace("/img/",Configuration["Server"]["Storage"]);#clear paths && replace old origin with server official origin

				if os.path.isfile(path):
					senddata(readdata(path),"Content-type: image/png",clientsocket)#if file has no ending *.file
				else:
					senderror(clientsocket,"Image error");# if booth do not match error response will be send

			elif headers["Path"][:15] == "/API/UNKclients":
				senddata(json.dumps(D_Temporary_Clients),"Content-type: application/json",clientsocket);

			elif headers["Path"][:4] == "/PSI":#Possible PSI REQUEST
				senddata(gPSI,"Content-type: application/json",clientsocket)#sendimage
			else:
				if "error" in headers["Path"]:#autodetect path for 'error' and send error image // image normally only requested by errorpage
					senddata(readdata("error.jpg"),"Content-type: image/png",clientsocket)#send error image
				else:
					senderror(clientsocket,"Internal relay error" )#send error on error page error
		except Exception as e:
			senderror(clientsocket)
			raise
	print "Connection Closed ", clientaddr, "\n"

if __name__ == "__main__":

	try:
		Fstr = open('config.json')
	except Exception, e:
		print "[!][Config] failed to open config.json"

	try:
		Configuration = json.load(Fstr);
	except Exception, e:
		print "[!][Config] Failed to load JSON from file config.json"

	Configuration["ADDR"] = "http://" + str(Configuration["Server"]["PublicAddress"]) + ":" + str(Configuration["Server"]["PublicPort"]) + "/"#INIT CONFIG
	if "TRUE" == Configuration["Server"]["Debug"]: Configuration["Server"]["Debug"] = True;
	if "FALSE" == Configuration["Server"]["Debug"]: Configuration["Server"]["Debug"] = False;
	if "TRUE" == Configuration["Server"]["Command"]: Configuration["Server"]["Command"] = True;
	if "FALSE" == Configuration["Server"]["Command"]: Configuration["Server"]["Command"] = False;

	addr = (Configuration["Server"]["LocalAddress"], Configuration["Server"]["Port"])

	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(addr)
	serversocket.listen(2)
	thread.start_new_thread(Modules.psi.PSIAutoUpdate, ())
	print "***|SERVER started on %s:%s with buffer size %s bytes|***" % (Configuration["Server"]["LocalAddress"],Configuration["Server"]["Port"],Configuration["Server"]["Buffer"]) 
	while 1:
		clientsocket, clientaddr = serversocket.accept()
		thread.start_new_thread(handler, (clientsocket, clientaddr))
	serversocket.close()
