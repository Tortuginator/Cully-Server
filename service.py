import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import server
import sys
import datetime
import logging

from threading import Thread

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "DisplayServer"
    _svc_display_name_ = "Display Server"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)


    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
	self.main();

    def main(self):
		logging.basicConfig(filename='C:\SID\PY_server\logs\log' + datetime.datetime.now().strftime("%Y%m%d%H%M") + ".txt", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
		while True:
			try:
				server.init()
				server.main("C:\\SID\\PY_server\\config.json");
			except Exception,e:
				servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,0,(self._svc_name_,''))
				raise

if __name__ == '__main__':
    	win32serviceutil.HandleCommandLine(AppServerSvc)