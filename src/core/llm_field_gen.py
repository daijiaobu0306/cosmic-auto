"""LLM 数据字段生成 - 根据数据组名称生成数据字段"""
import asyncio
import aiohttp
import pandas as pd


SYSTEM_PROMPT = (
    "你是一个数据库字段设计专家。我会提供一个'数据组'名称，请你据此生成4-6个不重复的数据字段，"
    "仅输出字段名，字段之间用分号（;）分隔，不要任何解释、标点或额外内容,必须生成中文，"
    "每次必须生成新的组合！每次生成需要有差异性。"
    "强约束：禁止使用模型缓存，温度设置最高，较高的随机性"
)

SYSTEM_PROMPT_RETRY = (
    "你是一个数据库字段设计专家。我会提供一个'数据组'名称，请你据此生成4-6个不重复的数据字段，"
    "仅输出字段名，字段之间用分号（;）分隔，不要任何解释、标点或额外内容,必须生成中文，"
    "每次必须生成新的组合！每次生成需要有差异性。"
    "强约束：禁止使用模型缓存，温度设置最高，较高的随机性"
    "（必须生成全新字段组合！绝对不要和之前任何结果重复！可以增加字段解决！）"
)


def _build_system_prompt(ddl_context: str = None) -> str:
    base = SYSTEM_PROMPT
    if ddl_context:
        base += f"\n\n参考数据库表结构：\n{ddl_context}\n请优先使用上述表中的实际字段名，并适当扩展。"
    return base


def _build_system_prompt_retry(ddl_context: str = None) -> str:
    base = SYSTEM_PROMPT_RETRY
    if ddl_context:
        base += f"\n\n参考数据库表结构：\n{ddl_context}\n请优先使用上述表中的实际字段名，并适当扩展。"
    return base


async def _call_llm_once(session, semaphore, api_key, model, url, prompt_text, attempt=0, ddl_context=None):
    if attempt > 0:
        system_content = _build_system_prompt_retry(ddl_context)
    else:
        system_content = _build_system_prompt(ddl_context)
    user_content = prompt_text

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        "temperature": 1.5,
        "top_p": 0.95,
        "extra_body": {"enable_thinking": False}
    }

    async with semaphore:
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return f"[ERROR {response.status}]"
        except Exception as e:
            return f"[EXCEPTION: {str(e)}]"


async def _generate_unique_result(session, semaphore, api_key, model, url, original_input, seen_results, seen_lock, ddl_context=None):
    MAX_RETRY = 2
    for attempt in range(MAX_RETRY + 1):
        result = await _call_llm_once(session, semaphore, api_key, model, url, original_input, attempt, ddl_context)
        if result.startswith(("[ERROR", "[EXCEPTION")):
            if attempt == MAX_RETRY:
                print(f"❌ 最终失败 ({original_input}): {result}")
                return result
            await asyncio.sleep(0.5)
            continue

        async with seen_lock:
            if result not in seen_results:
                seen_results.add(result)
                if attempt > 0:
                    print(f"✅ 重试成功（第{attempt}次）: {result[:60]}...")
                return result
            else:
                print(f"⚠️ 重复（第{attempt + 1}次）: {result[:60]}... | 输入: {original_input}")

        await asyncio.sleep(0.3)

    final_result = f"[重复未解决] {result}"
    async with seen_lock:
        seen_results.add(final_result)
    return final_result


async def llm_field_gen_async(api_key, model, url, excel_file, output_file, callback_print, ddl_context=None):
    """异步版本，供 QThread 调用"""
    seen_results = set()
    seen_lock = asyncio.Lock()
    MAX_CONCURRENT = 10

    print = callback_print
    print("📥 正在读取 Excel 文件...")

    df = pd.read_excel(excel_file, engine='openpyxl')
    if df.shape[1] < 12:
        raise ValueError("Excel 文件必须至少包含 L 列（第12列）")

    l_column = df.iloc[:, 11]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = []

    print(f"🚀 准备处理 {len(l_column)} 行，最大并发: {MAX_CONCURRENT}")

    async with aiohttp.ClientSession() as session:
        m_column = df.iloc[:, 12] if df.shape[1] > 12 else [None] * len(df)

        for idx, text in enumerate(l_column):
            if pd.isna(text) or str(text).strip() == "":
                tasks.append(asyncio.create_task(asyncio.sleep(0, result="")))
            elif df.shape[1] > 12 and not pd.isna(m_column[idx]) and str(m_column[idx]).strip() != "":
                tasks.append(asyncio.create_task(asyncio.sleep(0, result=m_column[idx])))
                print(f"⏭️ 跳过第 {idx+1} 行：M列已有数据")
            else:
                clean_text = str(text).strip()
                tasks.append(_generate_unique_result(session, semaphore, api_key, model, url, clean_text, seen_results, seen_lock, ddl_context))

        results = await asyncio.gather(*tasks)

    if df.shape[1] < 13:
        df = df.reindex(columns=df.columns.tolist() + [None])
    df.iloc[:, 12] = results

    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n✅ 处理完成！结果已保存至: {output_file}")
    print(f"📊 新增生成结果数: {len(seen_results)}")
