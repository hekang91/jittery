
import viz
import viztask
import vizcam
import random
import os

global nSecPerTrial
nSecPerTrial = 30 # for debug
#nSecPerTrial = 60



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
		pj = ParamsJitter()
		whiteNoise = random.gauss(0,1)
		newPos = trackerLinkableInt.getPosition()
		newPos[pj.dim] = newPos[pj.dim] + pj.amp*whiteNoise
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
	
	'''
	def writeToFile(self,subjectName,status):
		# create data directory if needed
		dataDir = './'
		if not os.path.isdir(dataDir):
			os.makedirs(dataDir)    # this does recursive directory creation so we're always good
		
		# create filename and open file for writing
		dataFileName = subjectName + str(status) + '.txt'
		dataFile = open(dataDir + dataFileName, "w")
		
		# write data
		# header
		dataFile.write(str(self))
		dataFile.write('\n')

        # data
        for sample in self.sampleList:
            dataFile.write(str(sample))
            dataFile.write('\n')

        # done
        dataFile.flush()
        dataFile.close()
    '''


	def collectData(self):
		class Sample:
			def __init__(self):
				self.time = 0
				self.subjectPos = [0,0,0]
				self.subjectOriEuler = [0,0,0]
				self.subjectOriQuat = [0,0,0,0]
			def __str__(self):
				temp = [self.time] + self.subjectPos + self.subjectOriEuler + self.subjectOriQuat
				return iterable2str(temp,'\t')
		while True:
			global s
			s = Sample()
			s.time          = viz.tick()
			s.subjectPos    = headTrack.getPosition()
			#s.subjectPos    = viz.MainView.getPosition()
			s.subjectOriEuler    = headTrack.getEuler()
			s.subjectOriQuat    = headTrack.getQuat()
			#s.subjectOriEuler   = viz.MainView.getEuler()
			#s.subjectOriQuat    = viz.MainView.getQuat()
			#print s
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
			yield viztask.waitTime(nSecPerTrial)
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
			yield my_trial.doTrial(nSecPerTrial)
			#my_trial.writeToFile(subjectName,status)
			viz.quit()
		except:
			# close screen on error
			viz.logError('** Caught exception in expt.doTrials')
			viz.quit()
			raise




def main():

	global subjectName,status,displayMode
	subjectName = str(viz.input('Enter subject name'))
	if subjectName == '': raise RuntimeError('Need subject name')	
	status = str(viz.input('stand or walk? (input s/w)'))
	if status != 's' and status != 'w': raise RuntimeError('input s/w!')
	displayMode = str(viz.input('Enter display mode -- [1] RB dirve HMD [2] RB drive screen [3] RB with Screen: 1/2/3'))

	global headTrack	
	if displayMode == '1':
		viz.setDisplayMode(2560, 1024, 32, 60)
		import nvis
		nvis.nvisorSX60()
		headTrack = getOptiTrackTracker()
		headLink = viz.link(headTrack, viz.MainView)
		vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)
	elif displayMode == '2':
		viz.window.setFullscreenMonitor(1)
		headTrack = getOptiTrackTracker()
		headLink = viz.link(headTrack, viz.MainView)
		vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)		
	elif displayMode == '3':
		viz.window.setFullscreenMonitor(1)
		headTrack = getOptiTrackTracker()
	else:
		raise RuntimeError('Wrong display mode')
		
	
	viz.setOption('viz.fullscreen', 1)	
	#viz.setOption('viz.dwm_composition', 0)	# disable DWM composition to help with reliable timing
	#viz.setOption('viz.prevent_screensaver', 1)
	viz.add('piazza.osgb')
	viz.go()	
	random.seed()
	


	expt = Executive()
	try:
		expt.startSession()
	except:
		viz.logError('** Caught exception in main')
		viz.quit()
		raise
		


if __name__ == '__main__':
	main()
