#Functions
def PrintError(Address,Content):
	ErrorImage = "error.jpg";
	ErrorBackground = "#f3f4f4";
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-color:' + ErrorBackground + ';"><img src="' + Address + ErrorImage + '" style=" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintFullframeImage(Address,Content):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-image:url(\'' + Address + 'img/' + Content + '\');background-position: right top;background-size: 100%;">'

def PrintCostumHTML(Address,Content):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;">\n%s\n' % (Content)

def PrintCenteredImage(Address,Content):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;"><img src="' + Address + 'img/' + Content + '" style =" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintSlideshowImage(Address,Content):
	image = Content.split("\\");
	image = image[len(image)-2] + "\\" + image[len(image)-1]
	return '<body style = "font-family:' + font +'!important;background-color:black;margin:0px;padding:0px;"><img src="' + Address + 'img/' + image + '" style =" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);">' + Content + '</src>';

#DO NOT EDIT
#Backbone functions for server call and input
def GetBackbone(innerHTML,debug):
	if (innerHTML == None):innerHTML == "";
	typefaceCSS = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,300" rel="stylesheet" type="text/css">';
	htmlCSS = "font-family: '" + font + "', sans-serif !important;"
	if debug == True:
		debugHTML = '<div style="background-color:black;color:white;position:fixed;top:50px;left:50px;padding:5px;text-align:center;font-size:25;">Developermode <p style="display:inline;color:green;">Active</p> | Connection <p style="display:inline;color:green;">Active</p></div>\n<div id="debug_lower" style="background-color:black;color:white;position:fixed;bottom:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>\n<div id="debug_upper" style="background-color:black;color:white;position:fixed;top:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>';
	else:
		debugHTML = '<div id="debug_lower" style="display:none;"></div>\n<div id="debug_upper" style="display:none;"></div>';
	return "<html style=\"" + htmlCSS + "\">\n" + innerHTML + "\n</body>\n" + debugHTML + "\n" + typefaceCSS + "\n</html>";

def GetPage(Address,Type,Content,overlay,debug):
	Type = int(Type);ret = None;
	if str(Type) in functions:
		return GetBackbone(functions[str(Type)](Address,Content),debug);
	else:
		return GetBackbone(functions['0'](Address,Content),debug)

#Global Function Register
global functions
functions = {'0':PrintError,'3':PrintCostumHTML,'4':PrintFullframeImage,'5':PrintCenteredImage,'6':PrintSlideshowImage};#add your customized functions here 'ID',FuntionName || '0' is predefined error
global font
font = "Open Sans";#"MS-Comic sans" not allowed to be used "Open sans" recommanded