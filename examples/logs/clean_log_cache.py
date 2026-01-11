import os

# 清理当前目录（examples/logs）下以 .log 结尾的日志文件

def clean_log_cache() -> None:
    # 计算当前脚本所在目录作为日志目录
    base = os.path.dirname(__file__)
    # 列出目录内所有 .log 文件并计数
    names = [n for n in os.listdir(base) if n.endswith(".log")]
    count = len(names)
    # 逐个删除，失败时忽略异常保证尽可能清理
    for name in names:
        path = os.path.join(base, name)
        try:
            os.remove(path)
        except OSError:
            pass
    # 输出删除的日志文件数量
    print(f"removed {count} log files")

if __name__ == "__main__":
    clean_log_cache()
