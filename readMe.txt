
恒定刺激法测量行走时知觉到水平/竖直方向抖动的阈限
-------------------------------------------------
【实验设计】

2*2*7设计
两个场景：sphere（empty背景里一个蓝球）和room
被试到球/房间最远端距离为10m
两个抖动方向：水平和竖直
7个抖动大小：0.002:0.005:0.032

每个刺激条件共10个trial
共2*2*7*10 = 280个trial
每个trial约10s，共50min

-----------------------
【实验步骤】

测静止站立和行走时的头动（/baseline下的baseline.py）
分三种情况：[1] RB drive HMD [2] RB drive Screen [3] RB with Screen
时间1分钟

跑步机的步速为2.5 km/h ~ 0.7m/s（1m/s感觉仍慢）

向被试展示/demo下的三个demo：分别为不抖，左右抖，上下抖

正式实验：
运行任何一个.py都可以调用main.py
（实验时把鼠标移开）
实验中被试需要注视场景中央的注视点
每个场景持续3s，场景消失后，被试立刻进行判断：抖动/不抖
被试口述判断，由主试按键：leftArrow/rightArrow

中途随时可以休息
在主试按键之前，记下按哪个键，然后引导被试下跑步机
等休息完，被试上跑步机后，按刚才的键，继续实验

----------------------------------------------
【数据保存】
baseline: 
subjectName+baseline+mode(1/2/3)+status(s/w).txt
n*13矩阵
各列表示：time,tracker_position(3),VR_position(3),tracker_EulerOri(3),VR_EulerOri(3)
可以直接用matlab读取

main: 
subjectName.txt
4*280矩阵
每行分别代表scene,dim,jitter,response
处理时需要先转换成mat文件，matlab的load无法读取

----------------------
【OptiTrack】
kalman filter: Translation 0.1, Rotation 0.5
viewOffset                  = [0.05, -0.2, 0.085] # RB到视中心的offset
trackerSpaceOffset          = [-0.36,0.11,-0.42]  # 跑步机中心定为[0,0,0],与OptiTrack坐标系的offset;经验值，勿改；跑步机位置改变或重新标定后重测

--------------------------------------------
【todo】

两种实验条件选哪个？大屏幕-world reference；头盔-head reference

code:
随时休息
数据目前存在jittery目录，最好存在/data/下
数据最好存成mat格式
