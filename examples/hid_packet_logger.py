import os
import sys
import time

from pydualsense.pydualsense import pydualsense


def main() -> None:
    # 可选参数：
    # -v/--verbose 打开调试日志
    # --backend=hidapi 指定 HID 后端（仅支持 hidapi）
    verbose = ("-v" in sys.argv) or ("--verbose" in sys.argv)
    backend = None
    for arg in sys.argv:
        if arg.startswith("--backend="):
            backend = arg.split("=", 1)[1].strip().lower()
    # 记录目录固定为 examples/logs，下方会自动创建
    base = os.path.dirname(__file__)
    log_dir = os.path.join(base, "logs")
    # 创建手柄对象，启用 HID 输入/输出报文记录
    ds = pydualsense(verbose=verbose, backend=backend)
    ds.enable_packet_logger(log_dir)
    ds.init()
    print(f"logging to: {log_dir}")
    try:
        # 主循环保持连接与记录，Ctrl+C 退出
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    # 退出前关闭记录并释放资源
    ds.disable_packet_logger()
    ds.close()


if __name__ == "__main__":
    main()
