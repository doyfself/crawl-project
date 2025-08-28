import time
import random
import csv
import os
from datetime import datetime
from playwright.sync_api import sync_playwright


def init_csv(keyword):
    """初始化CSV文件并写入表头（包含主页链接字段）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kuaishou_authors_{keyword}_{timestamp}.csv"
    # 新增"主页链接"字段
    headers = ["序号", "名字", "作品数", "粉丝数", "关注数", "简介", "主页链接"]

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

    # 初始化CSV文件
    csv_filename = init_csv(search_keyword)
    authors_data = []
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
                time.sleep(random.uniform(2, 3))

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

            # 从起始序号开始遍历
            for index in range(start_index - 1, total):
                current_card_index = index + 1
                card = card_items[index]
                try:
                    print(f"\n处理第{current_card_index}/{total}个作者...")
                    time.sleep(random.uniform(1, 2))

                    # 点击卡片前先获取链接（如果卡片本身是a标签）
                    # 方法1: 尝试直接获取卡片的href属性
                    author_url = ""
                    try:
                        # 检查卡片是否包含链接或自身是链接
                        if card.locator("a").count() > 0:
                            author_url = card.locator("a").first.get_attribute("href")
                        else:
                            # 如果卡片本身不是链接，尝试通过点击后获取新页面URL
                            pass
                    except Exception as e:
                        print(f"提前获取链接失败: {str(e)}，将在页面打开后获取")

                    # 点击卡片打开新页面
                    with page.expect_popup() as popup_info:
                        card.click()
                    author_page = popup_info.value

                    # 方法2: 从新页面获取URL（更可靠）
                    author_url = author_page.url  # 获取当前页面的完整URL
                    print(f"获取到主页链接: {author_url}")

                    author_page.wait_for_selector("div.user-detail", timeout=10000)
                    print("作者页面加载完成，开始读取信息...")
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

                    # 构建数据（包含主页链接）
                    item_data = {
                        "序号": current_card_index,
                        "名字": name,
                        "作品数": works,
                        "粉丝数": fans,
                        "关注数": follows,
                        "简介": desc,
                        "主页链接": author_url,  # 新增主页链接字段
                    }
                    authors_data.append(item_data)

                    # 实时保存
                    save_to_csv_realtime(item_data, csv_filename)

                    # 打印结果
                    print(f"【名字】: {name}")
                    print(f"【作品】: {works} | 【粉丝】: {fans} | 【关注】: {follows}")
                    print(f"【简介】: {desc}")
                    print(f"【主页链接】: {author_url}")

                    time.sleep(random.uniform(2, 3))
                    author_page.close()

                except Exception as e:
                    print(f"处理第{current_card_index}个卡片时出错: {str(e)}")
                    try:
                        author_page.close()
                    except:
                        pass
                    continue

            print(
                f"\n所有操作完成！共提取{len(authors_data)}条有效数据，已实时保存到 {csv_filename}"
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
