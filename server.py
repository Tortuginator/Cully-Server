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
import Data_gov
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
	if not "?" in url:
		return
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
	return pages.GetPage(A_addr,Type,Content,overl,configuration.Config_Server_DebugOverlay)

def handle_gettime(listt,target,total):
	p=0;total = total + 0.0;
	for i,r in enumerate(listt):
		p = p + ((int(r)+0.0)/total)	
		if p > ((target+0.0)/total):
			if i == 0:
				return 0
			else:
				return int(i)-1

def handle_calcitem(listt,id):
	p = 0
	for v,i in enumerate(listt):
		p = p + int(i)
		if v == int(id):
			return p;

def handle_timing(seconds,currid,total_round,time_blocks):
	time_c_item = handle_calcitem(time_blocks,currid)
	if time_c_item < seconds:
		a = seconds + time_c_item;
		b = a%time_c_item;
		return handle_gettime(time_blocks,b,total_round)
	else:
		return int(currid);

def handle_DisplayUpdate(p):
	#ALGORITHM COPYRIGHT FELIX FRIEDBERGER 2015/2016 DO NOT DISTRIBUTE FREELY
	A_mysql = MySQLdb.Connection(configuration.Config_Mysql_host, configuration.Config_Mysql_username, configuration.Config_Mysql_password,configuration.Config_Mysql_database)
	#CHECK if device exists
	try:
		A_mysql_cur = A_mysql.cursor()
		A_mysql_cur.execute("SELECT * FROM m_push WHERE device = %s", (p["d"], ))
		if not A_mysql_cur.rowcount == 1:return None;
		display_sql = A_mysql_cur.fetchone()
		if display_sql[2] == "" or "|" not in display_sql[2] or ";" not in display_sql[2]:return None;#check if data valid and present
		sub_id = int(display_sql[5]); #get possible sub
		#CALCULATE NEXT TIME AND TOTAL TIME
		total_round_duration = 0;
		content = str(display_sql[2]).split("|");#split content into frames
		time_blocks = list();itemlist = list();
		t_dpgroup = int(display_sql[1]);#Active Group

		for frame in content:
			if not ";" in frame:frame = frame + ";10";#if not time given replace with 10 seconds
			bframe = frame.split(";");
			time_blocks.append(bframe[1])#add to time
			itemlist.append(bframe[0]);#add to idlist
			total_round_duration = total_round_duration + int(bframe[1]);

		time_gap = time_blocks[t_dpgroup];

		#CALCULATE TIMEDIFFERENCE
		then = datetime.datetime.strptime(display_sql[3], A_stime)
		now = datetime.datetime.now()
		time_passed = now - then;time_passed = time_passed.seconds;

	except Exception, e:
		logging.error('handle_DisplayUpdate();TimeCalculate Error occured:', exc_info=True)

	#HANDLE IF NEXT ITEM OR STAY WITH ITEM
	try:

		if time_passed >= int(time_gap): #NEXT ITEM
			album_content = None;
			calculated_item = handle_timing(time_passed,t_dpgroup,total_round_duration,time_blocks);

			#Check if nextitem is 0 or +1
			calculated_item = calculated_item+1
			if calculated_item >= len(itemlist):#check if max value reached
				calculated_item = 0;

			#GET ITEM
			A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (itemlist[calculated_item], )) #GET ITEM
			if not A_mysql_cur.rowcount == 1:return None;#ID does not exist
			display_sql = A_mysql_cur.fetchone()

			#SLIDESHOW
			if int(display_sql[2]) == 6:
				sub_id = int(sub_id);
				opret = False;
				path = configuration.Config_Server_Storage + display_sql[3];
				if not os.path.isdir(path):
					sub_id = 0;
					opret = True;
				else:
					files = [f for f in listdir(path) if isfile(join(path, f))];
					if len(files) == 0: opret = True;
					if (len(files)-1) <= sub_id:
						sub_id = 0;
					else:
						sub_id = int(sub_id) + 1;

					try:
						album_content = path + "\\" + files[sub_id]
					except IndexError:
						opret = True;sub_id = 0;album_content = "";

				#UPDATE TIMEING + CURRENT STATUS
				A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s, m_push.current_sub = %s WHERE device = %s", (calculated_item,now.strftime(A_stime),int(sub_id),str(p["d"]), )) #GET ITEM
				A_mysql.commit()
				if opret == True: return None;
			else:
				A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s WHERE device = %s", (calculated_item,now.strftime(A_stime),str(p["d"]), )) #GET ITEM
				A_mysql.commit()

		else:
			#STAY
			calculated_item = handle_timing(time_passed,t_dpgroup,total_round_duration,time_blocks);
			A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (itemlist[calculated_item], )) #GET ITEM
			if not A_mysql_cur.rowcount == 1:return None;#ID does not exist
			display_sql = A_mysql_cur.fetchone()

			#SLIDESHOW
			if int(display_sql[2]) == 6:
				sub_id = int(sub_id);
				opret = False;
				path = configuration.Config_Server_Storage + display_sql[3];
				if not os.path.isdir(path):
					sub_id = 0;
					opret = True;
				else:
					files = [f for f in listdir(path) if isfile(join(path, f))];
					try:
						album_content = path + "\\" + files[sub_id]
					except IndexError:
						opret = True;sub_id = 0;album_content = "";
			if opret == True: return None;

		#CHECK SLIDESHOW CONTENT
		if not album_content == None:
			content_inner = album_content;
		else:
			content_inner = display_sql[3];

		#RETURN
		try:
			return {"content":demultiplex_item(display_sql[2],content_inner),"id":display_sql[0],"type":display_sql[2],"name":display_sql[1]}
		except Exception,e:
			return None;
			logging.error('handle_DisplayUpdate();Error occured while Rendering / Finally returning values:', exc_info=True)
	except Exception, e:
		logging.error('handle_DisplayUpdate();TimeSelect Error occured:', exc_info=True)

