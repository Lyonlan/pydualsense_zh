from pydualsense.pydualsense import pydualsense


def cross_down(state: bool) -> None:
    print(f'cross {state}')


def circle_down(state: bool) -> None:
    print(f'circle {state}')


def dpad_down(state: bool) -> None:
    print(f'dpad {state}')


def joystick(stateX: int, stateY: int) -> None:
    print(f'lj {stateX} {stateY}')


def gyro_changed(pitch: int, yaw: int, roll: int) -> None:
    print(f'{pitch}, {yaw}, {roll}')


# 创建 dualsense
dualsense = pydualsense()
# 查找设备并初始化
dualsense.init()

# 添加事件处理函数
dualsense.cross_pressed += cross_down
dualsense.circle_pressed += circle_down
dualsense.dpad_down += dpad_down
dualsense.left_joystick_changed += joystick
dualsense.gyro_changed += gyro_changed

# 读取控制器状态直到 R1 被按下
while not dualsense.state.R1:
    ...

# 关闭设备
dualsense.close()
