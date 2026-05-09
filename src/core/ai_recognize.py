"""AI 识图核心逻辑 - 调用多模态模型识别截图，输出功能清单 TXT"""
import os
import base64
import asyncio
import aiohttp
from pathlib import Path


# 系统提示词模板
SYSTEM_PROMPT = """你是一个软件功能分析专家。用户会给你一个软件系统的截图，你需要识别截图中的功能模块和具体功能点。

系统名称：{system_name}
系统描述：{system_desc}

请按照以下格式输出：
1 二级功能名称
    1.1 三级功能名称
        功能过程1
        功能过程2
    1.2 三级功能名称
        功能过程3

规则：
1. 使用序号+缩进表示层级，不使用树形符号
2. 二级功能：无缩进，序号为 1、2、3...
3. 三级功能：4空格缩进，序号为 1.1、1.2...
4. 功能过程：8空格缩进，无序号，用动词开头（查询/添加/修改/删除/导出/展示）
5. 只输出功能结构，不输出其他解释文字
6. 输出中文
7. 每一级缩进必须严格使用4个空格，不要使用tab或其他数量的空格"""


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_files(folder_path: str) -> list[str]:
    """遍历文件夹，获取所有 JPG/PNG 文件，按文件名排序"""
    supported_ext = {".jpg", ".jpeg", ".png"}
    image_files = []

    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in supported_ext:
            image_files.append(str(file))

    # 按文件名排序
    image_files.sort(key=lambda x: Path(x).name)
    return image_files


def get_mime_type(file_path: str) -> str:
    """根据文件扩展名获取 MIME 类型"""
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    return mime_map.get(ext, "image/jpeg")


