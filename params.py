# params.py
import viz

class Params:
	# the scene we used
	all_scene = [0]
	
	# the direction we apply the jittery on
	all_dim = [0,1] # 0:x, 1:y, 2:z
	# face Z postive: 0: left or right, 1: up or down, 2: back or forth
	
	all_amp = [0.001,0.1] # for debug
	#all_amp = [0.004,0.008,0.012,0.016,0.020,0.024,0.028,0.032] # walk, 8 level, do not use
	#all_amp = [0.002,0.007,0.012,0.017,0.022,0.027,0.032]		 # walk, 7 level, use it in the exp
	
	nTrialPerCond = 2 # default = 10
	nTrialPerJitter = len(all_scene)*len(all_dim)*nTrialPerCond # for each jittery condition, do how many trials
	# x-room,y-room,x-sphere,y-sphere; 
	# thus we will totally have nTrialPerCond*length(all_amp) trials
	# we have 2*2*7 conditions so far: dim(2)*background(2)*jittery(7)
	
	nTrials = len(all_amp)*nTrialPerJitter
	nSecPerTrial = 3 # second, default = 3
	
	#sound
	startSound = viz.addAudio('notify.wav')
	endSound = viz.addAudio('chimes.wav')
	
	
	# offsets
	viewOffset                  = [0.05, -0.2, 0.085]
	trackerSpaceOffset          = [-0.19,0.11,-0.83] # for gallery
	#trackerSpaceOffset          = [-1.6,0.11,5.8] # for rural pit: startPos = [-1.5,1.63,6.5]
	trackerSpaceRot             = [0,0,0] # for rural pit: startOri = [5,0,0]
	startZ						= 0
	eyeHeight					= 1.7
	
	# distance settings
	treadmillPosZ = 0.6 # need to measure every time
	
	sphereScale = 0.3
	sphereHeight = 2 # the sphere does not lay on the floor; it floats at a constant position
	sphereDistance = 10 + treadmillPosZ # the distance between the observer and sphere
	
	ROOM_DISTANCE = 9.87 # from the center of the room to the end
	roomPosOffset = sphereDistance - ROOM_DISTANCE
	
	
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