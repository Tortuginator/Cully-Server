#Functions
def PrintError(Adress,Content):
	ErrorImage = "error.jpg";
	ErrorBackground = "#f3f4f4";
	return '<body style="margin:0px;padding:0px;background-color:' + ErrorBackground + ';"><img src="' + Adress + ErrorImage + '" style="height:600px;display: inline-block;vertical-align: middle;margin-left: auto;margin-right: auto"></src>';

def PrintFullframeImage(Adress,Content):
	return '<body style="margin:0px;padding:0px;background-image:url(\'' + Adress + 'img/' + content + '\');background-position: right top;background-size: 100%;">'

def PrintCostumHTML(Adress,Content):
	return '<body style = "margin:0px;padding:0px;">\n%s\n' % (Content)


#DO NOT EDIT
#Backbone functions for server call and input
def GetBackbone(innerHTML):
	if (innerHTML == None):innerHTML == "";
	typefaceCSS = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,300" rel="stylesheet" type="text/css">';
	htmlCSS = "font-family: 'Open Sans', sans-serif;"
	return "<html style=\"" + htmlCSS + "\">\n" + innerHTML + "\n</body>\n" + typefaceCSS + "\n</html>";

def GetPage(Adress,Type,Content,overlay):
	Type = int(Type);ret = None;
	if str(Type) in functions:
		return GetBackbone(functions[str(Type)](Adress,Content));
	else:
		return GetBackbone(functions['0'](Adress,Content))

#Global Function Register
global functions
functions = {'0':PrintError,'3':PrintCostumHTML,'4':PrintFullframeImage};