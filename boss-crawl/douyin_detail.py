from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import random
import csv
import os
from typing import List, Dict


def load_existing_links(keyword: str) -> List[str]:
    """加载已爬取的链接（用于断点续爬）"""
    result_csv = f"douyin_{keyword}.csv"
    existing_links = []
    if os.path.exists(result_csv):
        with open(result_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if "用户主页链接" in reader.fieldnames:
                existing_links = [
                    row["用户主页链接"].strip()
                    for row in reader
                    if row["用户主页链接"].strip()
                ]
    return existing_links


def read_link_csv(keyword: str) -> List[str]:
    """读取原始用户链接（完全保留CSV中的格式）"""
    link_csv = f"douyin_link_{keyword}.csv"
    if not os.path.exists(link_csv):
        print(f"错误：链接文件 {link_csv} 不存在，请先生成！")
        return []

    with open(link_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头（假设为"用户主页链接"）
        links = [row[0].strip() for row in reader if row and row[0].strip()]
        unique_links = list(set(links))  # 去重
        print(f"成功读取 {len(unique_links)} 个不重复原始链接")
    return unique_links


def init_result_csv(keyword: str) -> None:
    """初始化结果CSV（不存在则创建表头）"""
    result_csv = f"douyin_{keyword}.csv"
    if not os.path.exists(result_csv):
        with open(result_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "用户主页链接",
                    "用户名",
                    "抖音号",
                    "IP属地",
                    "作品数量",
                    "关注数",
                    "粉丝数",
                    "获赞数",
                    "简介",
                ],
            )
            writer.writeheader()
            print(f"创建结果文件：{result_csv}")


def save_user_info(keyword: str, user_info: Dict[str, str]) -> None:
    """保存用户信息到CSV"""
    result_csv = f"douyin_{keyword}.csv"
    with open(result_csv, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "用户主页链接",
                "用户名",
                "抖音号",
                "IP属地",
                "作品数量",
                "关注数",
                "粉丝数",
                "获赞数",
                "简介",
            ],
        )
        writer.writerow(user_info)
        f.flush()  # 立即写入磁盘


def extract_user_info(page, target_url: str) -> Dict[str, str]:
    """提取用户主页信息"""
    user_info = {
        "用户主页链接": target_url,
        "用户名": "未找到用户名",
        "抖音号": "未找到抖音号",
        "IP属地": "未找到IP属地",
        "作品数量": "未找到作品数量",
        "关注数": "未找到关注数",
        "粉丝数": "未找到粉丝数",
        "获赞数": "未找到获赞数",
        "简介": "未找到简介",
    }

    try:
        # -------------------------- 修复：将locators()改为locator() --------------------------
        # 1. 关注/粉丝/获赞（div.C1cxu0Vq）
        # 用locator()配合all()获取所有匹配元素（正确语法）
        stats = page.locator("div.C1cxu0Vq").all()
        if len(stats) >= 3:
            user_info["关注数"] = (
                stats[0].text_content().strip()
                if stats[0].text_content()
                else "未找到关注数"
            )
            user_info["粉丝数"] = (
                stats[1].text_content().strip()
                if stats[1].text_content()
                else "未找到粉丝数"
            )
            user_info["获赞数"] = (
                stats[2].text_content().strip()
                if stats[2].text_content()
                else "未找到获赞数"
            )

        # 2. 用户名（第一个 span.arnSiSbK）
        username = page.locator("span.arnSiSbK").nth(0)
        if username.is_visible():
            user_info["用户名"] = (
                username.text_content().strip()
                if username.text_content()
                else "未找到用户名"
            )

        # 3. 抖音号（span.OcCvtZ2a，去除前缀）
        douyin_id = page.locator("span.OcCvtZ2a").first
        if douyin_id.is_visible():
            id_text = douyin_id.text_content()
            user_info["抖音号"] = (
                id_text.strip().replace("抖音号：", "").replace("抖音号:", "")
                if id_text
                else "未找到抖音号"
            )

        # 4. IP属地（span.DtUnx4ER，去除前缀）
        ip = page.locator("span.DtUnx4ER").first
        if ip.is_visible():
            ip_text = ip.text_content()
            user_info["IP属地"] = (
                ip_text.strip().replace("IP属地：", "").replace("IP属地:", "")
                if ip_text
                else "未找到IP属地"
            )

        # 5. 作品数量（span.MNSB3oPV）
        works = page.locator("span.MNSB3oPV").first
        if works.is_visible():
            user_info["作品数量"] = (
                works.text_content().strip()
                if works.text_content()
                else "未找到作品数量"
            )

        # 6. 简介（优先hover，其次备用元素）
        hover_bio = page.locator("div.DW9FqY4N").first
        if hover_bio.is_visible():
            hover_bio.hover()
            dynamic_p = page.wait_for_selector(
                selector="p.rOmiw4gg", state="visible", timeout=15000
            )
            user_info["简介"] = dynamic_p.text_content().strip()
        else:
            backup_bio = page.locator("span.arnSiSbK").nth(1)
            if backup_bio.is_visible():
                user_info["简介"] = (
                    backup_bio.text_content().strip()
                    if backup_bio.text_content()
                    else "未找到简介"
                )

    except Exception as e:
        print(f"  提取信息出错：{str(e)}")

    return user_info


