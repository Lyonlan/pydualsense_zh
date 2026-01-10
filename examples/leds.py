import time

from pydualsense.enums import PlayerID
from pydualsense.pydualsense import pydualsense

# 获取 dualsense 实例
dualsense = pydualsense()
dualsense.init()
# 将触控板周围颜色设置为红色
dualsense.light.setColorI(255, 0, 0)
# 静音麦克风
dualsense.audio.setMicrophoneState(True)
# 设置玩家 1 指示灯开启
dualsense.light.setPlayerID(PlayerID.PLAYER_1)
# 稍作等待以查看控制器上的结果
# 这在正常使用中不是必需的
time.sleep(2)
# 终止消息线程并关闭设备
dualsense.close()
