"""
LED 效果示例脚本

提供多种触控板灯光效果（固定色、彩虹循环、呼吸、玩家编号、脉冲、亮度），
并支持通过命令行参数切换效果与设置颜色/时长。

使用建议：
- 优先使用 USB‑C 有线连接（更稳定），蓝牙需先在系统中完成配对
- 运行示例前，确保已安装并导入 pydualsense 包（pip install -e .）
"""

import argparse
import math
import time

from pydualsense.enums import Brightness, LedOptions, PlayerID, PulseOptions
from pydualsense.pydualsense import pydualsense


def effect_solid(ds: pydualsense, r: int, g: int, b: int, duration: float) -> None:
    """
    固定颜色效果
    参数:
        ds: 控制器实例
        r, g, b: RGB 颜色分量（0..255）
        duration: 持续时长（秒）
    """
    ds.light.setColorI(r, g, b)
    time.sleep(duration)


def effect_rainbow(ds: pydualsense, duration: float) -> None:
    """
    彩虹循环效果（连续变换 RGB）
    参数:
        ds: 控制器实例
        duration: 持续时长（秒）
    """
    t0 = time.time()
    i = 0
    while time.time() - t0 < duration:
        s = i * 0.017
        r = int((1 + math.sin(s)) * 127)
        g = int((1 + math.sin(s + 2)) * 127)
        b = int((1 + math.sin(s + 4)) * 127)
        ds.light.setColorI(r, g, b)
        time.sleep(0.03)
        i += 1


def effect_breathe(ds: pydualsense, r: int, g: int, b: int, duration: float) -> None:
    """
    呼吸效果（指定颜色的明暗渐变）
    参数:
        ds: 控制器实例
        r, g, b: 基础颜色（0..255）
        duration: 持续时长（秒）
    """
    t0 = time.time()
    t = 0
    while time.time() - t0 < duration:
        k = (1 + math.sin(t * 0.05)) * 0.5
        ds.light.setColorI(int(r * k), int(g * k), int(b * k))
        time.sleep(0.02)
        t += 1


def effect_player_cycle(ds: pydualsense, duration: float) -> None:
    """
    玩家编号循环（依次点亮 1/2/3/4）
    参数:
        ds: 控制器实例
        duration: 持续时长（秒）
    """
    ids = [
        PlayerID.PLAYER_1,
        PlayerID.PLAYER_2,
        PlayerID.PLAYER_3,
        PlayerID.PLAYER_4,
    ]
    t0 = time.time()
    i = 0
    while time.time() - t0 < duration:
        ds.light.setPlayerID(ids[i % len(ids)])
        time.sleep(0.5)
        i += 1


def effect_pulse_cycle(ds: pydualsense, duration: float) -> None:
    """
    脉冲模式循环（Off / FadeBlue / FadeOut）
    参数:
        ds: 控制器实例
        duration: 持续时长（秒）
    说明:
        脉冲选项需结合 LEDOption 才会生效，此处默认同时控制两侧 LED。
    """
    ds.light.setLEDOption(LedOptions.Both)
    modes = [PulseOptions.Off, PulseOptions.FadeBlue, PulseOptions.FadeOut]
    t0 = time.time()
    i = 0
    while time.time() - t0 < duration:
        ds.light.setPulseOption(modes[i % len(modes)])
        time.sleep(1.0)
        i += 1


def effect_brightness_cycle(ds: pydualsense, duration: float) -> None:
    """
    亮度循环（低/中/高）
    参数:
        ds: 控制器实例
        duration: 持续时长（秒）
    """
    levels = [Brightness.low, Brightness.medium, Brightness.high]
    t0 = time.time()
    i = 0
    while time.time() - t0 < duration:
        ds.light.setBrightness(levels[i % len(levels)])
        time.sleep(0.8)
        i += 1


def main() -> None:
    """
    命令行入口
    参数:
        --effect: 选择灯光效果
        --r/--g/--b: 固定/呼吸效果的颜色分量
        --duration: 效果持续时长（秒）
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--effect", choices=["solid", "rainbow", "breathe", "player", "pulse", "brightness", "demo"], default="demo")
    parser.add_argument("--r", type=int, default=255)
    parser.add_argument("--g", type=int, default=80)
    parser.add_argument("--b", type=int, default=0)
    parser.add_argument("--duration", type=float, default=6.0)
    args = parser.parse_args()

    ds = pydualsense()
    ds.init()
    try:
        if args.effect == "solid":
            effect_solid(ds, args.r, args.g, args.b, args.duration)
        elif args.effect == "rainbow":
            effect_rainbow(ds, args.duration)
        elif args.effect == "breathe":
            effect_breathe(ds, args.r, args.g, args.b, args.duration)
        elif args.effect == "player":
            effect_player_cycle(ds, args.duration)
        elif args.effect == "pulse":
            effect_pulse_cycle(ds, args.duration)
        elif args.effect == "brightness":
            effect_brightness_cycle(ds, args.duration)
        else:
            effect_solid(ds, args.r, args.g, args.b, 2.0)
            effect_breathe(ds, args.r, args.g, args.b, 4.0)
            effect_rainbow(ds, 6.0)
            effect_player_cycle(ds, 4.0)
            effect_pulse_cycle(ds, 6.0)
            effect_brightness_cycle(ds, 4.0)
    finally:
        ds.close()


if __name__ == "__main__":
    main()
