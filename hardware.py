# hardware.py
import viz
import vizact
import random
from params import params


# actually i don't like to mix the hardware configuration with the experiment setting (apply jittery)
# any other way of coding?

def getOptiTrackTracker(dim,jitter,speedZ,startTime):
	global trackerLinkableInt
	vrpn7 = viz.add('vrpn7.dle')
	TRACKER_ID = "Tracker"
	VRPN_MACHINE = "localhost"
	trackerLinkable = vrpn7.addTracker(TRACKER_ID+'@'+VRPN_MACHINE,0)
	
	trackerLinkableInt = trackerLinkable
	trackerLinkable = viz.addGroup()
	
	def transformQuat():
		if params.displayMode == '1':
			newQuat = [
				trackerLinkableInt.getQuat()[0] * -1, 
				trackerLinkableInt.getQuat()[1] * -1, 
				trackerLinkableInt.getQuat()[2] * -1,
				trackerLinkableInt.getQuat()[3] * 1
				]
		elif params.displayMode == '2':
			newQuat = [
				trackerLinkableInt.getQuat()[0] * -1, 
				trackerLinkableInt.getQuat()[1] * -1, 
				trackerLinkableInt.getQuat()[2] * -1,
				#0 * -1,
				trackerLinkableInt.getQuat()[3] * 1
				]
		elif params.displayMode == '3':
			newQuat = [0,0,0,1]
		
		trackerLinkable.setQuat(newQuat)
	
	vizact.onupdate(viz.PRIORITY_PLUGINS+1,transformQuat)	
	
	
	def applyJitter():
		whiteNoise = random.gauss(0,1)
		if params.displayMode != '3':
			newPos = trackerLinkableInt.getPosition()
			newPos[dim] = newPos[dim] + jitter*whiteNoise
			newPos[2] = newPos[2] + speedZ*(viz.tick()-startTime)
		elif params.displayMode == '3':
			newPos = [0,0,0]
			newPos[1] = params.eyeHeight
			newPos[dim] = newPos[dim] + jitter*whiteNoise
			newPos[2] = 0 + speedZ*(viz.tick()-startTime)
			
		trackerLinkable.setPosition(newPos)	
	
	vizact.onupdate(viz.PRIORITY_PLUGINS+2,applyJitter)	
	
	return (trackerLinkable,trackerLinkableInt)
	
	

# the monitor and helmet display settings
def setupGfx():	
	if params.displayMode == '1':
		viz.setDisplayMode(2560, 1024, 32, 60)
		import nvis
		nvis.nvisorSX60()
		
	elif params.displayMode == '2' or params.displayMode == '3':
		viz.window.setFullscreenMonitor(1)
		
	else:
		raise RuntimeError('Wrong display mode')
	
	viz.setOption('viz.fullscreen', 1)	
	viz.setOption('viz.dwm_composition', 0)	# disable DWM composition to help with reliable timing
	viz.setOption('viz.prevent_screensaver', 1)
	viz.setMultiSample(False)

	#viz.MainScene.enable(viz.POINT_SMOOTH,viz.NICE)
	viz.go()

# if executing this, call main
if __name__ == "__main__":
    import main
    main.main()	