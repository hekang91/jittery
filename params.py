# params.py

class Params:
	
	# the direction we apply the jittery on
	all_dim = [0,1] # 0:x, 1:y, 2:z
	# face Z postive: 0: left or right, 1: up or down, 2: back or forth
	
	#all_amp = [0.01,0.03] # for debug
	#all_amp = [0.004,0.008,0.012,0.016,0.020,0.024,0.028,0.032] # walk, 8 level, do not use
	all_amp = [0.002,0.007,0.012,0.017,0.022,0.027,0.032]		 # walk, 7 level, use it in the exp
	
	nTrialPerCond = 4*10 # for each jittery condition, do how many trials
	# x-room,y-room,x-sphere,y-sphere; default = 40
	# thus we will totally have nTrialPerCond*length(all_amp) trials
	# we have 2*2*7 conditions so far: dim(2)*background(2)*jittery(7)
	# each condition will have nTrialPerCond/4 trials
	
	nTrials = len(all_amp)*nTrialPerCond
	nSecPerTrial = 3 # second, default = 3
	
	
	# distance settings
	treadmillPosZ = 0.6 # need to measure every time
	
	sphereScale = 0.3
	sphereHeight = 2 # the sphere does not lay on the floor; it floats at a constant position
	sphereDistance = 10 + treadmillPosZ # the distance between the observer and sphere
	
	ROOM_DISTANCE = 9.87 # from the center of the room to the end
	roomPosOffset = sphereDistance - ROOM_DISTANCE
	
	
	# walking speed
	walkSpeedZ = 0.7