def handle_command(headers,soc):
	p = decode_parameters(headers["Path"]);
	if ("d" in p) and ("c" in p):
		if p["c"] == "GET": #GET Display
			return json.dumps(handle_DisplayUpdate(p))
		else: #UNKNOWN Command
			return None

def senddata(data,type,cl):
	cl.send('HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\nAccess-Control-Allow-Headers:x-device\nCache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data)

def senderror(cl):
	senddata(demultiplex_item(0,""),"Content-type: text/html",cl);
	
def readdata(file):
	try:
		with open(file, "rb") as image_file:
			return image_file.read()      
	except Exception, e:
		logging.error('readdata();Error while reading file:', exc_info=True)
def decode_header(raw):
	try:
		raw_headers = raw.split("\r\n");headers = dict();
		if raw_headers[0][:3] == "OPT":
			return None;
		if raw_headers[0][:3] == "GET":
			headers["Request"] = "GET"
			headers["Path"] = raw_headers[0].split(" ")[1]
			headers["Version"] = raw_headers[0].split(" ")[2]

		for head in raw_headers:
			if ":" in head:
				tmp = head.split(":")
				headers[tmp[0]] = tmp[1]
			elif len(head) > 1:
				headers["Content"] = head
		return headers

	except Exception, e:
		logging.error('decode_header();Error occured when decoding header:', exc_info=True)

def handler(clientsocket, clientaddr):
	print "Connection Established " , clientaddr
	logging.info('System Initialized')
	while 1:
		rec_data = clientsocket.recv(C_buffer)
		if not rec_data:
			break
		try:
			headers = decode_header(rec_data)
			if None == headers:
				senderror(clientsocket);
				break
			if headers["Path"][:2] == "/?":
				encoded_string = handle_command(headers,clientsocket)
				if encoded_string == None or encoded_string == "null":
					senderror(clientsocket);
				else:
					senddata(encoded_string,"Content-type: application/json",clientsocket);
			elif headers["Path"][:5] == "/img/":
				path = headers["Path"];
				path = path.replace("%5C","\\");
				path = path.replace("/img/",configuration.Config_Server_Storage);
				if os.path.isfile(path + ".file"):
					senddata(readdata(path + ".file"),"Content-type: image/png",clientsocket)
				else:
					if os.path.isfile(path):
						senddata(readdata(path),"Content-type: image/png",clientsocket)
					else:
						senderror(clientsocket)
			else:
				if "error" in headers["Path"]:
					senddata(readdata("error.jpg"),"Content-type: image/png",clientsocket)
				else:
					senderror(clientsocket)
		except Exception as e:
			senderror(clientsocket)
			logging.error('handler(); Mainroutine error:', exc_info=True)
			raise
	print "Connection Closed ", clientaddr

if __name__ == "__main__":
	addr = (C_host, C_port)
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(addr)
	serversocket.listen(2)
	logging.info('System Initialized')
	print "***|SERVER started on %s:%s with buffer size %s bytes|***" % (C_host,C_port,C_buffer) 
	while 1:
		clientsocket, clientaddr = serversocket.accept()
		thread.start_new_thread(handler, (clientsocket, clientaddr))
	serversocket.close()
