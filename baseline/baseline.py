
import viz
import viztask
import vizcam
import random
import os

class Params:
	nSecPerTrial = 30 # for debug
	#nSecPerTrial = 60

	viewOffset                  = [0.05, -0.2, 0.085]
	#trackerSpaceOffset          = [-0.36,0.11,-0.42] # for gallery
	trackerSpaceOffset          = [-1.6,0.11,5.8] # for rural pit: startPos = [-1.5,1.63,6.5]
	trackerSpaceRot             = [5,0,0] # for rural pit: startOri = [5,0,0]
	
	walkSpeed = 1
	

global params
params = Params()

class ParamsJitter:
	dim = 0 #0:x, 1:y, 2:z
	#face Z postive: 0:lr, 1:ud, 2: bf 
	amp = 0.00



def getOptiTrackTracker():
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
		pj = ParamsJitter()
		whiteNoise = random.gauss(0,1)
		newPos = trackerLinkableInt.getPosition()
		newPos[pj.dim] = newPos[pj.dim] + pj.amp*whiteNoise
		newPos[2] = newPos[2] + speedZ*(viz.tick()-startTime)
		trackerLinkable.setPosition(newPos)	
	
	vizact.onupdate(viz.PRIORITY_PLUGINS+2,applyJitter)	
	
	return trackerLinkable



def iterable2str(seq, sep): 
    it = iter(seq)
    sep = str(sep)
    try:
        first = it.next()
    except StopIteration:
        return []
    
    def add_sep(r, v):
        r += [sep, str(v)]
        return r
    
    return ''.join(reduce(add_sep, it, [str(first)]))   # TODO: check precision, need to increase?



class ActiveTrial:
	def __init__(self):
		global sampleList
		self.sampleList 	            = []
	

	def collectData(self):
		class Sample:
			def __init__(self):
				self.time = 0
				self.trackerPos = [0,0,0]
				self.VRPos = [0,0,0]
				self.trackerOriEuler = [0,0,0]
				self.VROriEuler = [0,0,0]
				#self.trackerOriQuat = [0,0,0,0]
			def __str__(self):
				temp = [self.time] + self.trackerPos + self.VRPos + self.trackerOriEuler + self.VROriEuler#+ self.trackerOriQuat
				return iterable2str(temp,'\t')
		while True:
			global s
			s = Sample()
			s.time          = viz.tick()
			s.trackerPos    = headTrack.getPosition()
			s.VRPos    = viz.MainView.getPosition()
			s.trackerOriEuler    = headTrack.getEuler()
			#s.trackerOriQuat    = headTrack.getQuat()
			s.VROriEuler   = viz.MainView.getEuler()
			#s.VROriQuat    = viz.MainView.getQuat()
			print s
			self.sampleList.append(s)
			self.saveData(subjectName,status,displayMode)
			yield viztask.waitTime(1/60)
			
	def saveData(self,subjectName,status,displayMode):
		#result = open(str(subjectName)+'_baseline_'+str(status)+'.txt', 'a') 
		result = open(str(subjectName)+'_baseline_mode'+str(displayMode)+'_'+str(status)+'.txt', 'a') 
		#result.write('scene,dim,jitter,response\n\n')
		result.write( str(s) + '\n')
			
	def doTrial(self,nSecPerTrial):
		isDoneWithTrial = False
		while not isDoneWithTrial:
			collectDataTask = viztask.schedule(self.collectData())
			yield viztask.waitTime(params.nSecPerTrial)
			isDoneWithTrial = True
			collectDataTask.kill()



class Executive:
	def startSession(self):
		viztask.schedule(self.runExperiment)
		
	def runExperiment(self):
		yield self.doTrials()
		
	def doTrials(self):
		try:
			my_trial = ActiveTrial()
			yield my_trial.doTrial(params.nSecPerTrial)
			#my_trial.writeToFile(subjectName,status)
			viz.quit()
		except:
			# close screen on error
			viz.logError('** Caught exception in expt.doTrials')
			viz.quit()
			raise


def setTrackerOffset():
	global headTrack, headLink
	
	headTrack = getOptiTrackTracker()
	headLink = viz.link(headTrack, viz.MainView)
	
	# position (as this offset is local in head space)
	if not all(v == 0 for v in params.viewOffset):
		# we've got a non-zero link offset:
		headLink.preTrans(params.viewOffset)
	
	# setup an offset to position the VR world relative to the tracker space
	# any tracker space rotation is added below to the mirrorRotationOperator
	if not all(v == 0 for v in params.trackerSpaceOffset):
		# we've got a non-zero link offset:
		headLink.postTrans(params.trackerSpaceOffset)
	
	if not all(v == 0 for v in params.trackerSpaceRot):
		# we've got a non-zero link offset:
		headLink.postEuler(params.trackerSpaceRot)


import shader_scene
class RuralPit:
	def __init__(self):
		#Setup lighting
		self.light = viz.add(viz.LIGHT)
		self.light.position(0,1,0,0)
		self.light.disable()
		
		self.env = viz.add(viz.GROUP)
		#Add room
		self.room = self.env.add('RuralPit/ruralPit.ive')
		shader_scene.process(self.room)

		sky = self.env.add('RuralPit/ruralPit_sky.ive')
		sky.appearance(viz.DECAL)
		sky.apply(viz.addUniformFloat('ambient',1))



def main():

	global subjectName,status,displayMode
	subjectName = str(viz.input('Enter subject name'))
	if subjectName == '': raise RuntimeError('Need subject name')	
	
	
	status = str(viz.input('stand or walk? (input s/w)'))
	if status != 's' and status != 'w': raise RuntimeError('input s/w!')
	
	global speedZ
	if status == 's':
		speedZ = 0
	elif status == 'w':
		speedZ = params.walkSpeed
	
	
	displayMode = str(viz.input('Enter display mode -- [1] RB dirve HMD [2] RB drive screen [3] RB with Screen: 1/2/3'))

	global headTrack	
	if displayMode == '1':
		viz.setDisplayMode(2560, 1024, 32, 60)
		import nvis
		nvis.nvisorSX60()

		setTrackerOffset()
		vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)
	elif displayMode == '2':
		viz.window.setFullscreenMonitor(1)

		setTrackerOffset()
		vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)		
	elif displayMode == '3':
		viz.window.setFullscreenMonitor(1)
		headTrack = getOptiTrackTracker()
	else:
		raise RuntimeError('Wrong display mode')
		
	
	viz.setOption('viz.fullscreen', 1)	
	#viz.setOption('viz.dwm_composition', 0)	# disable DWM composition to help with reliable timing
	#viz.setOption('viz.prevent_screensaver', 1)
	
	
	viz.go()	
	random.seed()
	curr_scene = RuralPit()
	global startTime
	startTime = viz.tick()


	expt = Executive()
	try:
		expt.startSession()
	except:
		viz.logError('** Caught exception in main')
		viz.quit()
		raise
		


if __name__ == '__main__':
	main()
