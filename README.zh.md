# pydualsense（派生版）

中文 | [English](./README.md)

基于 pydualsense 的 fork，目标是在 macOS 上用 PS5 DualSense 触控板进行系统控制。保留上游 API，补充中文文档与本地化示例。遵循 MIT 许可，致谢原作者 Florian (flok)。

## 文档
- 英文：`make html -C docs` 输出至 `docs/build/html`
- 中文：`make html-zh -C docs` 输出至 `docs/build/zh/html`

## 安装
- Windows：下载 [hidapi](https://github.com/libusb/hidapi/releases) 的 x64 .dll 并加入 PATH，然后安装 PyPI 包
  ```bash
  pip install --upgrade pydualsense
  ```
- Linux：添加 udev 规则，安装 `libhidapi-dev`，然后安装 PyPI 包
  ```bash
  sudo cp 70-ps5-controller.rules /etc/udev/rules.d
  sudo udevadm control --reload-rules && sudo udevadm trigger
  sudo apt install libhidapi-dev
  pip install --upgrade pydualsense
  ```

## 快速上手
```python
from pydualsense import pydualsense, TriggerModes

def on_cross(state):
    print(state)

ds = pydualsense()
ds.init()
ds.cross_pressed += on_cross
ds.light.setColorI(255, 0, 0)
ds.triggerL.setMode(TriggerModes.Rigid)
ds.triggerL.setForce(1, 255)
ds.close()
```

## 依赖
- hidapi-usb >= 0.3

## 致谢
- 上游项目 pydualsense（Florian/flok）
- 参考资料见上游 README

## 规划
- 将触控板输入映射为 macOS 系统事件（光标/点击/手势）
- 支持多手柄
