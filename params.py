# params.py

class Params:
	
	all_dim = [0,1] #0:x, 1:y, 2:z
	#face Z postive: 0: left or right, 1: up or down, 2: back or forth
	
	all_amp = [0.01,0.03] # for debug
	#all_amp = [0.004,0.008,0.012,0.016,0.020,0.024,0.028,0.032] #walk, 8 level
	#all_amp = [0.002,0.007,0.012,0.017,0.022,0.027,0.032]		 #walk, 7 level
	
	nTrialPerCond = 40 # for each jittery condition, do how many trials
	# x-room,y-room,x-sphere,y-sphere; default = 40
	
	nSecPerTrial = 3 # second, default = 3
	
	# sphere settings
	sphereHeight = 2
	distance = 9