async def _call_vision_api(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    api_key: str,
    api_url: str,
    model_name: str,
    image_path: str,
    system_prompt: str,
    callback_print=None,
    attempt: int = 0,
    user_prompt: str = "请识别这张截图中的功能：",
) -> str:
    """调用多模态 Vision API 识别单张图片"""
    # 编码图片
    base64_image = encode_image_to_base64(image_path)
    mime_type = get_mime_type(image_path)

    # 图片大小检查
    image_size_kb = len(base64_image) * 3 / 4 / 1024
    if callback_print:
        callback_print(f"  图片大小: {image_size_kb:.1f} KB")

    # 确保 URL 以 /v1/chat/completions 结尾
    api_url = api_url.rstrip("/")
    if not api_url.endswith("/chat/completions"):
        if api_url.endswith("/v1"):
            full_url = f"{api_url}/chat/completions"
        else:
            full_url = f"{api_url}/v1/chat/completions"
    else:
        full_url = api_url

    if callback_print and attempt == 0:
        callback_print(f"  请求地址: {full_url}")
        callback_print(f"  模型名称: {model_name}")
        # 调试：打印请求格式（不打印 base64 内容）
        callback_print(f"  请求类型: vision多模态请求")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 构造多模态消息内容（嵌套格式，兼容阿里云百炼等国内API）
    content_parts = [
        {"type": "text", "text": user_prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        },
    ]

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts},
        ],
        "max_completion_tokens": 4096,
    }

    # 设置超时：连接超时30秒，总超时300秒（5分钟）
    timeout = aiohttp.ClientTimeout(total=300, connect=30)

    async with semaphore:
        try:
            if callback_print:
                callback_print(f"  正在发送请求...")
                callback_print(f"  认证方式: Bearer Token")
            async with session.post(full_url, json=payload, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    error_text = await response.text()
                    return f"[ERROR {response.status}] {error_text[:200]}"
        except asyncio.TimeoutError:
            return f"[EXCEPTION] 请求超时（5分钟）"
        except Exception as e:
            return f"[EXCEPTION] {str(e)}"


async def _recognize_single_image(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    api_key: str,
    api_url: str,
    model_name: str,
    image_path: str,
    system_prompt: str,
    callback_print=None,
    max_retry: int = 2,
    user_prompt: str = "请识别这张截图中的功能：",
) -> str:
    """识别单张图片，支持重试"""
    image_name = Path(image_path).name

    for attempt in range(max_retry + 1):
        if attempt > 0:
            if callback_print:
                callback_print(f"  重试第 {attempt} 次: {image_name}")

        result = await _call_vision_api(
            session, semaphore, api_key, api_url, model_name,
            image_path, system_prompt, callback_print, attempt,
            user_prompt=user_prompt,
        )

        if not result.startswith(("[ERROR", "[EXCEPTION")):
            return result

        if attempt < max_retry:
            await asyncio.sleep(1)

    # 所有重试都失败
    if callback_print:
        callback_print(f"  识别失败: {image_name} - {result}")
    return f"# 识别失败: {image_name}\n# 错误: {result}\n"


async def recognize_images_async(
    image_folder: str,
    system_name: str,
    system_desc: str,
    api_key: str,
    api_url: str,
    model_name: str,
    callback_print=None,
    custom_system_prompt=None,
    custom_user_prompt=None,
) -> str:
    """
    异步识别文件夹中的所有截图，返回带层级缩进的 TXT 文本。

    Args:
        image_folder: 截图文件夹路径
        system_name: 系统名称（一级功能）
        system_desc: 系统描述
        api_key: API 密钥
        api_url: API 地址
        model_name: 模型名称
        callback_print: 日志输出回调函数

    Returns:
        带层级缩进的功能清单文本
    """
    if callback_print:
        print = callback_print

    # 打印 API 配置（隐藏密钥）
    masked_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
    print(f"API 配置:")
    print(f"  URL: {api_url}")
    print(f"  Key: {masked_key}")
    print(f"  Model: {model_name}")
    print("")

    # 获取图片列表
    print(f"正在扫描文件夹: {image_folder}")
    image_files = get_image_files(image_folder)

    if not image_files:
        raise ValueError(f"文件夹中没有找到 JPG/PNG 图片: {image_folder}")

    print(f"找到 {len(image_files)} 张图片")
    print("")

    # 构建系统提示词（优先使用自定义）
    prompt_template = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT
    system_prompt = prompt_template.format(
        system_name=system_name,
        system_desc=system_desc,
    )

    # 用户提示词
    user_prompt = custom_user_prompt if custom_user_prompt else "请识别这张截图中的功能："

    # 并发控制
    semaphore = asyncio.Semaphore(5)
    all_results = []

    async with aiohttp.ClientSession() as session:
        # 逐张识别（保持顺序）
        for idx, image_path in enumerate(image_files):
            image_name = Path(image_path).name
            print(f"正在识别 [{idx + 1}/{len(image_files)}]: {image_name}")

            result = await _recognize_single_image(
                session, semaphore, api_key, api_url, model_name,
                image_path, system_prompt, callback_print,
                user_prompt=user_prompt,
            )

            all_results.append(result)
            print(f"  识别完成: {image_name}")

    # 合并所有结果
    print(f"\n所有图片识别完成，正在合并结果...")
    merged_text = "\n\n".join(all_results)

    return merged_text


def save_txt(content: str, output_path: str) -> str:
    """保存 TXT 文件"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write(content)

    return str(output)


# 独立运行测试
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("用法: python ai_recognize.py <图片文件夹> <系统名称> <系统描述>")
        sys.exit(1)

    folder = sys.argv[1]
    name = sys.argv[2]
    desc = sys.argv[3]

    # 需要设置环境变量或直接传入
    api_key = os.environ.get("API_KEY", "")
    api_url = os.environ.get("API_URL", "https://api.openai.com/v1")
    model = os.environ.get("MODEL_NAME", "gpt-4o")

    if not api_key:
        print("请设置 API_KEY 环境变量")
        sys.exit(1)

    result = asyncio.run(recognize_images_async(
        folder, name, desc, api_key, api_url, model, print
    ))

    print("\n" + "=" * 50)
    print("识别结果：")
    print("=" * 50)
    print(result)
