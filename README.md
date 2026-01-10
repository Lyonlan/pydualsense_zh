# pydualsense (fork)

[中文](./README.zh.md) | English

Fork of pydualsense, focused on using the PS5 DualSense touchpad to control macOS. Preserves upstream API; adds Chinese docs and localized examples. MIT; credits to Florian (flok).

# Documentation

Build docs locally:
- English: `make html -C docs` → `docs/build/html`
- Chinese: `make html-zh -C docs` → `docs/build/zh/html`

# Installation


## Windows 
Download [hidapi](https://github.com/libusb/hidapi/releases) and place the x64 .dll file into your PATH. Then install from [PyPI](https://pypi.org/project/pydualsense/). 

```bash
pip install --upgrade pydualsense
```

## Linux

On Linux, add a udev rule to access the controller without root:

```bash
sudo cp 70-ps5-controller.rules /etc/udev/rules.d
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Install hidapi via your package manager (Ubuntu: `libhidapi-dev`):

```bash
sudo apt install libhidapi-dev
```

Then install from [PyPI](https://pypi.org/project/pydualsense/). 

```bash
pip install --upgrade pydualsense
```

# Usage (quickstart)

```python

from pydualsense import pydualsense, TriggerModes

def cross_pressed(state):
    print(state)

ds = pydualsense()
ds.init()

ds.cross_pressed += cross_pressed
ds.light.setColorI(255,0,0)
ds.triggerL.setMode(TriggerModes.Rigid)
ds.triggerL.setForce(1, 255)
ds.close()
```

See [examples](https://github.com/flok/pydualsense/tree/master/examples) for more ideas.

# Help wanted

Help wanted from people that want to use this and have feature requests. Just open a issue with the correct label.

# Dependencies

- hidapi-usb >= 0.3

# Credits


Upstream credits:


- [https://www.reddit.com/r/gamedev/comments/jumvi5/dualsense_haptics_leds_and_more_hid_output_report/](https://www.reddit.com/r/gamedev/comments/jumvi5/dualsense_haptics_leds_and_more_hid_output_report/)
- [https://github.com/Ryochan7/DS4Windows](https://github.com/Ryochan7/DS4Windows)

# Roadmap
- macOS touchpad mapping to system events (cursor/gestures)
- multi-controller support
