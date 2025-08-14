import asyncio
import random
import time
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError

# 配置参数
CONFIG = {
    "EXCEL_PATH": "boss.xlsx",  # 数据文件路径
    "TAB_COUNT": 5,  # 同时并行的页签数量
    "MAX_RETRIES": 2,  # 单个ID最大重试次数
    "BATCH_SIZE": 10,  # 每个页签一次处理的ID数量
    "PROCESS_BATCH": 50,  # 每批处理的ID总数
    "REST_RANGE": (60, 180),  # 休息时间范围(秒)，1-3分钟
    "START_ROW": 1,  # 起始处理行（Excel行号，1-based），如80表示从第80行开始
    "USER_AGENTS": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
    ],
    "READ_COLUMN": 0,  # 读取ID的列号（0-based）
    "WRITE_COLUMN": 6,  # 写入结果的列号（0-based）
}


async def tab_worker(page, tab_id, ids, results):
    """单个页签的工作函数：独立处理分配的ID列表"""
    print(f"页签 {tab_id} 开始处理 {len(ids)} 个ID")
    for i, id in enumerate(ids):
        try:
            # 导航到目标页面（仅等待DOM加载，加速）
            await page.goto(f"https://www.zhipin.com/gongsi/{id}.html", wait_until="domcontentloaded", timeout=15000)
            
            # 随机滚动模拟用户行为
            await page.mouse.wheel(0, random.randint(200, 500))
            await asyncio.sleep(random.uniform(2, 5))
            
            # 提取目标文本
            await page.wait_for_selector(".business-detail-name", timeout=8000)
            name = await page.evaluate("""
                () => {
                    const el = document.querySelector('.business-detail-name');
                    return Array.from(el.childNodes)
                        .filter(n => n.nodeType === 3 && n.textContent.trim())
                        .map(n => n.textContent.trim()).join('') || '无文本';
                }
            """)
            
            results.append((id, name))
            print(f"页签 {tab_id} 完成 {i+1}/{len(ids)}：ID {id} -> {name[:20]}")
            
        except TimeoutError:
            print(f"页签 {tab_id} ID {id} 超时")
            results.append((id, "超时"))
        except Exception as e:
            print(f"页签 {tab_id} ID {id} 错误：{str(e)[:30]}")
            results.append((id, "错误"))
        
        # 每处理BATCH_SIZE个ID，随机刷新页面（反反爬）
        if (i + 1) % CONFIG["BATCH_SIZE"] == 0:
            await page.goto("https://www.zhipin.com/", wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1, 2))


async def process_batch(ids_batch):
    """处理单个批次的ID"""
    # 平均分配当前批次ID到多个页签
    tab_ids = [ids_batch[i::CONFIG["TAB_COUNT"]] for i in range(CONFIG["TAB_COUNT"])]
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # 创建页签和任务
        pages = []
        tasks = []
        results = []
        
        for i in range(CONFIG["TAB_COUNT"]):
            context = await browser.new_context(user_agent=random.choice(CONFIG["USER_AGENTS"]))
            page = await context.new_page()
            await page.goto("https://www.zhipin.com/")
            pages.append(page)
            
            task = asyncio.create_task(tab_worker(page, i+1, tab_ids[i], results))
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        # 关闭资源
        for page in pages:
            await page.close()
        await browser.close()
        
        return results


def main():
    # 读取ID列表
    try:
        df = pd.read_excel(CONFIG["EXCEL_PATH"])
    except FileNotFoundError:
        print(f"错误：找不到文件 {CONFIG['EXCEL_PATH']}")
        return
    
    # 计算起始行的索引（Excel行号转iloc索引：1-based -> 0-based）
    start_row_excel = CONFIG["START_ROW"]
    start_row_idx = start_row_excel - 1  # 例如：第80行 -> 索引79
    
    # 校验起始行是否超出数据范围
    if start_row_idx >= len(df):
        print(f"错误：起始行 {start_row_excel} 超出数据总行数（共{len(df)}行）")
        return
    
    # 提取起始行及之后的ID列数据（保留原始索引，用于后续更新）
    id_series = df.iloc[start_row_idx:, CONFIG["READ_COLUMN"]].dropna().astype(str)
    if id_series.empty:
        print(f"从第{start_row_excel}行开始无有效ID数据（列索引：{CONFIG['READ_COLUMN']}）")
        return
    
    total_ids = len(id_series)
    print(f"总ID数：{total_ids}，从第{start_row_excel}行开始处理，分为{CONFIG['TAB_COUNT']}个页签并行处理，每{CONFIG['PROCESS_BATCH']}个ID休息一次")
    
    # 按批次处理ID
    for batch_idx in range(0, total_ids, CONFIG["PROCESS_BATCH"]):
        # 获取当前批次的ID（包含原始索引）
        batch_start = batch_idx
        batch_end = min(batch_idx + CONFIG["PROCESS_BATCH"], total_ids)
        current_batch = id_series.iloc[batch_start:batch_end]
        current_ids = current_batch.tolist()
        batch_num = (batch_idx // CONFIG["PROCESS_BATCH"]) + 1
        
        # 计算当前批次对应的Excel行号范围
        first_row_in_batch = start_row_excel + batch_start
        last_row_in_batch = start_row_excel + batch_end - 1
        print(f"\n===== 开始处理第 {batch_num} 批：{first_row_in_batch}-{last_row_in_batch}行（共{batch_end - batch_start}个ID） =====")
        
        # 处理当前批次
        batch_results = asyncio.run(process_batch(current_ids))
        
        # 映射ID到结果
        id_to_name = {id: name for id, name in batch_results}
        
        # 更新当前批次的结果到DataFrame（使用原始索引定位行）
        for idx, id_val in current_batch.items():  # idx是原始DataFrame中的iloc索引
            df.iloc[idx, CONFIG["WRITE_COLUMN"]] = id_to_name.get(str(id_val), "未处理")
        
        # 保存当前批次结果
        df.to_excel(CONFIG["EXCEL_PATH"], index=False)
        print(f"第 {batch_num} 批处理完成，已保存结果（累计处理到第{last_row_in_batch}行）")
        
        # 如果不是最后一批，休息一段时间
        if batch_end < total_ids:
            rest_time = random.randint(*CONFIG["REST_RANGE"])
            print(f"准备休息 {rest_time//60}分{rest_time%60}秒...")
            time.sleep(rest_time)  # 使用同步休眠，确保休息生效
    
    print(f"\n全部完成，所有结果已写入第{CONFIG['WRITE_COLUMN']+1}列，共处理{total_ids}个ID（从第{start_row_excel}行开始）")


if __name__ == "__main__":
    main()