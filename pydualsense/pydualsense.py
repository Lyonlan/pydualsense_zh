"""
DualSense 控制器主接口

提供连接、读取输入、设置灯光/音频/扳机效果等完整功能。
"""
import logging
import os
import sys
from sys import platform

if platform.startswith("win32") and sys.version_info >= (3, 8):
    os.environ["PATH"] += os.pathsep + os.path.dirname(__file__)


import threading
import time
from copy import deepcopy
from typing import Any, List, Optional, Tuple

# 后端在运行时动态选择与加载
from .checksum import compute
from .enums import (
    BatteryState,
    Brightness,
    ConnectionType,
    LedOptions,
    PlayerID,
    PulseOptions,
    TriggerModes,
)
from .event_system import Event

logger = logging.getLogger()
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)


class pydualsense:  # noqa: N801
    OUTPUT_REPORT_USB = 0x02
    OUTPUT_REPORT_BT = 0x31

    def __init__(self, verbose: bool = False, backend: Optional[str] = None) -> None:
        """
        初始化库但不连接到控制器。调用 :func:`init() <pydualsense.pydualsense.init>` 来连接到控制器

        参数:
            verbose (bool, optional): 显示详细输出 (输入和输出的调试打印)。默认为 False。
            backend (str | None): 选择 HID 后端，仅支持 "hidapi"。默认使用 hidapi。
        """

        self.verbose = verbose

        if self.verbose:
            logger.setLevel(logging.DEBUG)

        self.leftMotor = 0
        self.rightMotor = 0
        self.last_input_len = 0
        self.backend_name = ""
        self._hid: Any = None

        self.last_states: DSState = None # type: ignore[assignment]

        self.register_available_events()
        self._init_backend(backend)
        self.packet_log_enabled = False
        self._packet_log_dir = ""
        self._packet_in_fp = None
        self._packet_out_fp = None

    def enable_packet_logger(self, log_dir: str) -> None:
        """
        启用 HID 报文记录功能

        参数:
            log_dir: 日志目录（不存在将自动创建），会生成 input_*.log 与 output_*.log
        说明:
            - 每行格式: 时间戳(秒) 报文长度 十六进制串
            - input_* 记录手柄输入报文；output_* 记录发送给手柄的报文
        """
        self.packet_log_enabled = True
        self._packet_log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        self._packet_in_fp = open(os.path.join(log_dir, f"input_{ts}.log"), "a")
        self._packet_out_fp = open(os.path.join(log_dir, f"output_{ts}.log"), "a")

    def disable_packet_logger(self) -> None:
        """
        关闭 HID 报文记录并安全关闭文件句柄
        """
        self.packet_log_enabled = False
        try:
            if self._packet_in_fp:
                self._packet_in_fp.close()
        except Exception:
            pass
        try:
            if self._packet_out_fp:
                self._packet_out_fp.close()
        except Exception:
            pass
        self._packet_in_fp = None
        self._packet_out_fp = None

    def _log_input_packet(self, data: bytes) -> None:
        """
        写入一条输入报文到 input_*.log（时间戳/长度/十六进制）
        """
        if not self.packet_log_enabled or self._packet_in_fp is None:
            return
        try:
            self._packet_in_fp.write(f"{time.time():.6f} {len(data)} {data.hex()}\n")
            self._packet_in_fp.flush()
        except Exception:
            pass

    def _log_output_packet(self, data: bytes) -> None:
        """
        写入一条输出报文到 output_*.log（时间戳/长度/十六进制）
        """
        if not self.packet_log_enabled or self._packet_out_fp is None:
            return
        try:
            self._packet_out_fp.write(f"{time.time():.6f} {len(data)} {data.hex()}\n")
            self._packet_out_fp.flush()
        except Exception:
            pass

    def _init_backend(self, backend: Optional[str]) -> None:
        """
        初始化 HID 后端。优先按参数，其次按环境变量，最后按平台选择。
        """
        prefer = []
        env_backend = os.getenv("PYDUALSENSE_BACKEND")
        chosen = backend or (env_backend if env_backend in ("hidapi",) else None)
        prefer = [chosen] if chosen is not None else ["hidapi"]

        last_err = None
        for name in prefer:
            try:
                if name == "hidapi":
                    import hidapi as hidapi_mod  # type: ignore[import]
                    self._hid = hidapi_mod
                    self.backend_name = "hidapi"
                    return
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"Failed to load HID backend ({prefer}). Last error: {last_err}")

    def register_available_events(self) -> None:
        """
        注册控制器可用的所有事件
        """

        # button events
        self.triangle_pressed = Event()
        self.circle_pressed = Event()
        self.cross_pressed = Event()
        self.square_pressed = Event()

        # dpad events
        # TODO: add a event that sends the pressed key if any key is pressed
        # self.dpad_changed = Event()
        self.dpad_up = Event()
        self.dpad_down = Event()
        self.dpad_left = Event()
        self.dpad_right = Event()

        # joystick
        self.left_joystick_changed = Event()
        self.right_joystick_changed = Event()

        # trigger back buttons
        self.r1_changed = Event()
        self.r2_changed = Event()
        self.r3_changed = Event()

        self.l1_changed = Event()
        self.l2_changed = Event()
        self.l3_changed = Event()

        # Dualsense Edge specific buttons
        # Default to a disabled event
        self.r4_changed = Event(False)
        self.r5_changed = Event(False)
        self.l4_changed = Event(False)
        self.l5_changed = Event(False)


        # misc
        self.ps_pressed = Event()
        self.touch_pressed = Event()
        self.microphone_pressed = Event()
        self.share_pressed = Event()
        self.option_pressed = Event()

        # trackpad touch
        # handles 1 or 2 fingers
        # self.trackpad_frame_reported = Event()

        # gyrometer events
        self.gyro_changed = Event()

        self.accelerometer_changed = Event()

        # trigger analog
        self.l2_value_changed = Event()
        self.r2_value_changed = Event()

    def init(self) -> None:
        """
        初始化模块和设备状态。在结束时启动 sendReport 后台线程
        """
        self.device, self.is_edge = self.__find_device()
        self.light = DSLight()  # control led light of ds
        self.audio = DSAudio()  # ds audio setting
        self.triggerL = DSTrigger()  # left trigger
        self.triggerR = DSTrigger()  # right trigger
        self.state = DSState()  # controller states
        # Initialize extra buttons
        if self.is_edge:
            self.state.L4, self.state.L5, self.state.R4, self.state.R5 = False, False, False, False
            (self.l4_changed.available, self.l5_changed.available,
             self.r4_changed.available, self.r5_changed.available) = True, True, True, True
        self.battery = DSBattery()
        self.conType = self.determineConnectionType()  # determine USB or BT connection
        if self.conType is ConnectionType.ERROR:
            raise Exception("Couldn't determine connection type")
        self.ds_thread = True
        self.connected = True
        self.report_thread = threading.Thread(target=self.sendReport)
        self.report_thread.start()
        self.states = None

    def determineConnectionType(self) -> ConnectionType:
        """
        确定控制器的连接类型。例如 USB 或 BT。

        我们向控制器请求一个长度最多 100 字节的输入报告，
        然后检查接收到的输入报告的长度。
        连接类型决定了报告的长度。

        这种确定方式不是很优雅，但它有效。。

        返回:
            ConnectionType: 检测到的控制器连接类型。
        """

        input_report_length = 0
        for _ in range(10):
            dummy_report = self.device.read(100, timeout_ms=50)
            input_report_length = len(dummy_report) if dummy_report is not None else 0
            if input_report_length != 0:
                break
            time.sleep(0.05)

        if input_report_length == 64:
            self.input_report_length = 64
            self.output_report_length = 64
            return ConnectionType.USB
        elif input_report_length == 78:
            self.input_report_length = 78
            self.output_report_length = 78
            return ConnectionType.BT

        self.input_report_length = 64
        self.output_report_length = 64
        return ConnectionType.USB

    def close(self) -> None:
        """
        停止报告线程并关闭 HID 设备
        """
        # TODO: reset trigger effect to default

        self.ds_thread = False
        self.report_thread.join()
        self.device.close()

    def __find_device(self) -> Tuple[Any, bool]:
        """
        查找 HID dualsense 设备并打开它

        引发:
            Exception: 检测到 HIDGuardian
            Exception: 未检测到设备

        返回:
            hid.Device: 返回打开的控制器设备
            bool: 如果设备是 DualSense Edge，则返回 true。
        """
        # TODO: detect connection mode, bluetooth has a bigger write buffer
        # TODO: implement multiple controllers working
        if sys.platform.startswith("win32"):
            import pydualsense.hidguardian as hidguardian

            if hidguardian.check_hide():
                raise Exception(
                    "HIDGuardian detected. Delete the controller from HIDGuardian and restart PC to connect to controller"
                )
        detected_info: Any = None
        try:
            devices = self._hid.enumerate()
        except TypeError:
            try:
                devices = self._hid.enumerate(0x054C, 0)
            except Exception:
                devices = []
        # 收集候选设备（优先 GamePad 接口）
        candidates: List[Any] = []
        gamepad_candidates: List[Any] = []
        for d in devices:
            vendor = getattr(d, "vendor_id", None)
            product = getattr(d, "product_id", None)
            if vendor is None or product is None:
                if isinstance(d, dict):
                    vendor = d.get("vendor_id")
                    product = d.get("product_id")
            if vendor == 0x054C and product in (0x0CE6, 0x0DF2):
                candidates.append(d)
                usage_page = getattr(d, "usage_page", None)
                usage = getattr(d, "usage", None)
                if usage_page == 0x01 and usage == 0x05:
                    gamepad_candidates.append(d)
        ordered = gamepad_candidates + [c for c in candidates if c not in gamepad_candidates]

        if not ordered:
            raise Exception("No device detected")

        # 迭代尝试打开，回退顺序：info -> vid/pid -> path
        last_err: Optional[Exception] = None
        device = None
        for info in ordered:
            vendor = getattr(info, "vendor_id", None)
            product = getattr(info, "product_id", None)
            if vendor is None or product is None:
                vendor = info.get("vendor_id")
                product = info.get("product_id")
            path = getattr(info, "path", None)
            if path is None and isinstance(info, dict):
                path = info.get("path")
            for _ in range(5):
                try:
                    device = self._hid.Device(info=info)
                    detected_info = info
                    # 验证是否为期望的输入接口
                    ok = False
                    for _ in range(5):
                        sample = device.read(100, timeout_ms=100)
                        slen = len(sample) if sample is not None else 0
                        if slen in (64, 78):
                            ok = True
                            break
                        time.sleep(0.05)
                    if ok:
                        break
                    else:
                        try:
                            device.close()
                        except Exception:
                            pass
                        device = None
                except Exception as e1:
                    last_err = e1
                try:
                    serial = getattr(info, "serial_number", None)
                    device = self._hid.Device(vendor_id=vendor, product_id=product, serial_number=serial)
                    detected_info = info
                    ok = False
                    for _ in range(5):
                        sample = device.read(100, timeout_ms=100)
                        slen = len(sample) if sample is not None else 0
                        if slen in (64, 78):
                            ok = True
                            break
                        time.sleep(0.05)
                    if ok:
                        break
                    else:
                        try:
                            device.close()
                        except Exception:
                            pass
                        device = None
                except Exception as e2:
                    last_err = e2
                try:
                    if path:
                        path_bytes = path if isinstance(path, (bytes, bytearray)) else str(path).encode()
                        device = self._hid.Device(path=path_bytes)
                        detected_info = info
                        ok = False
                        for _ in range(5):
                            sample = device.read(100, timeout_ms=100)
                            slen = len(sample) if sample is not None else 0
                            if slen in (64, 78):
                                ok = True
                                break
                            time.sleep(0.05)
                        if ok:
                            break
                        else:
                            try:
                                device.close()
                            except Exception:
                                pass
                            device = None
                except Exception as e3:
                    last_err = e3
                time.sleep(0.2)
            if device is not None:
                break

        if device is None:
            if last_err is None:
                last_err = RuntimeError("No valid HID input interface (no 64/78 byte reports)")
            raise Exception(f"Failed to open DualSense HID device: {last_err}")

        is_edge = bool(product == 0x0DF2)
        return device, is_edge

    def setLeftMotor(self, intensity: int) -> None:
        """
        设置左侧电机振动

        参数:
            intensity (int): 振动强度

        引发:
            TypeError: intensity 类型错误
            Exception: intensity 超出范围 0..255
        """
        if not isinstance(intensity, int):
            raise TypeError("left motor intensity needs to be an int")

        if intensity > 255 or intensity < 0:
            raise Exception("maximum intensity is 255")
        self.leftMotor = intensity

    def setRightMotor(self, intensity: int) -> None:
        """
        设置右侧电机振动

        参数:
            intensity (int): 振动强度

        引发:
            TypeError: intensity 类型错误
            Exception: intensity 超出范围 0..255
        """
        if not isinstance(intensity, int):
            raise TypeError("right motor intensity needs to be an int")

        if intensity > 255 or intensity < 0:
            raise Exception("maximum intensity is 255")
        self.rightMotor = intensity

    def sendReport(self) -> None:
        """后台线程处理设备的读取并更新其状态"""
        while self.ds_thread:
            try:
                # read data from the input report of the controller
                inReport = self.device.read(self.input_report_length, timeout_ms=50)
                if inReport is None:
                    self.last_input_len = 0
                    outReport = self.prepareReport()
                    self._log_output_packet(bytes(outReport))
                    self.writeReport(outReport)
                    continue
                self.last_input_len = len(inReport)
                if self.verbose:
                    logger.debug(inReport)
                self._log_input_packet(bytes(inReport))
                # decrypt the packet and bind the inputs
                self.readInput(inReport)

                # prepare new report for device
                outReport = self.prepareReport()

                # write the report to the device
                self._log_output_packet(bytes(outReport))
                self.writeReport(outReport)
            except OSError:
                self.connected = False
                break
                
            except AttributeError:
                self.connected = False
                break

    def readInput(self, inReport : List[int]) -> None:
        """
        从控制器读取输入并分配状态

        参数:
            inReport (bytearray): 读取包含整个控制器状态的字节数组
        """

        if not inReport:
            return
        # 根据实际输入报文长度动态修正连接类型
        if len(inReport) == 64 and self.conType != ConnectionType.USB:
            self.conType = ConnectionType.USB
            self.input_report_length = 64
            self.output_report_length = 64
        elif len(inReport) == 78 and self.conType != ConnectionType.BT:
            self.conType = ConnectionType.BT
            self.input_report_length = 78
            self.output_report_length = 78

        if self.conType == ConnectionType.USB and len(inReport) < 64:
            return
        if self.conType == ConnectionType.BT and len(inReport) < 78:
            return

        # the reports for BT and USB are structured the same,
        # but there is one more byte at the start of the bluetooth report.
        # We drop that byte, so that the format matches up again.
        states: List[int] = list(inReport)[1:] if self.conType == ConnectionType.BT else list(inReport)

        self.states: List[int] = states # type: ignore[assigment]
        # states 0 is always 1
        self.state.LX = states[1] - 128
        self.state.LY = states[2] - 128
        self.state.RX = states[3] - 128
        self.state.RY = states[4] - 128
        self.state.L2 = bool(states[5])
        self.state.R2 = bool(states[6])

        # trigger analog
        self.state.L2_value = states[5]
        self.state.R2_value = states[6]

        # state 7 always increments -> not used anywhere

        buttonState = states[8]
        self.state.triangle = (buttonState & (1 << 7)) != 0
        self.state.circle = (buttonState & (1 << 6)) != 0
        self.state.cross = (buttonState & (1 << 5)) != 0
        self.state.square = (buttonState & (1 << 4)) != 0

        # dpad
        dpad_state = buttonState & 0x0F
        self.state.setDPadState(dpad_state)

        misc = states[9]
        self.state.R3 = (misc & (1 << 7)) != 0
        self.state.L3 = (misc & (1 << 6)) != 0
        self.state.options = (misc & (1 << 5)) != 0
        self.state.share = (misc & (1 << 4)) != 0
        self.state.R2Btn = (misc & (1 << 3)) != 0
        self.state.L2Btn = (misc & (1 << 2)) != 0
        self.state.R1 = (misc & (1 << 1)) != 0
        self.state.L1 = (misc & (1 << 0)) != 0

        misc2 = states[10]
        self.state.ps = (misc2 & (1 << 0)) != 0
        self.state.touchBtn = (misc2 & 0x02) != 0
        self.state.micBtn = (misc2 & 0x04) != 0
        if self.is_edge:
            self.state.L4 = (misc2 & 0x10) != 0
            self.state.R4 = (misc2 & 0x20) != 0
            self.state.L5 = (misc2 & 0x40) != 0
            self.state.R5 = (misc2 & 0x80) != 0

        # trackpad touch
        self.state.trackPadTouch0.ID = inReport[33] & 0x7F
        self.state.trackPadTouch0.isActive = (inReport[33] & 0x80) == 0
        self.state.trackPadTouch0.X = ((inReport[35] & 0x0F) << 8) | (inReport[34])
        self.state.trackPadTouch0.Y = ((inReport[36]) << 4) | (
            (inReport[35] & 0xF0) >> 4
        )

        # trackpad touch
        self.state.trackPadTouch1.ID = inReport[37] & 0x7F
        self.state.trackPadTouch1.isActive = (inReport[37] & 0x80) == 0
        self.state.trackPadTouch1.X = ((inReport[39] & 0x0F) << 8) | (inReport[38])
        self.state.trackPadTouch1.Y = ((inReport[40]) << 4) | (
            (inReport[39] & 0xF0) >> 4
        )

        # accelerometer
        self.state.accelerometer.X = int.from_bytes(
            ([inReport[16], inReport[17]]), byteorder="little", signed=True
        )
        self.state.accelerometer.Y = int.from_bytes(
            ([inReport[18], inReport[19]]), byteorder="little", signed=True
        )
        self.state.accelerometer.Z = int.from_bytes(
            ([inReport[20], inReport[21]]), byteorder="little", signed=True
        )

        # gyrometer
        self.state.gyro.Pitch = int.from_bytes(
            ([inReport[22], inReport[23]]), byteorder="little", signed=True
        )
        self.state.gyro.Yaw = int.from_bytes(
            ([inReport[24], inReport[25]]), byteorder="little", signed=True
        )
        self.state.gyro.Roll = int.from_bytes(
            ([inReport[26], inReport[27]]), byteorder="little", signed=True
        )

        # from kit-nya
        battery = states[53]
        self.battery.State = BatteryState((battery & 0xF0) >> 4)
        self.battery.Level = min((battery & 0x0F) * 10 + 5, 100)

        # first call we dont have a "last state" so we create if with the first occurence
        if self.last_states is None:
            self.last_states: DSState = deepcopy(self.state) # type: ignore[assignment]
            return

        # send all events if neede
        if self.state.circle != self.last_states.circle:
            self.circle_pressed(self.state.circle)

        if self.state.cross != self.last_states.cross:
            self.cross_pressed(self.state.cross)

        if self.state.triangle != self.last_states.triangle:
            self.triangle_pressed(self.state.triangle)

        if self.state.square != self.last_states.square:
            self.square_pressed(self.state.square)

        if self.state.DpadDown != self.last_states.DpadDown:
            self.dpad_down(self.state.DpadDown)

        if self.state.DpadLeft != self.last_states.DpadLeft:
            self.dpad_left(self.state.DpadLeft)

        if self.state.DpadRight != self.last_states.DpadRight:
            self.dpad_right(self.state.DpadRight)

        if self.state.DpadUp != self.last_states.DpadUp:
            self.dpad_up(self.state.DpadUp)

        if self.state.LX != self.last_states.LX or self.state.LY != self.last_states.LY:
            self.left_joystick_changed(self.state.LX, self.state.LY)

        if self.state.RX != self.last_states.RX or self.state.RY != self.last_states.RY:
            self.right_joystick_changed(self.state.RX, self.state.RY)

        if self.state.R1 != self.last_states.R1:
            self.r1_changed(self.state.R1)

        if self.state.R2 != self.last_states.R2:
            self.r2_changed(self.state.R2)

        if self.state.L1 != self.last_states.L1:
            self.l1_changed(self.state.L1)

        if self.state.L2 != self.last_states.L2:
            self.l2_changed(self.state.L2)

        if self.state.R3 != self.last_states.R3:
            self.r3_changed(self.state.R3)

        if self.state.L3 != self.last_states.L3:
            self.l3_changed(self.state.L3)

        if self.is_edge:
            if self.state.R4 != self.last_states.R4:
                self.r4_changed(self.state.R4)

            if self.state.R5 != self.last_states.R5:
                self.r5_changed(self.state.R5)

            if self.state.L4 != self.last_states.L4:
                self.l4_changed(self.state.L4)

            if self.state.L5 != self.last_states.L5:
                self.l5_changed(self.state.L5)

        if self.state.ps != self.last_states.ps:
            self.ps_pressed(self.state.ps)

        if self.state.touchBtn != self.last_states.touchBtn:
            self.touch_pressed(self.state.touchBtn)

        if self.state.micBtn != self.last_states.micBtn:
            self.microphone_pressed(self.state.micBtn)

        if self.state.share != self.last_states.share:
            self.share_pressed(self.state.share)

        if self.state.options != self.last_states.options:
            self.option_pressed(self.state.options)

        if (
            self.state.accelerometer.X != self.last_states.accelerometer.X
            or self.state.accelerometer.Y != self.last_states.accelerometer.Y
            or self.state.accelerometer.Z != self.last_states.accelerometer.Z
        ):
            self.accelerometer_changed(
                self.state.accelerometer.X,
                self.state.accelerometer.Y,
                self.state.accelerometer.Z,
            )

        if (
            self.state.gyro.Pitch != self.last_states.gyro.Pitch
            or self.state.gyro.Yaw != self.last_states.gyro.Yaw
            or self.state.gyro.Roll != self.last_states.gyro.Roll
        ):
            self.gyro_changed(
                self.state.gyro.Pitch, self.state.gyro.Yaw, self.state.gyro.Roll
            )

        if self.state.L2_value != self.last_states.L2_value:
            self.l2_value_changed(self.state.L2_value)

        if self.state.R2_value != self.last_states.R2_value:
            self.r2_value_changed(self.state.R2_value)

        """
        copy current state into temp object to check next cycle if a change occuret
        and event trigger is needed
        """
        self.last_states = deepcopy(
            self.state
        )  # copy current state into object to check next time

        # TODO: control mouse with touchpad for fun as DS4Windows

    def writeReport(self, outReport : List[int]) -> None:
        """
        将报告写入设备

        参数:
            outReport (list): 要写入设备的报告
        """
        self.device.write(bytes(outReport))

    def forceConnectionType(self, con: ConnectionType) -> None:
        """
        强制设置连接类型（USB/BT），并调整报文长度
        """
        if con == ConnectionType.BT:
            self.conType = ConnectionType.BT
            self.input_report_length = 78
            self.output_report_length = 78
        elif con == ConnectionType.USB:
            self.conType = ConnectionType.USB
            self.input_report_length = 64
            self.output_report_length = 64
        else:
            self.conType = ConnectionType.ERROR
    def prepareReport(self) -> List[int]:
        """
        准备要发送到控制器的输出

        返回:
            list: 要发送到控制器的报告
        """
        outReport = (
            [0] * self.output_report_length
        )  # create empty list with range of output report
 
        if self.conType == ConnectionType.USB:
            # 数据包类型
            outReport[0] = self.OUTPUT_REPORT_USB

            # 标志确定此数据包将执行哪些更改
            # 0x01 设置主电机（还需要标志 0x02）；单独设置此标志将允许振动优雅地终止然后重新启用音频触觉，而不设置它将立即停止振动并重新启用音频触觉。
            # 0x02 设置主电机（还需要标志 0x01；没有位 0x01 电机允许超时而不重新启用音频触觉）
            # 0x04 设置右侧扳机电机
            # 0x08 设置左侧扳机电机
            # 0x10 修改音频音量
            # 0x20 在耳机连接时切换内部扬声器
            # 0x40 修改麦克风音量
            outReport[1] = 0xFF  # [1]

            # 进一步标志确定此数据包将执行哪些更改
            # 0x01 切换麦克风 LED
            # 0x02 切换音频/麦克风静音
            # 0x04 切换触摸板侧面的 LED 条
            # 0x08 将主动关闭所有 LED？便利标志？（如果是，第三方可能不支持它）
            # 0x10 切换触摸板下方的白色玩家指示灯 LED
            # 0x20 ???
            # 0x40 调整整体电机/效果功率（索引 37 - 阅读扳机上的注释）
            # 0x80 ???
            outReport[2] = 0x1 | 0x2 | 0x4 | 0x10 | 0x40  # [2]

            outReport[3] = self.rightMotor  # 右侧低频电机 0-255 # [3]
            outReport[4] = self.leftMotor  # 左侧低频电机 0-255 # [4]

            # outReport[5] - outReport[8] 音频相关

            # 设置麦克风 LED，设置不影响麦克风设置
            outReport[9] = self.audio.microphone_led  # [9]

            outReport[10] = 0x10 if self.audio.microphone_mute is True else 0x00

            # 将右侧扳机模式 + 参数添加到数据包
            outReport[11] = self.triggerR.mode.value
            outReport[12] = self.triggerR.forces[0]
            outReport[13] = self.triggerR.forces[1]
            outReport[14] = self.triggerR.forces[2]
            outReport[15] = self.triggerR.forces[3]
            outReport[16] = self.triggerR.forces[4]
            outReport[17] = self.triggerR.forces[5]
            outReport[20] = self.triggerR.forces[6]

            outReport[22] = self.triggerL.mode.value
            outReport[23] = self.triggerL.forces[0]
            outReport[24] = self.triggerL.forces[1]
            outReport[25] = self.triggerL.forces[2]
            outReport[26] = self.triggerL.forces[3]
            outReport[27] = self.triggerL.forces[4]
            outReport[28] = self.triggerL.forces[5]
            outReport[31] = self.triggerL.forces[6]

            outReport[39] = self.light.ledOption.value
            outReport[42] = self.light.pulseOptions.value
            outReport[43] = self.light.brightness.value
            outReport[44] = self.light.playerNumber.value
            outReport[45] = self.light.TouchpadColor[0]
            outReport[46] = self.light.TouchpadColor[1]
            outReport[47] = self.light.TouchpadColor[2]

        elif self.conType == ConnectionType.BT:
            # 数据包类型
            outReport[0] = self.OUTPUT_REPORT_BT  # bt 类型

            outReport[1] = 0x02

            # 标志确定此数据包将执行哪些更改
            # 0x01 设置主电机（还需要标志 0x02）；单独设置此标志将允许振动优雅地终止然后重新启用音频触觉，而不设置它将立即停止振动并重新启用音频触觉。
            # 0x02 设置主电机（还需要标志 0x01；没有位 0x01 电机允许超时而不重新启用音频触觉）
            # 0x04 设置右侧扳机电机
            # 0x08 设置左侧扳机电机
            # 0x10 修改音频音量
            # 0x20 在耳机连接时切换内部扬声器
            # 0x40 修改麦克风音量
            outReport[2] = 0xFF  # [1]

            # 进一步标志确定此数据包将执行哪些更改
            # 0x01 切换麦克风 LED
            # 0x02 切换音频/麦克风静音
            # 0x04 切换触摸板侧面的 LED 条
            # 0x08 将主动关闭所有 LED？便利标志？（如果是，第三方可能不支持它）
            # 0x10 切换触摸板下方的白色玩家指示灯 LED
            # 0x20 ???
            # 0x40 调整整体电机/效果功率（索引 37 - 阅读扳机上的注释）
            # 0x80 ???
            outReport[3] = 0x1 | 0x2 | 0x4 | 0x10 | 0x40  # [2]

            outReport[4] = self.rightMotor  # 右侧低频电机 0-255 # [3]
            outReport[5] = self.leftMotor  # 左侧低频电机 0-255 # [4]

            # outReport[5] - outReport[8] 音频相关

            # 设置麦克风 LED，设置不影响麦克风设置
            outReport[10] = self.audio.microphone_led  # [9]

            outReport[11] = 0x10 if self.audio.microphone_mute is True else 0x00

            # 将右侧扳机模式 + 参数添加到数据包
            outReport[12] = self.triggerR.mode.value
            outReport[13] = self.triggerR.forces[0]
            outReport[14] = self.triggerR.forces[1]
            outReport[15] = self.triggerR.forces[2]
            outReport[16] = self.triggerR.forces[3]
            outReport[17] = self.triggerR.forces[4]
            outReport[18] = self.triggerR.forces[5]
            outReport[21] = self.triggerR.forces[6]

            outReport[23] = self.triggerL.mode.value
            outReport[24] = self.triggerL.forces[0]
            outReport[25] = self.triggerL.forces[1]
            outReport[26] = self.triggerL.forces[2]
            outReport[27] = self.triggerL.forces[3]
            outReport[28] = self.triggerL.forces[4]
            outReport[29] = self.triggerL.forces[5]
            outReport[32] = self.triggerL.forces[6]

            outReport[40] = self.light.ledOption.value
            outReport[43] = self.light.pulseOptions.value
            outReport[44] = self.light.brightness.value
            outReport[45] = self.light.playerNumber.value
            outReport[46] = self.light.TouchpadColor[0]
            outReport[47] = self.light.TouchpadColor[1]
            outReport[48] = self.light.TouchpadColor[2]

            crcChecksum = compute(outReport)

            outReport[74] = crcChecksum & 0x000000FF
            outReport[75] = (crcChecksum & 0x0000FF00) >> 8
            outReport[76] = (crcChecksum & 0x00FF0000) >> 16
            outReport[77] = (crcChecksum & 0xFF000000) >> 24

        if self.verbose:
            logger.debug(outReport)

        return outReport


