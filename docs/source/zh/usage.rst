安装与使用
==========

安装
----

建议使用 pip 安装：

.. code-block:: console

   pip install --upgrade pydualsense

平台说明：

- Windows：需下载 HIDAPI 的 x64 .dll，并确保其位于系统 PATH 中
- Linux：需安装 libhidapi-dev（例如 Ubuntu 上）
- macOS：建议通过 Homebrew 安装 hidapi，并使用 pip 安装 Python 封装

快速上手
--------

.. code-block:: python

   from pydualsense.pydualsense import pydualsense
   from pydualsense.enums import TriggerModes, PlayerID

   ds = pydualsense()
   ds.init()
   ds.light.setColorI(255, 0, 0)          # 设置触控板灯为红色
   ds.triggerL.setMode(TriggerModes.Rigid)
   ds.triggerL.setForce(1, 255)
   ds.light.setPlayerID(PlayerID.PLAYER_1)
   ds.close()

注意事项
--------

- init() 建立连接，close() 释放资源
- 如果需要订阅输入事件（如按钮、摇杆变化），可使用 ds.cross_pressed += 回调 的方式
- BT 与 USB 的报文略有差异，库内部已处理
