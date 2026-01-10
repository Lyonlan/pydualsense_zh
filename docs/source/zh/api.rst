API 概览
========

模块说明
--------

- 主接口与状态：pydualsense.pydualsense（连接、事件、状态、输出）
- 枚举类型：pydualsense.enums（连接、LED、玩家编号、扳机模式、电池状态）
- 事件系统：pydualsense.event_system（C# 风格事件订阅/触发）
- 报文校验：pydualsense.checksum（输出报文校验）
- HidGuardian 检测：pydualsense.hidguardian（Windows 平台设备隐藏检测）

提示
----

本项目启用 ``autodoc`` 自动从代码 Docstring 生成 API 文档。如果构建时导入系统依赖失败（如 ``hidapi``），生成的 API 页面可能缺失部分条目。可在 ``conf.py`` 使用 ``autodoc_mock_imports`` 进行屏蔽。

详细 API
--------

.. toctree::
   :maxdepth: 2

   ds_enum
   ds_main
   ds_eventsystem