class DSTouchpad:
    """
    Dualsense 触摸板类。包含触摸的 X 和 Y 位置以及触摸是否活跃
    """

    def __init__(self) -> None:
        """
        类代表控制器的触摸板
        """
        self.isActive = False
        self.ID = 0
        self.X = 0
        self.Y = 0


class DSState:
    def __init__(self) -> None:
        """
        可以读取的所有 dualsense 状态（输入）。第二种方法检查输入是否被按下。
        """
        self.square, self.triangle, self.circle, self.cross = False, False, False, False
        self.DpadUp, self.DpadDown, self.DpadLeft, self.DpadRight = (
            False,
            False,
            False,
            False,
        )
        self.L1, self.L2, self.L3, self.R1, self.R2, self.R3, self.R2Btn, self.L2Btn = (
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        )
        (
            self.share,
            self.options,
            self.ps,
            self.touch1,
            self.touch2,
            self.touchBtn,
            self.touchRight,
            self.touchLeft,
        ) = False, False, False, False, False, False, False, False
        # Set to None to allow regular controllers to have these values unset
        self.L4, self.L5, self.R4, self.R5 = None, None, None, None
        self.touchFinger1, self.touchFinger2 = False, False
        self.micBtn = False
        self.RX, self.RY, self.LX, self.LY = 128, 128, 128, 128
        self.trackPadTouch0, self.trackPadTouch1 = DSTouchpad(), DSTouchpad()
        self.gyro = DSGyro()
        self.accelerometer = DSAccelerometer()
        self.L2_value = 0 # 扳机模拟值从 0 到 255
        self.R2_value = 0 # 扳机模拟值从 0 到 255

    def setDPadState(self, dpad_state: int) -> None:
        """
        根据从控制器读取的整数设置 dpad 状态变量

        参数:
            dpad_state (int): 表示 dpad 状态的整数
        """
        if dpad_state == 0:
            self.DpadUp = True
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = False
        elif dpad_state == 1:
            self.DpadUp = True
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = True
        elif dpad_state == 2:
            self.DpadUp = False
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = True
        elif dpad_state == 3:
            self.DpadUp = False
            self.DpadDown = True
            self.DpadLeft = False
            self.DpadRight = True
        elif dpad_state == 4:
            self.DpadUp = False
            self.DpadDown = True
            self.DpadLeft = False
            self.DpadRight = False
        elif dpad_state == 5:
            self.DpadUp = False
            self.DpadDown = True
            self.DpadLeft = True
            self.DpadRight = False
        elif dpad_state == 6:
            self.DpadUp = False
            self.DpadDown = False
            self.DpadLeft = True
            self.DpadRight = False
        elif dpad_state == 7:
            self.DpadUp = True
            self.DpadDown = False
            self.DpadLeft = True
            self.DpadRight = False
        else:
            self.DpadUp = False
            self.DpadDown = False
            self.DpadLeft = False
            self.DpadRight = False


