
import viz
import vizact
import random

import hardware
import trialData
import experiment
import params

def main():
	hardware.setupGfx()
	random.seed()
	expt = experiment.Executive()
	try:
		expt.startSession()
	except:
		viz.logError('** Caught exception in main')
		viz.quit()
		raise
		
if __name__ == '__main__':
	main()

