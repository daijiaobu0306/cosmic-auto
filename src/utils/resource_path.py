"""工具函数"""
import os
import sys


def resource_path(relative_path):
    """处理 PyInstaller 打包后的资源路径"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)