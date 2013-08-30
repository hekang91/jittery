
import viz
import viztask
import vizcam
import random


class ParamsJitter:
	dim = 0 #0:x, 1:y, 2:z
	#face Z postive: 0:lr, 1:ud, 2: bf 
	amp = 0.01



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
		self.sampleList 	            = []
	def collectData(self):
		class Sample:
			def __init__(self):
				self.time = 0
				self.subjectPos = [0,0,0]
				#self.subjectOri = [0,0,0]
				self.subjectOri = [0,0,0,0]
			def __str__(self):
				temp = [self.time] + self.subjectPos + self.subjectOri
				return iterable2str(temp,'\t')
		while True:
			s = Sample()
			s.time          = viz.tick()
			#s.subjectPos    = headTrack.getPosition()
			s.subjectPos    = viz.MainView.getPosition()
			#s.subjectOri    = headTrack.getEuler()
			#s.subjectOri    = viz.MainView.getEuler()
			s.subjectOri    = viz.MainView.getQuat()
			print s
			self.sampleList.append(s)
			yield viztask.waitTime(1/60)



import viz
viz.setDisplayMode(2560, 1024, 32, 60)
viz.setOption('viz.fullscreen', 1)
#viz.setOption('viz.dwm_composition', 0)	# disable DWM composition to help with reliable timing
#viz.setOption('viz.prevent_screensaver', 1)
import nvis
nvis.nvisorSX60()

viz.add('piazza.osgb')
viz.go()

random.seed()
headTrack = getOptiTrackTracker()

headLink = viz.link(headTrack, viz.MainView)
vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)


my_trial = ActiveTrial()
viztask.schedule(my_trial.collectData())
