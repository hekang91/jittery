
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

实验前向被试展示/demo下的三个demo：分别为不抖，左右抖，上下抖

测静止站立和行走时的头动（/baseline下的baseline.py），两个condition各三分钟
行走的步速为2.5 km/h ~ 0.7m/s

正式实验：
运行任何一个.py都可以调用main.py
实验中被试需要注视场景中央的注视点
每个场景持续3s，场景消失后，被试立刻进行判断：抖动/不抖
被试口述判断，由主试按键：leftArrow/rightArrow

中途随时可以休息
在主试按键之前，记下按哪个键，然后引导被试下跑步机
等休息完，被试上跑步机后，按刚才的键，继续实验

----------------------------------------------
【数据保存】
baseline: 
subjectName+baseline+status(s/w).txt
n*11矩阵
各列表示：time,position(3),EulerOri(3),QuatOri(4)
可以直接用matlab读取

main: 
subjectName.txt
4*280矩阵
每行分别代表scene,dim,jitter,response
处理时需要先转换成mat文件，matlab的load无法读取

----------------------
【todo】

两种实验条件选哪个？大屏幕-world reference；头盔-head reference

code:
随时休息
数据目前存在jittery目录，最好存在/data/下
数据最好存成mat格式
