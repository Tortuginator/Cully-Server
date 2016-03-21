from datetime import datetime
import pages
import json
class FrameTimer:
	@staticmethod
	def GetFrameIndex(Frames,StartTime):
		#Get Time Difference from START to NOW
		now = datetime.now()
		delta = now - StartTime
		TimeDifference = int(delta.total_seconds())

		#Remove Passed Cycles
		inCycleTime = TimeDifference%(FrameTimer.GetCycleTime(Frames))
		
		#Only for Debug
		print FrameTimer.GetCycleTime(Frames),inCycleTime
		print "Corresponding item",FrameTimer.GetItemByTime(Frames,inCycleTime)
		
		#Return Item to the corresponding time
		return FrameTimer.GetItemByTime(Frames,inCycleTime)

	@staticmethod
	def GetItemByTime(Frames,TargetTime):
		tmpTime = 0
		for frameID,time in enumerate(Frames):
			tmpTime += int(time)
			if tmpTime > TargetTime:#when sum of time is larger than the target time
				return int(frameID)

	@staticmethod
	def GetCycleTime(Frames):
		tmp = 0; 
		for FrameID,time in enumerate(Frames):
			tmp +=int(time)
		return tmp

class FrameContent:
	@staticmethod
	def GenerateFrame(Itype,Icontent,Iname,Iid,Configuration,Ext_Command):
		dPSI = FrameContent.ReadPSI()
		produced = {"content":FrameContent.HTMLframe(Itype,Icontent,Configuration),"id":Iid,"type":Itype,"name":Iname,"PSI":{"Int":int(dPSI["PSI"]),"time":str(dPSI["time"])}}
		if Ext_Command != "" and Configuration["Server"]["Command"] == True and Ext_Command != "NULL":#decide if there is to be a command included
			produced["command"] = Ext_Command
		return produced

	@staticmethod
	def InternalError(Detail = None):
		return {"content":"<center><h1>Internal Server Error</h1></center>","id":-1,"type":0,"name":"Error","debug-detail":Detail}


	@staticmethod
	def HTMLframe(Itype,Icontent,Configuration):
		return pages.GetPage(Itype,Icontent,Configuration)

	@staticmethod
	def ReadPSI():
		try:
			file_psi = open('psi.val', 'r');
			dPSI = file_psi.readlines();
			dPSI = json.loads(dPSI[0]);
		except Exception,e:
			dPSI = {"psi":-1,"time":0}
			print "FAILED to read and/or decode the PSI file/value"
		return dPSI