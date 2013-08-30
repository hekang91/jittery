# we want to run in high priority to minimize timing trouble
# high never hurts, realtime might mess things up on windows though....
# this info is based on timing testing of PsychToolbox by Mario Kleiner,
# his poster is distributed with PsychToolbox
import win32process
import win32con
win32process.SetPriorityClass(win32process.GetCurrentProcess(),win32con.HIGH_PRIORITY_CLASS)
# end high priority

import viz
import vizact
import random

from params import params
import hardware
import trialData
import experiment


def main():
	# get other needed input
	params.subjectName = str(viz.input('Enter subject name'))
	if params.subjectName == '': raise RuntimeError('Need subject name')

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

