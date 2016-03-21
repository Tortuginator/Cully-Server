import socket
import time
import thread
import json
import os
import _mysql
import MySQLdb
import datetime
import math
import __future__
import psi
import pages
from os import listdir
from os.path import isfile, join
import logging
import Modules
#SETTINGS
global D_StartTime
global Configuration
D_StartTime = datetime.datetime.now()

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
	A_mysql_cur.execute("UPDATE m_devices SET m_devices.LastSeen = %s WHERE m_devices.UID = %s", (now.strftime(Configuration["Server"]["TimeFormat"]),int(device), )) #Force Update

def handle_DisplayUpdate(parameter):
	#ALGORITHM COPYRIGHT FELIX FRIEDBERGER 2015/2016 DO NOT DISTRIBUTE FREELY
	try:
		A_mysql = MySQLdb.Connection(Configuration["MYSQL"]["Host"], Configuration["MYSQL"]["Username"], Configuration["MYSQL"]["Password"],Configuration["MYSQL"]["Database"])
	except Exception, e:
		raise;
		return None;

	#CHECK if device exists
	A_mysql_cur = A_mysql.cursor()
	A_mysql_cur.execute("SELECT * FROM m_push WHERE device = %s", (parameter["d"], ))
	if not A_mysql_cur.rowcount == 1:
		return None;

	display_sql = A_mysql_cur.fetchone()
	handle_TimeUpdate(A_mysql_cur,parameter["d"]);

	if display_sql[2] == "" or "|" not in display_sql[2] or ";" not in display_sql[2]:
		return None;#check if data valid and present

	Ext_Command = display_sql[6];
	if len(str(display_sql[2]).split("|")) <= 1:
		return None;#check if min. 2 items exist


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
		return None;#ID does not exist
	display_sql = A_mysql_cur.fetchone()

	return Modules.FrameContent.GenerateFrame(display_sql[2],display_sql[3],display_sql[1],display_sql[0],Configuration,Ext_Command)

def handle_command(headers,soc):
	p = decode_parameters(headers["Path"]);
	if ("d" in p) and ("c" in p):
		if p["c"] == "GET": #GET Display
			t = handle_DisplayUpdate(p)
			if t != None:
				return json.dumps(t)
			else:
				return Modules.FrameContent.InternalError("Display Update function returned NONE-object");
		else: #UNKNOWN Command
			return None;
	else:
		return None;
		

def generatepacket(type,data):
	return 'HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\nCache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data

def senddata(data,type,cl):
	cl.send(generatepacket(type,data))

def senderror(cl,detail = None):
	senddata(json.dumps(Modules.FrameContent.InternalError(detail)),"Content-type: text/html",cl);
	
def readdata(file):
	try:
		with open(file, "rb") as image_file:
			return image_file.read();
	except Exception, e:
		raise
def decode_header(raw):
	try:
		raw_headers = raw.split("\r\n");headers = dict();
		if raw_headers[0][:3] == "OPT":
			return None;
			
		if raw_headers[0][:3] == "GET":
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
		raise
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
				senderror(clientsocket);
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

				if os.path.isfile(path + ".file"):#typical server file
					senddata(readdata(path + ".file"),"Content-type: image/png",clientsocket)#sendimage
				else:
					if os.path.isfile(path):
						senddata(readdata(path),"Content-type: image/png",clientsocket)#if file has no ending *.file
					else:
						senderror(clientsocket);# if booth do not match error response will be send
			elif headers["Path"][:4] == "/PSI":#Possible PSI REQUEST
				if os.path.isfile("psi.val"):
					senddata(readdata("psi.val"),"Content-type: application/json",clientsocket)#sendimage
				else:
					senderror(clientsocket);
			else:
				if "error" in headers["Path"]:#autodetect path for 'error' and send error image // image normally only requested by errorpage
					senddata(readdata("error.jpg"),"Content-type: image/png",clientsocket)#send error image
				else:
					senderror(clientsocket)#send error on error page error
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
	thread.start_new_thread(psi.PSIAutoUpdate, ("psi.val", ))
	print "***|SERVER started on %s:%s with buffer size %s bytes|***" % (Configuration["Server"]["LocalAddress"],Configuration["Server"]["Port"],Configuration["Server"]["Buffer"]) 
	while 1:
		clientsocket, clientaddr = serversocket.accept()
		thread.start_new_thread(handler, (clientsocket, clientaddr))
	serversocket.close()
