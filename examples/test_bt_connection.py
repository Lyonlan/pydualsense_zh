"""
蓝牙连接交互式测试

支持交互命令：
- info                      显示连接类型与状态
- color R G B               设置颜色（0..255）
- pulse off|fadeblue|fadeout 设置脉冲效果
- bright low|medium|high    设置亮度
- player 1|2|3|4|all        设置玩家编号指示灯
- mic on|off                切换麦克风与其 LED
- listen                    订阅常用按键事件（再次输入 listen 取消）
- quit                      复位灯效并退出
"""

import sys
import threading
import time

from pydualsense.enums import Brightness, ConnectionType, PlayerID, PulseOptions
from pydualsense.pydualsense import pydualsense


# 打印交互式命令帮助
def print_help() -> None:
    print(
        "命令: info | color R G B | pulse off|fadeblue|fadeout | "
        "bright low|medium|high | player 1|2|3|4|all | "
        "micstate on|off | micled on|off | listen | quit"
    )


def main() -> None:
    # 解析命令行参数：-v/--verbose, --backend, --log[=DIR]
    verbose = ("-v" in sys.argv) or ("--verbose" in sys.argv)
    backend = None
    log_dir = None
    for arg in sys.argv:
        if arg.startswith("--backend="):
            backend = arg.split("=", 1)[1].strip().lower()
        if arg.startswith("--log"):
            parts = arg.split("=", 1)
            if len(parts) == 2:
                log_dir = parts[1].strip()
            else:
                log_dir = "examples/logs"
    # 创建并初始化手柄对象；如传入 --log 则开启 HID 报文日志
    ds = pydualsense(verbose=verbose, backend=backend)
    if log_dir:
        ds.enable_packet_logger(log_dir)
    ds.init()
    if not ds.connected:
        print("未成功连接到手柄，请在系统蓝牙里完成配对后重试。")
        return

    listening = True
    streaming = False

    def attach_listeners() -> None:
        # 订阅常用按键/摇杆事件并实时打印
        ds.cross_pressed += lambda v: print(f"cross={v}")
        ds.circle_pressed += lambda v: print(f"circle={v}")
        ds.square_pressed += lambda v: print(f"square={v}")
        ds.triangle_pressed += lambda v: print(f"triangle={v}")
        ds.left_joystick_changed += lambda x, y: print(f"lj={x},{y}")
        ds.right_joystick_changed += lambda x, y: print(f"rj={x},{y}")
        ds.dpad_up += lambda v: print(f"dpad_up={v}")
        ds.dpad_down += lambda v: print(f"dpad_down={v}")
        ds.dpad_left += lambda v: print(f"dpad_left={v}")
        ds.dpad_right += lambda v: print(f"dpad_right={v}")
        ds.l1_changed += lambda v: print(f"l1={v}")
        ds.r1_changed += lambda v: print(f"r1={v}")
        ds.l2_changed += lambda v: print(f"l2btn={v}")
        ds.r2_changed += lambda v: print(f"r2btn={v}")
        ds.l2_value_changed += lambda v: print(f"l2={v}")
        ds.r2_value_changed += lambda v: print(f"r2={v}")
        ds.microphone_pressed += lambda v: print(f"micBtn={v}")
        ds.ps_pressed += lambda v: print(f"ps={v}")
        ds.option_pressed += lambda v: print(f"options={v}")
        ds.share_pressed += lambda v: print(f"share={v}")
        ds.touch_pressed += lambda v: print(f"touchBtn={v}")

    def detach_listeners() -> None:
        # 事件系统为 += 添加，暂无 -= 接口；切换由用户再次输入 listen 控制打印频率
        pass

    # 默认开始实时打印按键事件
    if listening:
        attach_listeners()
        is_bt = ds.conType == ConnectionType.BT
        print(
            f"[auto] 已开始监听按键事件 / 连接类型: {'Bluetooth' if is_bt else 'USB'} "
            f"/ connected={ds.connected} "
            f"/ last_input_len={ds.last_input_len} "
            f"/ out_len={'78' if is_bt else '64'}"
        )

    def stream_states() -> None:
        # 以固定频率打印状态快照，辅助定位事件层是否工作
        while streaming:
            st = ds.state
            print(
                f"btn cross={st.cross} circle={st.circle} square={st.square} tri={st.triangle} "
                f"dpad U={st.DpadUp} D={st.DpadDown} L={st.DpadLeft} R={st.DpadRight} "
                f"L1={st.L1} R1={st.R1} L2btn={st.L2Btn} R2btn={st.R2Btn} "
                f"L2={st.L2_value} R2={st.R2_value} "
                f"axes LX={st.LX} LY={st.LY} RX={st.RX} RY={st.RY} "
                f"micBtn={st.micBtn} last_len={ds.last_input_len}"
            )
            time.sleep(0.25)

    stream_thread = None
    if streaming:
        stream_thread = threading.Thread(target=stream_states, daemon=True)
        stream_thread.start()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            line = "quit"
            print()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].lower()

        if cmd == "help":
            print_help()
            continue

        if cmd == "info":
            # 显示连接类型与最近输入报文长度（USB 64 / BT 78）
            is_bt = ds.conType == ConnectionType.BT
            print(
                f"连接类型: {'Bluetooth' if is_bt else 'USB'} "
                f"/ connected={ds.connected} "
                f"/ last_input_len={ds.last_input_len} "
                f"/ out_len={'78' if is_bt else '64'}"
            )

        elif cmd == "color" and len(parts) == 4:
            try:
                r, g, b = map(int, parts[1:4])
                ds.light.setColorI(r, g, b)
                print(f"颜色已设置为 ({r},{g},{b})")
            except Exception as e:
                print(f"设置颜色失败: {e}")

        elif cmd == "pulse" and len(parts) == 2:
            m = parts[1].lower()
            pulse_map = {
                "off": PulseOptions.Off,
                "fadeblue": PulseOptions.FadeBlue,
                "fadeout": PulseOptions.FadeOut,
            }
            if m in pulse_map:
                ds.light.setPulseOption(pulse_map[m])
                print(f"脉冲效果: {m}")
            else:
                print("无效脉冲模式；可选: off|fadeblue|fadeout")

        elif cmd == "bright" and len(parts) == 2:
            m = parts[1].lower()
            bright_map = {
                "low": Brightness.low,
                "medium": Brightness.medium,
                "high": Brightness.high,
            }
            if m in bright_map:
                ds.light.setBrightness(bright_map[m])
                print(f"亮度: {m}")
            else:
                print("无效亮度；可选: low|medium|high")

        elif cmd == "player" and len(parts) == 2:
            m = parts[1].lower()
            player_map = {
                "1": PlayerID.PLAYER_1,
                "2": PlayerID.PLAYER_2,
                "3": PlayerID.PLAYER_3,
                "4": PlayerID.PLAYER_4,
                "all": PlayerID.ALL,
            }
            if m in player_map:
                ds.light.setPlayerID(player_map[m])
                print(f"玩家编号: {m}")
            else:
                print("无效玩家编号；可选: 1|2|3|4|all")

        elif cmd == "micstate" and len(parts) == 2:
            v = parts[1].lower()
            if v in ("on", "off"):
                ds.audio.setMicrophoneState(v == "on")
                print(f"麦克风状态: {v}")
            else:
                print("用法: micstate on|off")

        elif cmd == "micled" and len(parts) == 2:
            v = parts[1].lower()
            if v in ("on", "off"):
                ds.audio.setMicrophoneLED(v == "on")
                print(f"麦克风 LED: {v}")
            else:
                print("用法: micled on|off")

        elif cmd == "listen":
            # 切换是否打印订阅回调（本质仍订阅，只是控制打印）
            listening = not listening
            if listening:
                attach_listeners()
                print("已订阅按键事件（再次输入 listen 取消订阅提示）")
            else:
                detach_listeners()
                print("事件订阅提示关闭")

        elif cmd == "quit":
            # 退出前关闭灯效并释放资源
            try:
                ds.light.setPulseOption(PulseOptions.Off)
                ds.light.setColorI(0, 0, 0)
            except Exception:
                pass
            streaming = False
            if stream_thread is not None:
                stream_thread.join(timeout=1.0)
            ds.close()
            print("已退出")
            break

        elif cmd == "force" and len(parts) == 2:
            # 强制设置连接类型（排障用途，正常自动判定）
            opt = parts[1].lower()
            if opt == "bt":
                ds.forceConnectionType(ConnectionType.BT)
                print("已强制设置为 Bluetooth")
            elif opt == "usb":
                ds.forceConnectionType(ConnectionType.USB)
                print("已强制设置为 USB")
            else:
                print("用法: force bt|usb")
        elif cmd == "stream" and len(parts) == 2:
            # 开关状态快照的后台打印线程
            v = parts[1].lower()
            if v in ("on", "off"):
                streaming = (v == "on")
                if streaming and (stream_thread is None or not stream_thread.is_alive()):
                    stream_thread = threading.Thread(target=stream_states, daemon=True)
                    stream_thread.start()
                print(f"stream={v}")
            else:
                print("用法: stream on|off")

        else:
            print("未知命令，输入 help 查看命令列表。")


if __name__ == "__main__":
    main()