class DSLight:
    """
    代表控制器上所有灯光功能
    """

    def __init__(self) -> None:
        self.brightness: Brightness = Brightness.low  # 设置
        self.playerNumber: PlayerID = PlayerID.PLAYER_1
        self.ledOption: LedOptions = LedOptions.Both
        self.pulseOptions: PulseOptions = PulseOptions.Off
        self.TouchpadColor = (0, 0, 255)

    def setLEDOption(self, option: LedOptions) -> None:
        """
        设置 LED 选项

        参数:
            option (LedOptions): LED 选项

        引发:
            TypeError: LedOption 类型错误
        """
        if not isinstance(option, LedOptions):
            raise TypeError("需要 LEDOption 类型")
        self.ledOption = option

    def setPulseOption(self, option: PulseOptions) -> None:
        """
        设置 LED 的脉冲选项

        参数:
            option (PulseOptions): LED 的脉冲选项

        引发:
            TypeError: 脉冲选项类型错误
        """
        if not isinstance(option, PulseOptions):
            raise TypeError("需要 PulseOption 类型")
        self.pulseOptions = option

    def setBrightness(self, brightness: Brightness) -> None:
        """
        定义玩家 LED 的亮度

        参数:
            brightness (Brightness): LED 的亮度

        引发:
            TypeError: 亮度类型错误
        """
        if not isinstance(brightness, Brightness):
            raise TypeError("需要 Brightness 类型")
        self.brightness = brightness

    def setPlayerID(self, player: PlayerID) -> None:
        """
        使用选择的 LED 设置控制器的 PlayerID。
        控制器有 4 个玩家状态

        参数:
            player (PlayerID): 为控制器选择的 PlayerID

        引发:
            TypeError: [description]
        """
        if not isinstance(player, PlayerID):
            raise TypeError("需要 PlayerID 类型")
        self.playerNumber = player

    def setColorI(self, r: int, g: int, b: int) -> None:
        """
        设置控制器触摸板周围的颜色

        参数:
            r (int): 红色通道
            g (int): 绿色通道
            b (int): 蓝色通道

        引发:
            TypeError: 颜色通道类型错误
            Exception: 颜色通道超出范围
        """
        if not isinstance(r, int) or not isinstance(g, int) or not isinstance(b, int):
            raise TypeError("颜色参数需要是 int")
        # 检查颜色是否超出范围
        if (r > 255 or g > 255 or b > 255) or (r < 0 or g < 0 or b < 0):
            raise Exception("颜色值仅从 0 到 255")
        self.TouchpadColor = (r, g, b)

    def setColorT(self, color: Tuple[int, int, int]) -> None:
        """
        将触摸板周围的颜色设置为元组

        参数:
            color (tuple): 颜色作为元组

        引发:
            TypeError: 颜色类型错误
            Exception: 颜色通道超出范围
        """
        if not isinstance(color, tuple):
            raise TypeError("颜色类型是 tuple")
        # 解包以检查超出范围
        r, g, b = map(int, color)
        # 检查颜色是否超出范围
        if (r > 255 or g > 255 or b > 255) or (r < 0 or g < 0 or b < 0):
            raise Exception("颜色值仅从 0 到 255")
        self.TouchpadColor = (r, g, b)


