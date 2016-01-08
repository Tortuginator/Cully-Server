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
import configuration
from os import listdir
from os.path import isfile, join
import logging
#SETTINGS
global C_buffer
C_buffer = configuration.Config_Server_buffer
global C_host
C_host = configuration.Config_Server_address
global C_port
C_port = configuration.Config_Server_port

#A_mysql = MySQLdb.Connection(configuration.Config_Mysql_host, configuration.Config_Mysql_username, configuration.Config_Mysql_password,configuration.Config_Mysql_database)
global A_stime
A_stime = configuration.Config_Server_TimeFormat
global A_addr
A_addr = "http://" + str(C_host) + ":" + str(C_port) + "/"

#Log INIT
logging.basicConfig(filename="server_er.log",level=logging.DEBUG)
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

def demultiplex_item(Type,Content):
	overl = 0 #Activate PSI overlay
	try:
		return pages.GetPage(A_addr,Type,Content,overl,configuration.Config_Server_DebugOverlay)
	except Exception,e:
		logging.error('demultiplex_item();Error occured while Rendering / Finally returning values:', exc_info=True)
		return "Runtime exception occured in the system. This error while rendering the page threatens the system integrety and security. The Error occured in the pages.py. Correct the error or reset the rendering engine to prevent system overload/failture.";
def handle_gettime(listt,target,total):
	p=0;total = total + 0.0;
	for i,r in enumerate(listt):
		p = p + ((int(r)+0.0)/total)	
		if p > ((target+0.0)/total):
			if i == 0:
				return 0
			else:
				return int(i)-1
	return None;
def handle_calcitem(listt,id):
	p = 0;
	for v,i in enumerate(listt):
		p = p + int(i);
		if v == int(id):
			return p;
	return None;
def handle_timing(seconds,currid,total_round,block_time):
	time_c_item = handle_calcitem(block_time,currid)
	if time_c_item < seconds:
		a = seconds + time_c_item;
		b = a%time_c_item;
		return handle_gettime(block_time,b,total_round);
	else:
		return int(currid);
def handle_TimeUpdate(A_mysql_cur,device):
	now = datetime.datetime.now();
	A_mysql_cur.execute("UPDATE m_devices SET m_devices.LastSeen = %s WHERE m_devices.UID = %s", (now.strftime(A_stime),int(device), )) #Force Update

