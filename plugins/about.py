from nonebot import on_regex
from nonebot.rule import to_me
from pathlib import Path


__zx_plugin_name__ = "关于"
__plugin_usage__ = """
usage：
    想要更加了解 Lacia 吗
    指令：
        关于
""".strip()
__plugin_des__ = "想要更加了解 Lacia 吗"
__plugin_cmd__ = ["关于"]
__plugin_version__ = 0.1
__plugin_type__ = ("其他",)
__plugin_author__ = "Nova-No1r"
__plugin_settings__ = {
    "level": 1,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["关于"],
}


about = on_regex("^关于$", priority=5, block=True, rule=to_me())


@about.handle()
async def _():
    ver_file = Path() / '__version__'
    version = None
    if ver_file.exists():
        with open(ver_file, 'r', encoding='utf8') as f:
            version = f.read().split(':')[-1].strip()
    msg = f"""
『 Lacia Bot 』(Modified From Zhenxun_Bot)
版本：{version}
简介：色。
项目地址：https://github.com/Nova-Noir/zhenxun_bot
原项目地址: https://github.com/Hibiker/zhenxun_bot
    """.strip()
    await about.send(msg)
