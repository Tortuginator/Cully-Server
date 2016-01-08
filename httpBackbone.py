
def decodeHeader(raw_input):
	raw_headers = raw_input.split("\r\n");
	headers = dict();

	if raw_headers[0][:3] == "OPT":#possible response header when browser not identifiable
		return None;	
	elif raw_headers[0][:3] == "GET":#Normal response header
		headers["Request"] = "GET";
		headers["Path"] = raw_headers[0].split(" ")[1];
		headers["Version"] = raw_headers[0].split(" ")[2];
	else:
		return None;
	#handle all possible head fields
	for head in raw_headers:
		if ":" in head:
			tmp = head.split(":");
			headers[tmp[0]] = tmp[1];
		elif len(head) > 1:
			headers["Content"] = head;
	if len(headers) > 1: return None;
	return headers;

def decodeAddress(url):
	if not "?" in url:return None;
	basic = url.split("?");basic = basic[1]

	if "&" in url:
		param = basic.split("&");
	else:
		param = {basic};
	p = dict();
	for a in param:
		if "=" in a:
			b = a.split("=");p[b[0]] = b[1];
	return p;

def encodeResponse(data,type):
	if type == "html":dat_type = "Content-type: text/html";
	elif type == "text":dat_type = "Content-type: text/html";
	elif type == "json":dat_type = "Content-type: application/json";
	elif type == "png":dat_type = "Content-type: image/png";
	elif type == "jpg":dat_type = "Content-type: image/jpg";
	else:dat_type = "Content-type: text/html";

	return 'HTTP/1.1 200 OK' + '\n' + 'Access-Control-Allow-Origin: *' + '\n' + 'Cache-Control: no-cache, no-store, must-revalidate' + '\n' + 'Pragma: no-cache' + '\n' + 'Expires: 0' + '\n' + 'Content-length: ' + str(len(data)) + '\n'+ dat_type + '\n' + '\n' + data
