import viz
import viztask
import vizact
import vizshape

import params
import hardware


params = params.Params()
lastTrials = params.nTrials # global variable is not a good way

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

	
class Scene:
	def __init__(self):
		self.id = 'None'
		self.curr_scene = None
		self.fixation = None
		
	def setupScene(self,id):
		if id == 0: #'sphere':
			import vizshape
			self.curr_scene = vizshape.addSphere()
			self.curr_scene.setScale([params.sphereScale,params.sphereScale,params.sphereScale])
			self.curr_scene.setPosition([0,params.sphereHeight,params.sphereDistance])
			self.curr_scene.color(viz.BLUE)
		if id == 1: #'room':
			#viz.add('piazza.osgb')
			self.curr_scene = viz.add('gallery.osgb')
			self.curr_scene.setPosition([0,0,params.roomPosOffset])
		'''
		if id == 2: #'ruralPit': not used so far
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
				
			self.curr_scene = RuralPit()
		'''
			
	def setupFixation(self):
		self.fixation = viz.addText3D('+',pos=[0,2,params.sphereDistance]) 
		self.fixation.alignment(viz.ALIGN_CENTER_BOTTOM) 
		self.fixation.setScale([0.7,0.7,0.7]) 
		
	def closeScene(self):
		self.curr_scene.visible(False)
		
	def closeFixation(self):
		self.fixation.visible(False)


class Instruction:
	def __init__(self):
		self.textTrials = None
		self.textChoice = None
	def initChoice(self):
		self.textChoice = viz.addText('Jittery or not?',viz.SCREEN)
		self.textChoice.alignment(viz.ALIGN_CENTER_CENTER)
		self.textChoice.setPosition([0.5,0.5,0])
	def updateTrials(self):
		self.textTrials = viz.addText('last '+ str(lastTrials) +' trials',viz.SCREEN) 
		self.textTrials.alignment(viz.ALIGN_RIGHT_BOTTOM)
		self.textTrials.setPosition([0.95,0.05,0])
		global lastTrials
		lastTrials = lastTrials - 1
		self.textTrials.visible(True)
	def closeTrials(self):
		self.textTrials.visible(False)
	def closeChoice(self):
		self.textChoice.visible(False)


def getTrial(scene,dim,jitter):
	t = ActiveTrial(scene,dim,jitter)
	return t


def judgeTask(response):
	while True:
		#Wait for either 'y' or 'n' key to be pressed
		d = yield viztask.waitKeyDown( ['65361','65363'] ) # left and right
		response.append(d.key)
		return


class ActiveTrial:
	def __init__(self,scene,dim,jitter,speedZ):
		self.sampleList = []
		self.scene = scene
		self.dim = dim
		self.jitter = jitter
		self.speedZ = speedZ
		self.startTime = 0
		
	def doTrial(self,response):
		isDoneWithTrial = False
		thisIns = Instruction()
		while not isDoneWithTrial:
			self.startTime = viz.tick()
			headTrack = hardware.getOptiTrackTracker(self.dim,self.jitter,self.speedZ,self.startTime)
			headLink = viz.link(headTrack, viz.MainView)
			vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)
			
			scene = Scene()
			scene.setupScene(self.scene)
			scene.setupFixation()
			
			if self.scene == 0:
				scene.closeFixation()
			
			yield viztask.waitTime(params.nSecPerTrial)
			scene.closeScene()
			scene.closeFixation()			
			
			thisIns.initChoice()
			thisIns.updateTrials()
			
			yield judgeTask(response)
			#yield viztask.waitKeyDown(' ')	
			
			thisIns.closeChoice()
			thisIns.closeTrials()
			
			isDoneWithTrial = True
			
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

