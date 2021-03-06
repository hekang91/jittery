# experiment.py
import viz
import vizact
import viztask
import itertools
import random
#from pyDOE import *
from fullfact import *

import hardware
import trialData

from params import params

def flattenList(input):
	if isinstance(input[0],tuple) or isinstance(input[0],list):
		return list(itertools.chain.from_iterable(input)) # flatten to unidimensional list
	else: # in the special case that we do not have a nested list, the above crashes as there is nothing to iterate...
		return input
		
		
class Executive:
	# member variables:
	# 	trialSequence 			list containing the IDs of trials to be run
	#   dim						list containing the associated values of the toggle (getTrial in trialData decided what to do with the toggle)
	
	def __init__(self):
		# these are set in createTrials()
		self.trialSequence 	= None
		self.jitter			= []
		self.dim	 		= []	
		self.scene			= []
		self.response		= []
		
	def generateTrials(self):
		fullmat = fullfact([len(params.all_amp),len(params.all_scene),len(params.all_dim)])
		a = tuple(itertools.repeat(fullmat, params.nTrialPerCond))
		b = map(None,*a)
		seq = flattenList(b) 
		order = range(len(seq))
		random.shuffle(order)
		
		self.trialSequence = [seq[i] for i in order]
		
		for each in self.trialSequence:
			self.jitter.append(params.all_amp[int(each[0])]) 
			self.scene.append(params.all_scene[int(each[1])])
			self.dim.append(params.all_dim[int(each[2])]) 			
	
	def startSession(self):
		self.generateTrials()
		viztask.schedule(self.runExperiment)
		
	def runExperiment(self):
		yield self.doTrials()
		
	def saveResponseData(self,subjectName):
		result = open('./data/'+str(subjectName)+'_mode_'+ str(params.displayMode) + '.txt', 'a') 
		
		for each in self.scene:
			result.write(str(each) + ' ')
		result.write('\n')
		
		for each in self.dim:
			result.write(str(each) + ' ')
		result.write('\n')
		
		for each in self.jitter:
			result.write(str(each) + ' ')
		result.write('\n')
		
		for each in self.response:
			result.write(str(each) + ' ')
		result.write('\n')
		
	def setGaussionFuzzy(self):
		import vizfx.postprocess
		from vizfx.postprocess.blur import GaussianBlurEffect
		effect = GaussianBlurEffect(blurRadius=params.BlurRadius)
		vizfx.postprocess.addEffect(effect)
		return effect
		
	def removeGaussionFuzzy(self,effect):
		effect.remove()
		
	def doTrials(self):
		print '==========='
		print '--expt start--'
		viz.mouse.setVisible(viz.OFF)
		# any error during the experiments needs to be caught here (as this function is run through the scheduler)
		try:
			effect = self.setGaussionFuzzy()
			for whatJitter,whatScene,whatDim in zip(self.jitter,self.scene,self.dim):
				
				print whatJitter,whatScene,whatDim # for debug
				trial = trialData.ActiveTrial(whatScene,whatDim,whatJitter,params.walkSpeedZ)
				
				yield trial.doTrial(self.response)
				trial.writeToFile(params.subjectName)
			
			self.removeGaussionFuzzy(effect)
			#print 'response = ',self.response # for debug
			print 'all trials finished'
						
			self.saveResponseData(params.subjectName)	
			
			viz.mouse.setVisible(viz.ON)
			viz.quit()
		except:
			# close screen on error
			viz.logError('** Caught exception in expt.doTrials')
			viz.mouse.setVisible(viz.ON)
			viz.quit()
			raise
			

# if executing this, call main
if __name__ == "__main__":
    import main
    main.main()