def handle_DisplayUpdate(parameter):
	#ALGORITHM COPYRIGHT FELIX FRIEDBERGER 2015/2016 DO NOT DISTRIBUTE FREELY
	try:
		A_mysql = MySQLdb.Connection(configuration.Config_Mysql_host, configuration.Config_Mysql_username, configuration.Config_Mysql_password,configuration.Config_Mysql_database)
	except Exception, e:
		raise;return None;

	#CHECK if device exists
	try:
		A_mysql_cur = A_mysql.cursor()
		A_mysql_cur.execute("SELECT * FROM m_push WHERE device = %s", (parameter["d"], ))
		if not A_mysql_cur.rowcount == 1:return None;
		display_sql = A_mysql_cur.fetchone()
		handle_TimeUpdate(A_mysql_cur,parameter["d"]);
		if display_sql[2] == "SUPER-OVERWRITE":return {"content":demultiplex_item("7",""),"id":-1,"type":-1,"name":"OVERWRITE"};
		if display_sql[2] == "" or "|" not in display_sql[2] or ";" not in display_sql[2]:return None;#check if data valid and present
		content_command = display_sql[6];
		if len(str(display_sql[2]).split("|")) <= 1:return None;#check if min. 2 items exist
		album_current_id = int(display_sql[5]); #get possible sub

		#CALCULATE NEXT TIME AND TOTAL TIME
		cycle_duration = 0;block_time = list();block_item = list();
		content = str(display_sql[2]).split("|");#split content into frames
		cycle_current = int(display_sql[1]);#Active Group

		for frame in content:
			if not ";" in frame:frame = frame + ";10";#if not time given replace with 10 seconds
			frame = frame.split(";");
			block_time.append(frame[1])#add to time
			block_item.append(frame[0]);#add to idlist
			cycle_duration = cycle_duration + int(frame[1]);

		cycle_current_item_time = block_time[cycle_current];

		#CALCULATE TIMEDIFFERENCE
		now = datetime.datetime.now()
		then = datetime.datetime.strptime(display_sql[3], A_stime);
		cycle_time_overall = now - then
		cycle_time_overall = cycle_time_overall.seconds;

	except Exception, e:
		logging.error('handle_DisplayUpdate();TimeCalculate Error occured:', exc_info=True)

	#HANDLE IF NEXT ITEM OR STAY WITH CURRENT ITEM
	try:

		if cycle_time_overall >= int(cycle_current_item_time): #NEXT ITEM
			album_content = None;
			calculated_item = handle_timing(cycle_time_overall,cycle_current,cycle_duration,block_time);

			#Check if nextitem is 0 or +1
			calculated_item = calculated_item+1
			if calculated_item >= len(block_item):calculated_item = 0;#check if max value reached

			#GET ITEM
			A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (block_item[calculated_item], )) #GET ITEM
			if not A_mysql_cur.rowcount == 1:
				A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s WHERE device = %s", (int(calculated_item)+1,now.strftime(A_stime),str(parameter["d"]), )) #Force Update
				A_mysql.commit()
				return None;#ID does not exist
			display_sql = A_mysql_cur.fetchone()
			#SLIDESHOW
			if display_sql[2] == "":return None; #IF no type is set
			if int(display_sql[2]) == 6:#SLIDESHOW ID
				album_current_id = int(album_current_id);
				operation_return = False;
				path = configuration.Config_Server_Storage + display_sql[3];
				if not os.path.isdir(path):
					album_current_id = 0;
					operation_return = True;
				else:
					files = [f for f in listdir(path) if isfile(join(path, f))];
					if len(files) == 0: operation_return = True;
					if (len(files)-1) <= album_current_id:
						album_current_id = 0;
					else:
						album_current_id = int(album_current_id) + 1;

					try:
						album_content = path + "\\" + files[album_current_id]
					except IndexError:
						operation_return = True;album_current_id = 0;album_content = "";

				#UPDATE TIMEING + CURRENT STATUS
				A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s, m_push.current_sub = %s WHERE device = %s", (calculated_item,now.strftime(A_stime),int(album_current_id),str(parameter["d"]), )) #GET ITEM
				A_mysql.commit()
				if operation_return == True: return None;
			else:
				A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s WHERE device = %s", (calculated_item,now.strftime(A_stime),str(parameter["d"]), )) #GET ITEM
				A_mysql.commit()

		else:
			#STAY
			calculated_item = handle_timing(cycle_time_overall,cycle_current,cycle_duration,block_time);
			A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (block_item[calculated_item], )) #GET ITEM
			if not A_mysql_cur.rowcount == 1:
				A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s WHERE device = %s", (int(calculated_item)+1,now.strftime(A_stime),str(parameters["d"]), )) #Force Update pn error
				A_mysql.commit()
				return None;#ID does not exist
			display_sql = A_mysql_cur.fetchone()
			album_content = None;
			#SLIDESHOW Mode if Type == 6 = Slideshow
			if int(display_sql[2]) == 6:
				album_current_id = int(album_current_id);
				operation_return = False;#optional forced retrun True;False
				path = configuration.Config_Server_Storage + display_sql[3];
				if not os.path.isdir(path):#if path is folder
					album_current_id = 0;
					operation_return = True;#
				else:
					files = [f for f in listdir(path) if isfile(join(path, f))];#all files in folder
					try:
						album_content = path + "\\" + files[album_current_id] #combine path
					except IndexError:
						operation_return = True;album_current_id = 0;album_content = ""; #reset variables on error
				if operation_return == True: return None;#initiate possible return Null;

				#CHECK SLIDESHOW CONTENT
		if not album_content == None:
			content_inner = album_content;
		else:
			content_inner = display_sql[3];

		#PSI
		file_psi = open('psi.val', 'r');dPSI = file_psi.readlines();dPSI = json.loads(dPSI[0]);

		#RETURN
		try:
			content_mplex = demultiplex_item(display_sql[2],content_inner);
			if content_mplex == "EX_err":return {"error":"EX_err"};
			if content_command != "" and configuration.Config_Server_CommandSystem == True and content_command != "NULL":
				return {"content":content_mplex,"id":display_sql[0],"type":display_sql[2],"name":display_sql[1],"command":content_command,"PSI":{"Int":int(dPSI["PSI"]),"Time":str(dPSI["time"])}}
			else:
				return {"content":content_mplex,"id":display_sql[0],"type":display_sql[2],"name":display_sql[1],"PSI":{"Int":int(dPSI["PSI"]),"Time":str(dPSI["time"])}}
		except Exception,e:
			logging.error('handle_DisplayUpdate();Error occured while Rendering / Finally returning values:', exc_info=True)
			return {"error":"EX_err"};

	except Exception, e:
		logging.error('handle_DisplayUpdate();TimeSelect Error occured:', exc_info=True)
		return None;

def handle_command(headers,soc):
	p = decode_parameters(headers["Path"]);
	if ("d" in p) and ("c" in p):
		if p["c"] == "GET": #GET Display
			return json.dumps(handle_DisplayUpdate(p))
		else: #UNKNOWN Command
			return None;
	else:
		return None;
		

def generateheader(type,data):
	return 'HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\nCache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data

def senddata(data,type,cl):
	cl.send(generateheader(type,data))

def senderror(cl):
	senddata(demultiplex_item(0,""),"Content-type: text/html",cl);
	
def readdata(file):
	try:
		with open(file, "rb") as image_file:
			return image_file.read();
	except Exception, e:
		logging.error('readdata();Error while reading file:', exc_info=True);

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
		logging.error('decode_header();Error occured when decoding header:', exc_info=True)

def handler(clientsocket, clientaddr):
	print "Connection Established " , clientaddr
	logging.info('System Initialized ' + str(clientaddr))	
	while 1:
		rec_data = clientsocket.recv(C_buffer)#Decode recived Content
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
					senderror(clientsocket);
				else:
					senddata(encoded_string,"Content-type: application/json",clientsocket);

			elif headers["Path"][:5] == "/img/":#Possible Image detection
				path = headers["Path"];
				path = path.replace("%5C","\\");
				path = path.replace("/img/",configuration.Config_Server_Storage);#clear paths && replace old origin with server official origin

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
			logging.error('handler(); Mainroutine error:', exc_info=True)
			raise
	print "Connection Closed ", clientaddr, "\n"

if __name__ == "__main__":
	addr = (C_host, C_port)
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(addr)
	serversocket.listen(2)
	logging.info('System Initialized')
	thread.start_new_thread(psi.PSIAutoUpdate, ("psi.val", ))
	print "***|SERVER started on %s:%s with buffer size %s bytes|***" % (C_host,C_port,C_buffer) 
	while 1:
		clientsocket, clientaddr = serversocket.accept()
		thread.start_new_thread(handler, (clientsocket, clientaddr))
	serversocket.close()
