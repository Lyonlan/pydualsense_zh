"""
pydualsense 包的入口模块

此模块用于导出常用的类与枚举，方便用户从 pydualsense 直接导入并使用。
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

from .enums import Brightness, LedOptions, PlayerID, PulseOptions, TriggerModes  # noqa : F401
from .event_system import Event  # noqa : F401
from .pydualsense import DSAudio, DSLight, DSState, DSTouchpad, DSTrigger, pydualsense  # noqa : F401

__version__ = "0.7.5"
