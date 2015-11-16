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
#SETTINGS
global C_buffer
C_buffer = 1024*2
global C_host
C_host = "localhost"
global C_port
C_port = 5541
global A_mysql
A_mysql = MySQLdb.Connection('localhost', 'root', 'test123','sys')
global A_stime
A_stime = '%Y-%m-%d %H:%M:%S'
global A_addr
A_addr = "http://" + str(C_host) + ":" + str(C_port) + "/"

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

def demultiplex_item(content,type):
	overl = 1
	e = '<div style="position:absolute;bottom:0;right:0;height:250px;background-color:red;width:250px;"><center><p style="text-align:center;color: white;font-size: 30px;margin:0px;margin-top:20px;margin-bottom:20px;">PSI</p><p style="padding: 0px;margin: 0px;text-align:center;color:white;font-size:100px;">135</p></center></div>'
	r = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,300" rel="stylesheet" type="text/css">'#basefont style
	c = "font-family: 'Open Sans', sans-serif;margin:0px;padding:0px;"
	t = int(type)
	if t == 1: #LIVE TIME TABLE
		html = content
	elif t == 2: #TEXT MESSAGE
		html = content
	elif t == 3: #MANUAL HTML
		b = '<body style = "%s">\n%s\n</body>\n</html>\n' % (c,content)
		html = b
	elif t == 4: #FULLSOZE IMAGE
		html = '<body style="' + c + 'background-image:url(\'' + A_addr + 'img/' + content + '\');background-position: right top;background-size: 100%;">'
	else:
		html = '<body style="margin:0px;padding:0px;background-color:#f3f4f4;"><img src="' + A_addr + 'error.jpg" style="height:600px;width:800px;display: block;margin-left: auto;margin-right: auto"></src>'
	if overl == 1:
		return "<html>\n" + html + "\n" + e + "\n</body>\n" + r + "\n</html>"
	else:
		return "<html>\n" + html + "\n</body>\n" + r + "\n</html>"

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
	if handle_calcitem(time_blocks,currid) <= seconds:
		a = seconds + handle_calcitem(time_blocks,currid) + 0.0;
		if (a/total_round) >= 1:
			b = (a/total_round) - math.floor(a/total_round);b = b*total_round;
			return handle_gettime(time_blocks,b,total_round)
		else:
			return handle_gettime(time_blocks,a,total_round)
	else:
		return int(currid)
def handle_DisplayUpdate(p):
	#CHECK if device exists
	A_mysql_cur = A_mysql.cursor()
	A_mysql_cur.execute("SELECT * FROM m_push WHERE device = %s", (p["d"], ))
	if not A_mysql_cur.rowcount == 1:return None;
	display_group = A_mysql_cur.fetchone()

	#CALCULATE NEXT TIME AND TOTAL TIME
	total_round_duration = 0
	content = str(display_group[2]).split("|");
	time_blocks = list();itemlist = list();
	if int(display_group[4]) == 0:
		for a in content:
			b = a.split(";")
			time_blocks.append(b[1])
			itemlist.append(b[0])
			total_round_duration = total_round_duration + int(b[1])
		time_gap = time_blocks[int(display_group[1])]
	else:
		for a in content:
			b = a.split(";")
			itemlist.append(b[0])
			time_blocks.append(display_group[4])
			total_round_duration = int(display_group[4]) + total_round_duration
		time_gap = int(display_group[4])

	#CALCULATE TIMEDIFFERENCE
	then = datetime.datetime.strptime(display_group[3], A_stime)
	now = datetime.datetime.now()
	time_passed = now - then;time_passed = time_passed.seconds;

	#HANDLE
	if time_passed >= int(time_gap):
		#NEXT
		predicted_item = handle_timing(time_passed,display_group[1],total_round_duration,time_blocks);
		if len(itemlist) <= predicted_item+1:
			predicted_item = 0;
		else:
			predicted_item = predicted_item+1

		#GET ITEM
		A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (itemlist[predicted_item], )) #GET ITEM
		if not A_mysql_cur.rowcount == 1:return None;
		display_item = A_mysql_cur.fetchone()

		A_mysql_cur.execute("UPDATE m_push SET m_push.current = %s, m_push.current_time = %s WHERE device = %s", (predicted_item,now.strftime(A_stime),str(p["d"]), )) #GET ITEM
		A_mysql.commit()

		return demultiplex_item(display_item[3],display_item[2])
	else:
		#STAY
		predicted_item = handle_timing(time_passed,display_group[1],total_round_duration,time_blocks);
		A_mysql_cur.execute("SELECT * FROM m_item WHERE ID = %s", (itemlist[predicted_item], )) #GET ITEM
		if not A_mysql_cur.rowcount == 1:return None;
		display_item = A_mysql_cur.fetchone()

		return demultiplex_item(display_item[3],display_item[2])

def handle_command(headers,soc):
	p = decode_parameters(headers["Path"]);
	if ("d" in p) and ("c" in p):
		if p["c"] == "GET": #Display Get
			return handle_DisplayUpdate(p)
		else:
			#Command not known
			return None

def senddata(data,type,cl):
    cl.send('HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *\nAccess-Control-Allow-Headers:x-device\nCache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ type+ '\n' + '\n' + data)
def senderror(cl):
	senddata(demultiplex_item("",0),"Content-type: text/html",cl);
def readdata(file):
    with open(file, "rb") as image_file:
	return image_file.read()      

def decode_header(raw):
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

def handler(clientsocket, clientaddr):
	print "Connection Established " , clientaddr
	while 1:
		rec_data = clientsocket.recv(C_buffer)
		if not rec_data:
			break
		try:
			headers = decode_header(rec_data)
			if None == headers:
				senddata(clientsocket)
				break
			if headers["Path"][:2] == "/?":
				encoded_string = handle_command(headers,clientsocket)
				if encoded_string == None:
					senddata(clientsocket)
				else:
					senddata(encoded_string,"Content-type: text/html",clientsocket)
			elif headers["Path"][:5] == "/img/":
				path = headers["Path"];path = path.replace("/img/","storage/");
				if os.path.isfile(path):
					senddata(readdata(path),"Content-type: image/png",clientsocket)
				else:
					senddata(clientsocket)
			else:
				if "error" in headers["Path"]:
					senddata(readdata("error.jpg"),"Content-type: image/png",clientsocket)
				else:
					senddata(clientsocket)
		except:
			senddata(clientsocket)
			raise

if __name__ == "__main__":
	addr = (C_host, C_port)
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(addr)
	serversocket.listen(2)
	print "***|SERVER started on %s:%s with buffer size %s bytes|***" % (C_host,C_port,C_buffer) 
	while 1:
		clientsocket, clientaddr = serversocket.accept()
		thread.start_new_thread(handler, (clientsocket, clientaddr))
	serversocket.close()
