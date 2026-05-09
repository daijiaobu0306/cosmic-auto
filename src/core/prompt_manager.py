"""提示词管理模块 - 负责自定义提示词的加载、保存、重置"""
import json
import os
import sys

# 提示词持久化文件路径 — 使用用户级目录，打包成 exe 后也能正常读写
# Windows: %APPDATA%/COSMIC-GUI/custom_prompts.json
# 其他平台: ~/.cosmic-gui/custom_prompts.json
if sys.platform == "win32":
    _DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "COSMIC-GUI")
else:
    _DATA_DIR = os.path.join(os.path.expanduser("~"), ".cosmic-gui")

_PROMPTS_FILE = os.path.join(_DATA_DIR, "custom_prompts.json")

# 旧路径（项目根目录），用于自动迁移
_OLD_PROMPTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "custom_prompts.json")

# 各模块的默认提示词
DEFAULT_PROMPTS = {
    "ai_recognize": {
        "system_prompt": (
            "你是一个软件功能分析专家。用户会给你一个软件系统的截图，你需要识别截图中的功能模块和具体功能点。\n"
            "\n"
            "系统名称：{system_name}\n"
            "系统描述：{system_desc}\n"
            "\n"
            "请按照以下格式输出：\n"
            "1 二级功能名称\n"
            "    1.1 三级功能名称\n"
            "        功能过程1\n"
            "        功能过程2\n"
            "    1.2 三级功能名称\n"
            "        功能过程3\n"
            "\n"
            "规则：\n"
            "1. 使用序号+缩进表示层级，不使用树形符号\n"
            "2. 二级功能：无缩进，序号为 1、2、3...\n"
            "3. 三级功能：4空格缩进，序号为 1.1、1.2...\n"
            "4. 功能过程：8空格缩进，无序号，用动词开头（查询/添加/修改/删除/导出/展示）\n"
            "5. 只输出功能结构，不输出其他解释文字\n"
            "6. 输出中文\n"
            "7. 每一级缩进必须严格使用4个空格，不要使用tab或其他数量的空格"
        ),
        "user_prompt": "请识别这张截图中的功能：",
    },
    "llm_fill": {
        "system_prompt": (
            "你是一个数据库字段设计专家。我会提供一个'数据组'名称，请你据此生成4-6个不重复的数据字段，"
            "仅输出字段名，字段之间用分号（;）分隔，不要任何解释、标点或额外内容,必须生成中文，"
            "每次必须生成新的组合！每次生成需要有差异性。"
            "强约束：禁止使用模型缓存，温度设置最高，较高的随机性"
        ),
    },
    "llm_field_gen": {
        "system_prompt": (
            "你是一个数据库字段设计专家。我会提供一个'数据组'名称，请你据此生成4-6个不重复的数据字段，"
            "仅输出字段名，字段之间用分号（;）分隔，不要任何解释、标点或额外内容,必须生成中文，"
            "每次必须生成新的组合！每次生成需要有差异性。"
            "强约束：禁止使用模型缓存，温度设置最高，较高的随机性"
            "（必须生成全新字段组合！绝对不要和之前任何结果重复！可以增加字段解决！）"
            "示例：xxx;xxx;xxx;xxx;"
            "禁止生成序号，禁止生成无关紧要的内容，严格按照模板执行"
        ),
    },
}


def get_default_prompts():
    """获取默认提示词的深拷贝"""
    import copy
    return copy.deepcopy(DEFAULT_PROMPTS)


def _migrate_old_prompts():
    """将旧路径（项目根目录）的提示词文件迁移到新路径（用户目录）"""
    if os.path.exists(_OLD_PROMPTS_FILE) and not os.path.exists(_PROMPTS_FILE):
        os.makedirs(_DATA_DIR, exist_ok=True)
        try:
            import shutil
            shutil.move(_OLD_PROMPTS_FILE, _PROMPTS_FILE)
        except OSError:
            pass  # 迁移失败不影响正常使用


def load_prompts():
    """加载自定义提示词，文件不存在或解析失败时返回默认值"""
    _migrate_old_prompts()

    if not os.path.exists(_PROMPTS_FILE):
        return get_default_prompts()

    try:
        with open(_PROMPTS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # 用默认值填充缺失的 key
        defaults = get_default_prompts()
        for module, prompts in defaults.items():
            if module not in saved:
                saved[module] = prompts
            else:
                for key, val in prompts.items():
                    if key not in saved[module]:
                        saved[module][key] = val
        return saved
    except (json.JSONDecodeError, OSError):
        return get_default_prompts()


def save_prompts(prompts):
    """将自定义提示词保存到 JSON 文件"""
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)


def reset_prompts():
    """删除自定义提示词文件，恢复为默认"""
    if os.path.exists(_PROMPTS_FILE):
        os.remove(_PROMPTS_FILE)
