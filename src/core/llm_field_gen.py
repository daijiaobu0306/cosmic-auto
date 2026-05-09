"""LLM 数据字段生成 - 根据数据组名称生成数据字段"""
import asyncio
import time
import aiohttp
import pandas as pd


SYSTEM_PROMPT = (
    "你是一个数据库字段设计专家。我会提供一个'数据组'名称，请你据此生成4-6个不重复的数据字段，"
    "仅输出字段名，字段之间用分号（;）分隔，不要任何解释、标点或额外内容,必须生成中文，"
    "每次必须生成新的组合！每次生成需要有差异性。"
    "强约束：禁止使用模型缓存，温度设置最高，较高的随机性"
    "（必须生成全新字段组合！绝对不要和之前任何结果重复！可以增加字段解决！）"
    "示例：xxx;xxx;xxx;xxx;"
    "禁止生成序号，禁止生成无关紧要的内容，严格按照模板执行"
)


def _build_system_prompt(ddl_context: str = None, custom_prompt: str = None) -> str:
    base = custom_prompt if custom_prompt else SYSTEM_PROMPT
    if ddl_context:
        base += f"\n\n参考数据库表结构：\n{ddl_context}\n请优先使用上述表中的实际字段名，并适当扩展。"
    return base


async def _call_llm_once(session, semaphore, api_key, model, url, prompt_text, attempt=0, ddl_context=None, custom_system_prompt=None):
    system_content = _build_system_prompt(ddl_context, custom_prompt=custom_system_prompt)
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


async def _generate_unique_result(session, semaphore, api_key, model, url, original_input, seen_results, seen_lock, ddl_context=None, row_index=None, custom_system_prompt=None):
    MAX_RETRY = 2
    for attempt in range(MAX_RETRY + 1):
        t0 = time.time()
        result = await _call_llm_once(session, semaphore, api_key, model, url, original_input, attempt, ddl_context, custom_system_prompt=custom_system_prompt)
        elapsed = time.time() - t0
        row_tag = f"行{row_index}" if row_index else ""
        if result.startswith(("[ERROR", "[EXCEPTION")):
            print(f"  ❌ {row_tag} 失败({elapsed:.1f}s): {result}")
            if attempt == MAX_RETRY:
                return result
            await asyncio.sleep(0.5)
            continue

        async with seen_lock:
            if result not in seen_results:
                seen_results.add(result)
                retry_tag = f" 重试第{attempt}次" if attempt > 0 else ""
                print(f"  ✅ {row_tag}{retry_tag}({elapsed:.1f}s): {result[:80]}")
                return result
            else:
                print(f"  ⚠️ {row_tag} 重复(第{attempt+1}次, {elapsed:.1f}s): {result[:60]}...")

        await asyncio.sleep(0.3)

    final_result = f"[重复未解决] {result}"
    async with seen_lock:
        seen_results.add(final_result)
    return final_result


async def llm_field_gen_async(api_key, model, url, excel_file, output_file, callback_print, ddl_context=None, custom_system_prompt=None):
    """异步版本，供 QThread 调用"""
    seen_results = set()
    seen_lock = asyncio.Lock()
    MAX_CONCURRENT = 10

    print = callback_print
    overall_start = time.time()

    print("📥 正在读取 Excel 文件...")
    t0 = time.time()
    df = pd.read_excel(excel_file, engine='openpyxl')
    print(f"  读取完成({time.time() - t0:.1f}s)，共 {len(df)} 行 {len(df.columns)} 列")

    if df.shape[1] < 12:
        raise ValueError("Excel 文件必须至少包含 L 列（第12列）")

    l_column = df.iloc[:, 11]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = []

    need_gen_count = 0
    skip_count = 0
    empty_count = 0

    print(f"\n🚀 准备处理 {len(l_column)} 行，最大并发: {MAX_CONCURRENT}")
    if ddl_context:
        print("📎 DDL 辅助：已开启，将参考数据库表结构生成字段")
    else:
        print("📎 DDL 辅助：未开启")

    async with aiohttp.ClientSession() as session:
        m_column = df.iloc[:, 12] if df.shape[1] > 12 else [None] * len(df)

        for idx, text in enumerate(l_column):
            row_num = idx + 1
            if pd.isna(text) or str(text).strip() == "":
                tasks.append(asyncio.create_task(asyncio.sleep(0, result="")))
                empty_count += 1
            elif df.shape[1] > 12 and not pd.isna(m_column[idx]) and str(m_column[idx]).strip() != "":
                tasks.append(asyncio.create_task(asyncio.sleep(0, result=m_column[idx])))
                print(f"  ⏭️ 第{row_num}行 跳过：M列已有数据")
                skip_count += 1
            else:
                clean_text = str(text).strip()
                print(f"  🔄 第{row_num}行 待生成: {clean_text}")
                tasks.append(_generate_unique_result(session, semaphore, api_key, model, url, clean_text, seen_results, seen_lock, ddl_context, row_index=row_num, custom_system_prompt=custom_system_prompt))
                need_gen_count += 1

        print(f"\n📊 统计：需生成 {need_gen_count} 行，跳过 {skip_count} 行，空行 {empty_count} 行")
        print(f"⏳ 开始调用大模型（预计 {need_gen_count / MAX_CONCURRENT * 3:.0f}~{need_gen_count * 5:.0f} 秒）...\n")

        t1 = time.time()
        results = await asyncio.gather(*tasks)
        print(f"\n✅ 大模型调用完成，总耗时 {time.time() - t1:.1f} 秒")

    if df.shape[1] < 13:
        df = df.reindex(columns=df.columns.tolist() + [None])
    df.iloc[:, 12] = results

    print(f"💾 正在保存文件...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"✅ 处理完成！结果已保存至: {output_file}")
    print(f"📊 新增生成结果数: {len(seen_results)}")
    print(f"⏱️ 总耗时: {time.time() - overall_start:.1f} 秒")
