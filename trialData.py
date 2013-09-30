import viz
import viztask
import vizact
import vizshape
import os

#import params
import hardware
from params import params

lastTrials = params.nTrials

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
		if id == 99:  #'grass ground':
			import shader_scene
			class RuralPit:
				def __init__(self):
					#Setup lighting
					#self.light = viz.add(viz.LIGHT)
					#self.light.position(0,1,0,0)
					#self.light.disable()
					#self.env = viz.add(viz.GROUP)

					#self.sky = self.env.add('RuralPit/ruralPit_sky.ive')
					#self.sky.appearance(viz.DECAL)
					#self.sky.apply(viz.addUniformFloat('ambient',1))
					
					#for eachrow in range(20):
						#for eachcol in range(20):
					#self.ground = viz.addChild('ground_grass.osgb')
					#self.ground.setScale([1,1,1])
							#self.ground.setPosition([eachrow*50-500,0,eachcol*50-500])
					self.ground = viz.addChild('sky_day.osgb')
					#viz.clearcolor(viz.SKYBLUE)
					#env = viz.addEnvironmentMap('sky.jpg') 
					#sky = viz.addCustomNode('skydome.dlc') 
					#sky.texture(env)
				def visible(self,Boolean):
					#self.sky.visible(Boolean)
					#for eachrow in range(20):
						#for eachcol in range(20):
					self.ground.visible(Boolean)
				def remove(self):
					#self.sky.remove()
					#for eachrow in range(20):
						#for eachcol in range(20):
					self.ground.remove()
					viz.clearcolor(viz.BLACK)
							
			self.curr_scene = RuralPit()
		
		if id == 1:
			self.curr_scene = viz.addChild('ground.osgb')


		if id == 0: #'sphere':
			import vizshape
			self.curr_scene = vizshape.addSphere()
			self.curr_scene.setScale([params.sphereScale,params.sphereScale,params.sphereScale])
			self.curr_scene.setPosition([0,params.sphereHeight,params.sphereDistance])
			self.curr_scene.color(viz.BLUE)
		if id == 101: #'room':
			#viz.add('piazza.osgb')
			self.curr_scene = viz.add('gallery.osgb')
			self.curr_scene.setPosition([0,0,params.roomPosOffset])
		'''
		if id == 102: #'ruralPit': not used so far
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
		#self.fixation = viz.addText3D('+',pos=[0,2,params.sphereDistance])
		self.fixation = viz.addText('+',viz.SCREEN) 
		self.fixation.setPosition([0.5,0.5,0])
		#self.fixation.alignment(viz.ALIGN_CENTER_BOTTOM)
		self.fixation.alignment(viz.ALIGN_CENTER_CENTER)
		self.fixation.setScale([0.5,0.5,0.5])
		
	def closeScene(self):
		self.curr_scene.visible(False)
		self.curr_scene.remove()
		
	def closeFixation(self):
		self.fixation.visible(False)
		self.fixation.remove()


class Instruction:
	def __init__(self):
		self.textTrials = None
		self.textChoice = None
	def initChoice(self):
		self.textChoice = viz.addText('Jittery or not?',viz.SCREEN)
		self.textChoice.alignment(viz.ALIGN_CENTER_CENTER)
		self.textChoice.setPosition([0.5,0.5,0])
	def playStartSound(self):
		#startSound = viz.addAudio('notify.wav')
		params.startSound.play()
	def playEndSound(self):
		#endSound = viz.addAudio('chimes.wav')
		params.endSound.play()
	def updateTrials(self):
		global lastTrials
		self.textTrials = viz.addText('last '+ str(lastTrials) +' trials',viz.SCREEN) 
		self.textTrials.alignment(viz.ALIGN_RIGHT_BOTTOM)
		self.textTrials.setPosition([0.95,0.05,0])
		lastTrials = lastTrials - 1
		self.textTrials.visible(True)
	def closeTrials(self):
		self.textTrials.visible(False)
		self.textTrials.remove()
	def closeChoice(self):
		self.textChoice.visible(False)
		self.textChoice.remove()

def getTrial(scene,dim,jitter):
	t = ActiveTrial(scene,dim,jitter)
	return t


def judgeTask(response):
	while True:
		thisResp = -1 
		#Wait for either 'y' or 'n' key to be pressed
		d = yield viztask.waitKeyDown( ['65361','65363'] ) # left and right
		if d.key = '65361':
			thisResp = 1 # left, jitter, yes
		else:
			thisResp = 0 # right, no jitter, no
		response.append(thisResp)
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
			global headLink
			headLink = viz.link(headTrack, viz.MainView)

			def setTrackerOffset():
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

			setTrackerOffset()
			

			vizact.onupdate(viz.PRIORITY_PLUGINS+3, headLink.update)
			
			scene = Scene()
			scene.setupScene(self.scene)
			
			collectDataTask = viztask.schedule(self.collectData())
			
			scene.setupFixation()
			thisIns.playStartSound()
			#if self.scene == 0:
				#scene.closeFixation()
			
			yield viztask.waitTime(params.nSecPerTrial)
			scene.closeScene()
			collectDataTask.kill()
			scene.closeFixation()			
			
			thisIns.playEndSound()
			thisIns.initChoice()
			thisIns.updateTrials()
			
			yield judgeTask(response)
			#yield viztask.waitKeyDown(' ')	
			
			thisIns.closeChoice()
			thisIns.closeTrials()
			
			isDoneWithTrial = True
	
	def writeToFile(subjectName):
		dataDir = './data_head/'
        if not os.path.isdir(dataDir):
            os.makedirs(dataDir)    # this does recursive directory creation so we're always good
        
		dataFileName = str(subjectName) + '_T_' + str(params.nTrials - lastTrials + 1) + '.txt'
		dataFile = open(dataDir + '/' + dataFileName, "w")
		
		# write data
        for sample in self.sampleList:
            dataFile.write(str(sample))
            dataFile.write('\n')
            
        # done
        dataFile.flush()
        bdataFile.close()
			
	def collectData(self):
		class Sample:
			def __init__(self):
				self.time = 0
				self.trackerPos = [0,0,0]
				self.VRPos = [0,0,0]
				self.trackerOri = [0,0,0]
				self.VROri = [0,0,0]
			def __str__(self):
				temp = [self.time] + self.trackerPos + self.VRPos + self.trackerOri + self.VROri
				return iterable2str(temp,'\t')
		while True:
			s = Sample()
			s.time          = viz.tick()
			#s.trackerPos    = headTrack.getPosition()
			s.trackerPos    = trackerLinkableInt.getPosition()
			s.VRPos    = viz.MainView.getPosition()
			s.trackerOri    = headTrack.getEuler()
			s.VROri    = viz.MainView.getEuler()
			#print s
			self.sampleList.append(s)
			#self.saveHeadData()
			yield viztask.waitTime(1/60)
	
	def remove(self):
        for item in self.removeList:
            item.remove()
	
	'''		
	def saveHeadData(self):
		result = open(str(subjectName)+str(params.nTrials - lastTrials + 1)+'.txt', 'a') 
		result.write( str(s) + '\n')
	'''
	


# if executing this, call main
if __name__ == "__main__":
    import main
    main.main()