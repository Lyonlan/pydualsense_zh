"""
事件系统实现

提供 C# 风格的事件订阅/取消订阅机制，用于在输入状态变化时触发回调。
"""
from typing import Any, Callable, List


# mypy: disable_error_code="type-arg"
class Event:
    """
    事件驱动系统的基类
    """

    def __init__(self, available=True) -> None:
        """
        初始化事件系统
        """
        self._event_handler: List[Callable] = []
        self.available = available

    def subscribe(self, fn: Callable) -> Any:
        """
        添加事件订阅

        Args:
            fn (function): 回调函数
        """
        if not self.available:
            raise ValueError("Event unavailable")
        self._event_handler.append(fn)
        return self

    def unsubscribe(self, fn: Callable) -> Any:
        """
        删除事件订阅 fn

        Args:
            fn (function): 回调函数
        """
        if not self.available:
            raise ValueError("Event unavailable")
        self._event_handler.remove(fn)
        return self

    def __iadd__(self, fn: Callable) -> Any:
        """
        添加事件订阅 fn

        Args:
            fn (function): 回调函数
        """
        if not self.available:
            raise ValueError("Event unavailable")
        self._event_handler.append(fn)
        return self

    def __isub__(self, fn: Callable) -> Any:
        """
        删除事件订阅 fn

        Args:
            fn (function): 回调函数
        """
        if not self.available:
            raise ValueError("Event unavailable")
        self._event_handler.remove(fn)
        return self

    def __call__(self, *args, **kwargs) -> None: # type: ignore[arg-type]
        """
        调用所有事件订阅函数
        """
        if not self.available:
            raise ValueError("Event unavailable")
        for eventhandler in self._event_handler:
            eventhandler(*args, **kwargs)
