# experiment.py
import viz
import vizact
import viztask
import itertools
import random

#import params
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
		self.dim	 		= None	
		self.scene			= None
		self.response		= []
		
	def generateTrials(self):
		a = tuple(itertools.repeat(params.all_amp, params.nTrialPerJitter)) # repeat conditionIDs nTrialPerJitter times
		b = map(None,*a)                                            	# combine over second dimension (think transpose in matlab)
		self.trialSequence = flattenList(b) 							# flatten into unidimensional array
	
		dim     = [0]*(params.nTrialPerJitter/2)
		dim[:0] = [1]*(params.nTrialPerJitter/2)
		dim     = [x[:] for x in itertools.repeat(dim, len(params.all_amp))] # repeat toggle for each condition, doing deep copy
		self.dim= flattenList(dim)
		
		#scene     = [0]*(params.nTrialPerJitter/4)
		#scene[:0] = [1]*(params.nTrialPerJitter/4)
		scene     = [0]*(params.nTrialPerJitter/2)
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
		
	def saveResponseData(self,subjectName):
		result = open(str(subjectName)+'_mode'+ str(params.displayMode) + '.txt', 'a') 
		#result.write('scene,dim,jitter,response\n\n')
		#result.write(str(self.scene) + '\n')
		#result.write(str(self.dim) + '\n')
		#result.write(str(self.trialSequence) + '\n')
		#result.write(str(self.response) + '\n')
		
		for each in self.scene:
			result.write(str(each) + ' ')
		result.write('\n')
		
		for each in self.dim:
			result.write(str(each) + ' ')
		result.write('\n')
		
		for each in self.trialSequence:
			result.write(str(each) + ' ')
		result.write('\n')
		
		for each in self.response:
			result.write(str(each) + ' ')
		result.write('\n')
		
		
	def doTrials(self):
		print '==========='
		print '--expt start--'
		viz.mouse.setVisible(viz.OFF)
		# any error during the experiments needs to be caught here (as this function is run through the scheduler)
		try:
			for whatJitter,whatScene,whatDim in zip(self.trialSequence,self.scene, self.dim):
				
				#print whatJitter,whatScene,whatDim # for debug
				trial = trialData.ActiveTrial(whatScene,whatDim,whatJitter,params.walkSpeedZ)
				
				yield trial.doTrial(self.response)
				trial.writeToFile(params.subjectName)

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