class DSAudio:
    def __init__(self) -> None:
        """
        初始化控制器的有限音频功能
        """
        self.microphone_mute = 0
        self.microphone_led = 0

    def setMicrophoneLED(self, value: bool) -> None:
        """
        激活或禁用麦克风 LED。
        这不会改变麦克风本身的静音/取消静音。

        参数:
            value (bool): 开启或关闭麦克风 LED

        引发:
            Exception: LED 的错误状态
        """
        if not isinstance(value, bool):
            raise TypeError("MicrophoneLED 只能是 bool")
        self.microphone_led = value

    def setMicrophoneState(self, state: bool) -> None:
        """
        设置麦克风状态并相应设置麦克风 LED

        参数:
            state (bool): 麦克风的期望状态

        引发:
            TypeError: state 不是 bool
        """

        if not isinstance(state, bool):
            raise TypeError("state 需要是 bool")

        self.setMicrophoneLED(state)  # 相应设置 LED
        self.microphone_mute = state


class DSTrigger:
    """
    Dualsense 扳机类。允许多个 :class:`TriggerModes <pydualsense.enums.TriggerModes>` 和多个力

    # TODO: 使此接口更用户友好，以便开发者知道他在做什么
    """

    def __init__(self) -> None:
        # 扳机模式
        self.mode: TriggerModes = TriggerModes.Off

        # 扳机的力参数
        self.forces = [0 for i in range(7)]

    def setForce(self, forceID: int = 0, force: int = 0) -> None:
        """
        设置选择的力参数的力

        参数:
            forceID (int, optional): 力参数。默认为 0。
            force (int, optional): 应用于参数的力。默认为 0。

        引发:
            TypeError: forceID 或 force 类型错误
            Exception: 选择了错误的力参数
        """
        if not isinstance(forceID, int) or not isinstance(force, int):
            raise TypeError("forceID 和 force 需要是 int 类型")

        if forceID > 6 or forceID < 0:
            raise Exception("只有 7 个参数可用")

        self.forces[forceID] = force

    def setMode(self, mode: TriggerModes) -> None:
        """
        设置扳机的模式

        参数:
            mode (TriggerModes): 扳机模式

        引发:
            TypeError: 错误的扳机模式类型
        """
        if not isinstance(mode, TriggerModes):
            raise TypeError("扳机模式参数需要是 `TriggerModes` 类型")

        self.mode = mode


class DSGyro:
    """
    代表控制器陀螺仪的类
    """

    def __init__(self) -> None:
        self.Pitch = 0
        self.Yaw = 0
        self.Roll = 0


class DSAccelerometer:
    """
    代表控制器加速度计的类
    """

    def __init__(self) -> None:
        self.X = 0
        self.Y = 0
        self.Z = 0


class DSBattery:
    """
    代表控制器电池的类
    """

    def __init__(self) -> None:
        self.State = BatteryState.POWER_SUPPLY_STATUS_UNKNOWN
        self.Level = 0
