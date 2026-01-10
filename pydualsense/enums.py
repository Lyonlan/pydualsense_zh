"""
DualSense 控制器相关枚举类型

包含连接类型、LED 选项、脉冲选项、亮度、玩家编号、扳机模式与电池状态等。
"""
from enum import IntFlag


class ConnectionType(IntFlag):
    """
    控制器连接类型
    """
    BT = 0x0
    USB = 0x1
    ERROR = 0xFF


class LedOptions(IntFlag):
    """
    LED 选项组合
    """
    Off = 0x0
    PlayerLedBrightness = 0x1
    UninterrumpableLed = 0x2
    Both = 0x01 | 0x02


class PulseOptions(IntFlag):
    """
    LED 脉冲效果选项
    """
    Off = 0x0
    FadeBlue = 0x1
    FadeOut = 0x2


class Brightness(IntFlag):
    """
    LED 亮度级别
    """
    high = 0x0
    medium = 0x1
    low = 0x2


class PlayerID(IntFlag):
    """
    玩家编号指示灯
    """
    PLAYER_1 = 4
    PLAYER_2 = 10
    PLAYER_3 = 21
    PLAYER_4 = 27
    ALL = 31


class TriggerModes(IntFlag):
    """
    扳机模式
    """
    Off = 0x0  # 无阻力
    Rigid = 0x1  # 持续阻力
    Pulse = 0x2  # 分段阻力
    Rigid_A = 0x1 | 0x20
    Rigid_B = 0x1 | 0x04
    Rigid_AB = 0x1 | 0x20 | 0x04
    Pulse_A = 0x2 | 0x20
    Pulse_B = 0x2 | 0x04
    Pulse_AB = 0x2 | 0x20 | 0x04
    Calibration = 0xFC


class BatteryState(IntFlag):
    """
    电池状态
    """
    POWER_SUPPLY_STATUS_DISCHARGING = 0x0
    POWER_SUPPLY_STATUS_CHARGING = 0x1
    POWER_SUPPLY_STATUS_FULL = 0x2
    POWER_SUPPLY_STATUS_NOT_CHARGING = 0xB
    POWER_SUPPLY_STATUS_ERROR = 0xF
    POWER_SUPPLY_TEMP_OR_VOLTAGE_OUT_OF_RANGE = 0xA
    POWER_SUPPLY_STATUS_UNKNOWN = 0x0
