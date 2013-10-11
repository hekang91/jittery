# params.py
import viz

class Params:
	all_amp = [0.01] # for debug
	#all_amp = [0.01,0.018,0.026,0.034,0.042,0.050,0.058]
	
	# the scene we used
	all_scene = [0]
	
	# the direction we apply the jittery on
	all_dim = [0,1] # 0:x, 1:y, 2:z
	# face Z postive: 0: left and right, 1: up and down, 2: back and forth
		
	nTrialPerCond = 20 # default = 20
	nTrials = len(all_scene)*len(all_dim)*len(all_amp)*nTrialPerCond # for each jittery condition, do how many trials

	nSecPerTrial = 2 # sec, default = 2
	
	#sound
	startSound = viz.addAudio('notify.wav')
	endSound = viz.addAudio('chimes.wav')
	
	
	# offsets
	viewOffset                  = [0,0,0] #for HMD [0.05, -0.2, 0.085]
	trackerSpaceOffset          = [0,0,0]
	trackerSpaceRot             = [0,0,0] # for rural pit: startOri = [5,0,0]
	startZ						= 0
	eyeHeight					= 1.7
	
	# distance settings
	#treadmillPosZ = 0.6 # need to measure every time

	circleScale = [0.5, 0.5, 0.5]
	circlePos = [0, 2, 7]
	BlurRadius = 10
	
	# walking speed
	walkSpeedZ = 0.7
	
	# to be set later in the client code:
	subjectName = None
	displayMode = 0
	
# make global so only one instance will exist shared by all imports and we can change parameter values anywhere
global params
params = Params()


# if executing this, call main
if __name__ == "__main__":
    import main
    main.main()