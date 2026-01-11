from pydualsense.enums import TriggerModes
from pydualsense.pydualsense import pydualsense

# 获取 dualsense 实例
dualsense = pydualsense()
dualsense.init()

print('Trigger Effect demo started')

dualsense.setLeftMotor(255)
dualsense.setRightMotor(100)
dualsense.triggerL.setMode(TriggerModes.Rigid)
dualsense.triggerL.setForce(1, 255)

dualsense.triggerR.setMode(TriggerModes.Pulse_A)
dualsense.triggerR.setForce(0, 200)
dualsense.triggerR.setForce(1, 255)
dualsense.triggerR.setForce(2, 175)

# 循环直到 R1 被按下以感受效果
while not dualsense.state.R1:
    ...
# 终止消息线程并关闭设备
dualsense.close()
