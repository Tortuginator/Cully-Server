#I mport
from datetime import datetime
import os
from os import listdir
from os.path import isfile, join
#Global Function Register
global font
font = "Open Sans";#"MS-Comic sans" not allowed to be used "Open sans" recommanded

global ItemStorage
ItemStorage = dict()

#Functions
def PrintError(Address,Content,ID):
	ErrorImage = "error.jpg";
	ErrorBackground = "#f3f4f4";
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-color:' + ErrorBackground + ';"><img src="' + Address + '' + ErrorImage + '" style=" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintFullframeImage(Address,Content,ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-image:url(\'' + Address + 'img/items/' + Content + '\');background-position: right top;background-size: 100%;">'

def PrintCostumHTML(Address,Content,ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;">\n%s\n' % (Content)

def PrintCenteredImage(Address,Content,ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;"><img src="' + Address + 'img/items/' + Content + '" style =" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintYoutube(Address,Content,ID):
	return "<body style = 'font-family:" + font +"!important;margin:0px;padding:0px;background-color:black;'><iframe id='playerId' type='text/html' width='100%' height='100%' src='http://www.youtube.com/embed/" + Content + "?enablejsapi=1&rel=0&playsinline=0&autoplay=1&html5=1' frameborder='0' allowfullscreen>";
def PrintCalendar(Address,Content,ID):
	return '';

def PrintSlideshowImage(Address,Content,ID):
	SlideshowFrameTime = int(Content.split(";")[1])
	StorageLocation = lConfig["Server"]["Storage"] +  "\\slideshows\\" + Content.split(";")[0]

	if os.path.isdir(StorageLocation):
		files = [f for f in listdir(StorageLocation) if isfile(join(StorageLocation, f))];

		#Calculate Current item:
		now = datetime.now()
		delta = now - ItemStorage[ID]
		TimeDifference = int(delta.total_seconds())
		TimeUnits = TimeDifference%(SlideshowFrameTime*len(files))	#Remove Fully Passed frames
		TimeUnits = TimeUnits - (TimeUnits%SlideshowFrameTime)		#Remove the current time in frame
		TimeUnits = TimeUnits / SlideshowFrameTime					#Convert the full seconds to the Frame ID

	else:
		return None
	return '<body style = "font-family:' + font +'!important;background-color:black;margin:0px;padding:0px;"><img src="' + Address + 'img/slideshows/' + Content.split(";")[0] + '/' + files[TimeUnits] + '" style ="max-height: 100%;max-width: 100%;position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintFullIFrame(Address,Content,ID):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;">\n<iframe src="' + Content + '" style="position:fixed; top:0px; left:0px; bottom:0px; right:0px; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999998;">Your browser doesn\'t support iframes</iframe>';


#DO NOT EDIT
#Backbone functions for server call and input
def GetBackbone(innerHTML,debug):
	if (innerHTML == None):innerHTML = "";
	typefaceCSS = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,300" rel="stylesheet" type="text/css">';
	htmlCSS = "font-family: '" + font + "', sans-serif !important;"
	if debug == True:
		debugHTML = '<div style="background-color:black;color:white;position:fixed;top:50px;left:50px;padding:5px;text-align:center;font-size:25;">Developermode <p style="display:inline;color:green;">Active</p> | Connection <p style="display:inline;color:green;">Active</p></div>\n<div id="debug_lower" style="background-color:black;color:white;position:fixed;bottom:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>\n<div id="debug_upper" style="background-color:black;color:white;position:fixed;top:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>\n<div id="special_frame" style=""></div>';
	else:
		debugHTML = '<div id="debug_lower" style="display:none;"></div>\n<div id="debug_upper" style="display:none;"></div>\n<div id="special_frame" style=""></div>';
	return "<html style=\"" + htmlCSS + "\">\n" + innerHTML + "\n</body>\n" + debugHTML + "\n" + typefaceCSS + "\n</html>";

def GetPage(Type,Content,ID,Configuration):
	debug = Configuration["Server"]["Debug"]
	global lConfig
	lConfig = Configuration

	functions = {'0':PrintError,'2':PrintCostumHTML,'3':PrintCostumHTML,'4':PrintFullframeImage,'5':PrintCenteredImage,'6':PrintSlideshowImage,'8':PrintFullIFrame,'9':PrintYoutube};#add your customized functions here 'ID',FuntionName || '0' is predefined error
	Type = int(Type);

	if not ID in ItemStorage:
		ItemStorage[ID] = datetime.now()

	if str(Type) in functions:
		return GetBackbone(functions[str(Type)](Configuration["ADDR"],Content,ID),debug);
	else:
		return GetBackbone(functions['0'](Configuration["ADDR"],Content,ID),debug)