def crawl_douyin_users(keyword: str) -> None:
    """核心爬取逻辑：读取链接→登录→循环爬取→保存结果"""
    # 1. 预处理：读取链接、初始化文件
    all_links = read_link_csv(keyword)
    if not all_links:
        return

    existing_links = load_existing_links(keyword)
    init_result_csv(keyword)
    to_crawl = [link for link in all_links if link not in existing_links]

    if not to_crawl:
        print(f"所有 {len(all_links)} 个链接已爬取完成！")
        return
    print(f"待处理链接数：{len(to_crawl)}")

    # 2. 启动浏览器
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",  # 防反爬识别
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                ],
            )
            page = browser.new_page()
            page.set_default_timeout(25000)  # 全局超时25秒

            # 3. 登录确认（访问第一个链接触发登录）
            print("\n请完成抖音登录：")
            first_link = to_crawl[0]
            page.goto(first_link, wait_until="domcontentloaded")
            input("扫码/输入账号登录后，按回车键开始爬取...")

            # 4. 循环爬取每个链接
            for idx, link in enumerate(to_crawl, 1):
                print(f"\n{'='*60}")
                print(f"处理第 {idx}/{len(to_crawl)} 个链接：{link}")

                try:
                    # 随机间隔1-3秒（防反爬）
                    time.sleep(random.uniform(1, 3))

                    # 访问链接（DOM加载完成即处理）
                    page.goto(link, wait_until="domcontentloaded")
                    time.sleep(random.uniform(2, 3))  # 等待动态内容

                    # 验证页面加载（重试机制）
                    username_loc = page.locator("span.arnSiSbK").nth(0)
                    load_success = False
                    for _ in range(2):
                        if username_loc.is_visible():
                            load_success = True
                            break
                        time.sleep(1)

                    if not load_success:
                        print("  页面加载失败，刷新后跳过...")
                        page.reload(wait_until="domcontentloaded")
                        time.sleep(2)
                        continue

                    # 提取并保存信息
                    user_info = extract_user_info(page, link)
                    save_user_info(keyword, user_info)
                    print(
                        f"  保存成功！用户名：{user_info['用户名']} | 粉丝数：{user_info['粉丝数']}"
                    )

                except PlaywrightTimeoutError:
                    print(f"  超时错误：访问 {link} 超过25秒，跳过")
                    page.reload(wait_until="domcontentloaded")
                    time.sleep(2)
                except Exception as e:
                    print(f"  处理错误：{str(e)}，跳过该链接")
                    if page.url != "https://www.douyin.com/":
                        page.goto(
                            "https://www.douyin.com/", wait_until="domcontentloaded"
                        )
                    time.sleep(2)

            # 爬取完成提示
            print(f"\n{'='*60}")
            print(f"爬取任务全部完成！")
            print(f"结果文件路径：{os.path.abspath(f'douyin_{keyword}.csv')}")

        except Exception as main_e:
            print(f"\n爬取主流程异常：{str(main_e)}")
        finally:
            input("爬取结束，按回车键关闭浏览器...")
            if browser:
                browser.close()


if __name__ == "__main__":
    keyword = input(
        "请输入搜索关键字（需与 douyin_link_XXX.csv 中的 XXX 一致）："
    ).strip()
    if not keyword:
        print("关键字不能为空！")
    else:
        crawl_douyin_users(keyword)
