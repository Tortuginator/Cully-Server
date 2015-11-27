#Functions
def PrintError(Adress,Content):
	ErrorImage = "error.jpg";
	ErrorBackground = "#f3f4f4";
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-color:' + ErrorBackground + ';"><img src="' + Adress + ErrorImage + '" style=" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

def PrintFullframeImage(Adress,Content):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;background-image:url(\'' + Adress + 'img/' + Content + '\');background-position: right top;background-size: 100%;">'

def PrintCostumHTML(Adress,Content):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;">\n%s\n' % (Content)

def PrintCenteredImage(Adress,Content):
	return '<body style = "font-family:' + font +'!important;margin:0px;padding:0px;"><img src="' + Adress + 'img/' + Content + '" style =" position: fixed;top: 50%;left: 50%;transform: translate(-50%, -50%);"></src>';

#DO NOT EDIT
#Backbone functions for server call and input
def GetBackbone(innerHTML,debug):
	if (innerHTML == None):innerHTML == "";
	typefaceCSS = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,300" rel="stylesheet" type="text/css">';
	htmlCSS = "font-family: 'Open Sans', sans-serif !important;"
	if debug == True:
		debugHTML = '<div id="debug_lower" style="background-color:black;color:white;position:fixed;bottom:50px;right:50px;padding:5px;text-align:center;font-size:25;"></div>';
	else:
		debugHTML = '<div id="debug_lower" style="display:none;"></div>';
	return "<html style=\"" + htmlCSS + "\">\n" + innerHTML + "\n</body>\n" + debugHTML + "\n" + typefaceCSS + "\n</html>";

def GetPage(Adress,Type,Content,overlay,debug):
	Type = int(Type);ret = None;
	if str(Type) in functions:
		return GetBackbone(functions[str(Type)](Adress,Content),debug);
	else:
		return GetBackbone(functions['0'](Adress,Content),debug)

#Global Function Register
global functions
functions = {'0':PrintError,'3':PrintCostumHTML,'4':PrintFullframeImage,'5':PrintCenteredImage};
global font
font = "Open Sans";