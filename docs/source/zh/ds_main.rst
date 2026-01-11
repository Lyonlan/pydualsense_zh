主接口与用法（pydualsense）
==========================

pydualsense 提供与 DualSense 手柄交互的主类与数据结构，支持连接初始化、读取输入事件、设置灯光/音频/扳机效果等。

示例
----

.. code-block:: python

   from pydualsense.pydualsense import pydualsense
   from pydualsense.enums import TriggerModes, PlayerID

   ds = pydualsense()
   ds.init()
   ds.light.setColorI(0, 128, 255)
   ds.triggerL.setMode(TriggerModes.Rigid)
   ds.light.setPlayerID(PlayerID.PLAYER_1)
   ds.close()

API 参考
--------
.. automodule:: pydualsense.pydualsense
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:
