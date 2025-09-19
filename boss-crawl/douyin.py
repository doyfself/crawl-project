import csv
import time
import random
import os
import asyncio
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


async def main():
    # 1. 获取用户输入的搜索关键字，定义CSV文件名
    keyword = input("请输入搜索关键字: ")
    csv_filename = f"douyin_link_{keyword}.csv"

    # 2. 检查CSV文件，初始化断点续爬和去重配置
    start_index = 0
    existing_links = set()
    if os.path.exists(csv_filename):
        with open(csv_filename, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if row and row[0].strip():
                    existing_links.add(row[0].strip())
            start_index = len(existing_links)
            print(
                f"检测到已有数据，已爬取 {start_index} 个用户链接，将从第 {start_index + 1} 个链接开始爬取"
            )

    # 3. 启动Playwright浏览器
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 4. 访问抖音用户搜索页（仅跳转，不立即滚动）
            search_url = f"https://www.douyin.com/root/search/{keyword}?type=user"
            print(f"\n正在访问搜索页：{search_url}")
            await page.goto(
                search_url, wait_until="domcontentloaded", timeout=30000
            )  # 等待DOM加载完成即可，不等待网络空闲
            print("搜索页已跳转完成，请确认页面正常加载（若需登录可先准备）")

            # -------------------------- 新增：等待用户回车确认后再滚动 --------------------------
            input(
                "请确认页面状态（如登录准备、页面加载），确认完成后按回车键开始滚动加载..."
            )
            # ----------------------------------------------------------------------------------

            # 5. 等待用户手动登录（若未登录，此时用户可在浏览器中扫码/输入账号登录）
            input(
                "请在浏览器中完成抖音登录（若已登录可直接按回车），登录后按回车键继续..."
            )

            # 6. 开始滚动页面加载所有用户卡片
            print("\n开始滚动页面，加载所有用户卡片...")
            last_height = await page.evaluate("document.body.scrollHeight")
            scroll_count = 0
            max_scroll_attempts = 10

            while scroll_count < max_scroll_attempts:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                sleep_time = random.uniform(2, 5)
                print(
                    f"第 {scroll_count + 1} 次滚动后，等待 {sleep_time:.2f} 秒加载内容"
                )
                await asyncio.sleep(sleep_time)

                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    print(f"页面已滚动到底部，共加载 {scroll_count + 1} 次，停止滚动")
                    break
                last_height = new_height
                scroll_count += 1
            else:
                print(f"已达到最大滚动尝试次数（{max_scroll_attempts}次），停止滚动")

            # 7. 提取用户卡片链接并写入CSV
            print("\n开始提取用户链接...")
            try:
                await page.wait_for_selector(
                    "div.search-result-card > a", timeout=15000
                )
                card_links = await page.locator("div.search-result-card > a").all()
                total_links = len(card_links)
                print(f"成功定位到 {total_links} 个用户卡片链接")

                if total_links == 0:
                    print("未找到任何用户卡片链接，可能是页面结构变化或未加载成功")
                    return

            except PlaywrightTimeoutError:
                print("超时：未找到用户卡片链接，可能是选择器失效或页面未加载")
                await browser.close()
                return
            except Exception as e:
                print(f"定位用户卡片时出错：{str(e)}")
                await browser.close()
                return

            # 写入CSV（含去重和断点续爬）
            with open(csv_filename, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if start_index == 0:
                    writer.writerow(["用户主页链接"])

                new_link_count = 0
                for i in range(start_index, total_links):
                    try:
                        link = await card_links[i].get_attribute("href")
                        if not link:
                            print(f"第 {i + 1} 个卡片：未获取到有效href，跳过")
                            continue

                        link = link.strip()

                        if link in existing_links:
                            print(f"第 {i + 1} 个卡片：链接已存在（{link}），跳过")
                            continue

                        writer.writerow([link])
                        existing_links.add(link)
                        new_link_count += 1
                        print(f"已提取第 {i + 1}/{total_links} 个链接：{link}")

                    except Exception as e:
                        print(f"处理第 {i + 1} 个卡片链接时出错：{str(e)}，跳过该链接")
                        continue

                print(f"\n爬取完成！本次共新增 {new_link_count} 个用户链接")
                print(f"所有链接已保存至：{os.path.abspath(csv_filename)}")
                print(f"累计爬取 {len(existing_links)} 个不重复的用户链接")

        except Exception as main_e:
            print(f"程序主流程出错：{str(main_e)}")
        finally:
            await browser.close()
            print("\n浏览器已关闭")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
