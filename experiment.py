# experiment.py
import viz
import vizact
import viztask
import itertools
import random

import params
import hardware
import trialData

params = params.Params()


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
		self.dim	 		= None	
		self.scene			= None
		self.response		= []
	def generateTrials(self):
		a = tuple(itertools.repeat(params.all_amp, params.nTrialPerCond)) # repeat conditionIDs nTrialPerCond times
		b = map(None,*a)                                            	# combine over second dimension (think transpose in matlab)
		self.trialSequence = flattenList(b) 							# flatten into unidimensional array
	
		dim     = [0]*(params.nTrialPerCond/2)
		dim[:0] = [1]*(params.nTrialPerCond/2)
		dim     = [x[:] for x in itertools.repeat(dim, len(params.all_amp))] # repeat toggle for each condition, doing deep copy
		self.dim= flattenList(dim)
		
		scene     = [0]*(params.nTrialPerCond/4)
		scene[:0] = [1]*(params.nTrialPerCond/4)
		scene     = [x[:] for x in itertools.repeat(scene, len(params.all_amp)*2)]
		self.scene= flattenList(scene)
		
	
		order = range(len(self.trialSequence))
		random.shuffle(order)
		self.trialSequence = [self.trialSequence[i] for i in order]
		self.dim        = [self.dim[i]        for i in order]
		self.scene        = [self.scene[i]        for i in order]
		
		#print 'jitter = ',self.trialSequence
		#print 'dim = ',self.dim
		#print 'scene = ',self.scene
	
	def startSession(self):
		self.generateTrials()
		viztask.schedule(self.runExperiment)
		
	def runExperiment(self):
		yield self.doTrials()
		
	def saveData(self):
		result = open('result.txt', 'a') 
		result.write('scene,dim,jitter,response\n\n')
		result.write(str(self.scene) + '\n')
		result.write(str(self.dim) + '\n')
		result.write(str(self.trialSequence) + '\n')
		result.write(str(self.response) + '\n')
		
	def doTrials(self):
		print '==========='
		print '--expt start--'

		# any error during the experiments needs to be caught here (as this function is run through the scheduler)
		try:
			for whatJitter,whatScene,whatDim in zip(self.trialSequence,self.scene, self.dim):
				
				#print whatJitter,whatScene,whatDim # for debug
				trial = trialData.ActiveTrial(whatScene,whatDim,whatJitter)
				
				yield trial.doTrial(self.response)

			#print 'response = ',self.response # for debug
			print 'all trials finished'
						
			self.saveData()			
			
			viz.quit()
		except:
			# close screen on error
			viz.logError('** Caught exception in expt.doTrials')
			viz.quit()
			raise