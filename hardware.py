# hardware.py
import viz
import vizact
import random

# actually i don't like to mix the hardware configuration with the experiment setting (apply jittery)
# any other way of coding?

def getOptiTrackTracker(dim,jitter,speedZ,startTime):
	vrpn7 = viz.add('vrpn7.dle')
	TRACKER_ID = "Tracker"
	VRPN_MACHINE = "localhost"
	trackerLinkable = vrpn7.addTracker(TRACKER_ID+'@'+VRPN_MACHINE,0)
	
	trackerLinkableInt = trackerLinkable
	trackerLinkable = viz.addGroup()
	
	def transformQuat():
		#trackerLinkable.setPosition(trackerLinkableInt.getPosition())
		#newEuler = [
		#	trackerLinkableInt.getEuler()[0] * -1, 
		#	trackerLinkableInt.getEuler()[1] * 1, 
		#	trackerLinkableInt.getEuler()[2] * 1
		#	]
		#trackerLinkable.setEuler(newEuler)
		newQuat = [
			trackerLinkableInt.getQuat()[0] * -1, 
			trackerLinkableInt.getQuat()[1] * -1, 
			trackerLinkableInt.getQuat()[2] * -1,
			trackerLinkableInt.getQuat()[3] * 1
			]
		#trackerLinkable.setEuler(newEuler)
		trackerLinkable.setQuat(newQuat)
	
	vizact.onupdate(viz.PRIORITY_PLUGINS+1,transformQuat)	
	
	
	def applyJitter():
		global prePosZ
		whiteNoise = random.gauss(-0.5,0.5)
		newPos = trackerLinkableInt.getPosition()
		newPos[dim] = newPos[dim] + jitter*whiteNoise
		newPos[2] = newPos[2] + speedZ*(viz.tick()-startTime)
		trackerLinkable.setPosition(newPos)	
	
	vizact.onupdate(viz.PRIORITY_PLUGINS+2,applyJitter)	
	
	return trackerLinkable


# the monitor and helmet display settings
def setupGfx():
	viz.setDisplayMode(2560, 1024, 32, 60)
	viz.setOption('viz.fullscreen', 1)
	#viz.setOption('viz.dwm_composition', 0)	# disable DWM composition to help with reliable timing
	#viz.setOption('viz.prevent_screensaver', 1)
	import nvis
	nvis.nvisorSX60()
	viz.go()
	