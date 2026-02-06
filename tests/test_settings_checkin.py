# ===========================================================================
# Chronos AI Learning Companion
# File: tests/test_settings_checkin.py
# Purpose: 打卡设置字段测试
# ===========================================================================

"""
打卡设置字段测试

确保 Settings 默认值与反序列化逻辑包含打卡相关字段。
"""

from models.settings_model import Settings


def test_checkin_defaults():
    """默认值应包含空网址与关闭自动打开。"""
    settings = Settings()
    assert settings.checkin_url == ""
    assert settings.checkin_auto_open is False


def test_checkin_from_dict():
    """from_dict 应正确读取打卡字段。"""
    data = {
        "checkin_url": "https://example.com/checkin",
        "checkin_auto_open": True,
    }
    settings = Settings.from_dict(data)
    assert settings.checkin_url == "https://example.com/checkin"
    assert settings.checkin_auto_open is True
