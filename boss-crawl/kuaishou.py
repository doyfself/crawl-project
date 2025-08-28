import time
import random
import csv
import os
from datetime import datetime
from playwright.sync_api import sync_playwright


def init_csv(keyword):
    """初始化CSV文件并写入表头（仅首次创建时调用）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kuaishou_authors_{keyword}_{timestamp}.csv"
    headers = ["序号", "名字", "作品数", "粉丝数", "关注数", "简介"]

    # 若文件不存在则创建并写入表头
    if not os.path.exists(filename):
        with open(filename, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
    return filename


def save_to_csv_realtime(data, filename):
    """实时追加单条数据到CSV文件"""
    try:
        with open(filename, mode="a", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            writer.writerow(data)
        print(f"已实时保存第{data['序号']}条数据到 {filename}")
    except Exception as e:
        print(f"实时保存数据失败: {str(e)}")


def main():
    # 输入关键词和起始序列
    search_keyword = input("请输入搜索关键词: ").strip()
    if not search_keyword:
        print("关键词不能为空！")
        return

    try:
        start_index = input("请输入起始序号（从1开始，默认1）: ").strip()
        start_index = int(start_index) if start_index else 1
        if start_index < 1:
            print("起始序号不能小于1，已自动调整为1")
            start_index = 1
    except ValueError:
        print("输入的起始序号无效，已自动调整为1")
        start_index = 1

    # 初始化CSV文件，获取文件名
    csv_filename = init_csv(search_keyword)
    authors_data = []  # 保留内存数据用于统计
    search_url = f"https://www.kuaishou.com/search/author?searchKey={search_keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            page.goto(search_url, wait_until="networkidle")
            print(f"已访问搜索页：{search_url}")

            input("请在浏览器中完成登录，登录后按回车键继续...")

            print("开始滚动加载内容...")
            loading_selector = "div.spinning.search-loading div.text"
            scroll_attempts = 0
            max_attempts = 5

            while scroll_attempts < max_attempts:
                scroll_distance = random.randint(500, 800)
                page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                time.sleep(random.uniform(2, 3))  # 延长滚动等待

                try:
                    page.wait_for_selector(loading_selector, timeout=1000)
                    print(f"检测到加载状态，尝试次数：{scroll_attempts + 1}")
                    scroll_attempts += 1
                except:
                    scroll_attempts = 0

            print("已加载所有内容，停止滚动")

            # 获取所有作者卡片
            card_items = page.locator("div.card-item").all()
            total = len(card_items)
            print(f"共找到{total}个作者卡片，从第{start_index}个开始提取...")

            # 从起始序号开始遍历（注意：列表索引从0开始，需-1转换）
            for index in range(start_index - 1, total):
                current_card_index = index + 1  # 显示的序号（1-based）
                card = card_items[index]
                try:
                    print(f"\n处理第{current_card_index}/{total}个作者...")
                    # 延长点击前等待：1-2秒
                    time.sleep(random.uniform(1, 2))

                    with page.expect_popup() as popup_info:
                        card.click()
                    author_page = popup_info.value

                    author_page.wait_for_selector("div.user-detail", timeout=10000)
                    print("作者页面加载完成，开始读取信息...")
                    # 延长页面加载后等待：2-3秒
                    time.sleep(random.uniform(2, 3))

                    # 提取信息
                    name = (
                        author_page.locator(
                            "div.profile-area p.user-name span"
                        ).text_content()
                        or "未获取到"
                    )
                    name = name.strip()

                    info_h3s = author_page.locator("div.user-detail-info h3").all()
                    works = (
                        info_h3s[0].text_content().strip()
                        if len(info_h3s) >= 1
                        else "0"
                    )
                    fans = (
                        info_h3s[1].text_content().strip()
                        if len(info_h3s) >= 2
                        else "0"
                    )
                    follows = (
                        info_h3s[2].text_content().strip()
                        if len(info_h3s) >= 3
                        else "0"
                    )

                    desc = author_page.locator("p.user-desc").text_content() or "无简介"
                    desc = desc.strip().replace("\n", " ")

                    # 构建单条数据
                    item_data = {
                        "序号": current_card_index,
                        "名字": name,
                        "作品数": works,
                        "粉丝数": fans,
                        "关注数": follows,
                        "简介": desc,
                    }
                    authors_data.append(item_data)

                    # 实时保存到CSV
                    save_to_csv_realtime(item_data, csv_filename)

                    # 打印提取结果
                    print(f"【名字】: {name}")
                    print(f"【作品】: {works} | 【粉丝】: {fans} | 【关注】: {follows}")
                    print(f"【简介】: {desc}")

                    # 延长关闭标签页前等待：2-3秒
                    time.sleep(random.uniform(2, 3))
                    author_page.close()

                except Exception as e:
                    print(f"处理第{current_card_index}个卡片时出错: {str(e)}")
                    try:
                        author_page.close()
                    except:
                        pass
                    continue

            # 最终统计
            print(
                f"\n所有操作完成！共提取{len(authors_data)}条有效数据，已实时保存到 {csv_filename}"
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
