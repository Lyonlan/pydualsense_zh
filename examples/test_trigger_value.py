"""
扳机模拟量读取示例

演示在连接 DualSense 后，连续读取 L2/R2 的模拟值（范围 0..255）。
建议使用 USB‑C 有线连接以提升稳定性；蓝牙需先在系统中完成配对。
"""
import time

from pydualsense.enums import ConnectionType
from pydualsense.pydualsense import pydualsense


def test_trigger_analog() -> None:
    """
    连接手柄并在 30 秒内打印 L2/R2 的模拟量。
    - L2_value / R2_value 为 0..255 的整型值，代表扳机的按压深度
    - 每 100ms 刷新一次输出
    """
    controller = pydualsense()
    controller.init()

    if controller.connected:
        # 根据报文长度自动判断连接类型（USB/BT），仅用于状态展示
        connection_type = "Bluetooth" if controller.conType == ConnectionType.BT else "USB"
        print(f"Controller connected via {connection_type}")

        # 记录起始时间并循环 30 秒
        start_time = time.time()
        print("Press L2 and R2 to see the analog values for 30 seconds, values range from 0 to 255")
        while time.time() - start_time < 30:
            # 打印当前帧的 L2/R2 模拟值，不换行覆盖输出
            print(f"L2: {controller.state.L2_value} R2: {controller.state.R2_value}", end="\r")
            time.sleep(0.1)
    else:
        # 未成功连接时给出提示
        print("Failed to connect to controller")

    # 释放线程与设备资源；若希望“退出后复位灯效/扳机”，可在此处追加复位设置
    controller.close()


if __name__ == "__main__":
    test_trigger_analog()
