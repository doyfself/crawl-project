import csv
import re
import time
from playwright.sync_api import sync_playwright

def parse_intro(intro_text):
    """解析简介文本，提取粉丝数量、视频数量和用户简介"""
    if not intro_text:
        return "", "", ""
    
    # 去除回车和空格
    intro_text = intro_text.replace('\n', '').replace(' ', '')
    
    # 正则表达式，匹配粉丝和视频数量（保留单位）
    pattern = r'(\d+(?:\.\d+)?)(万|亿)?粉丝·(\d+(?:\.\d+)?)(万|亿)?个视频'
    match = re.search(pattern, intro_text)
    
    if match:
        # 提取粉丝数量（保留单位）
        fans_num = match.group(1)
        fans_unit = match.group(2) or ""
        fans = f"{fans_num}{fans_unit}"
        
        # 提取视频数量（保留单位）
        videos_num = match.group(3)
        videos_unit = match.group(4) or ""
        videos = f"{videos_num}{videos_unit}"
        
        # 提取简介部分
        desc_start = match.end()
        description = intro_text[desc_start:] if desc_start < len(intro_text) else ""
        
        return fans, videos, description
    else:
        # 如果没有匹配到粉丝和视频信息，整个文本作为简介
        return "", "", intro_text

def main():
    # 创建CSV文件并设置表头
    with open('bilibili.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['用户名', '粉丝数量', '视频数量', '用户简介','主页链接']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 启动浏览器
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # 打开目标网站（请替换为实际URL）
            page.goto("https://search.bilibili.com/upuser?keyword=%E8%AF%B4%E5%BD%B1&from_source=webtop_search&spm_id_from=333.1007&search_source=5")
            
            # 等待页面加载完成
            page.wait_for_selector('div.user-content.pr_md')
            
            while True:
                # 等待用户名和简介元素加载完成
                page.wait_for_selector('div.user-content.pr_md .text1.p_relative')
                page.wait_for_selector('div.user-content.pr_md .b_text.fs_5.text2.text_ellipsis')
                
                # 提取所有用户信息
                user_elements = page.query_selector_all('div.user-content.pr_md')
                
                for user in user_elements:
                    # 提取用户名
                    username_element = user.query_selector('.text1.p_relative')
                    username = username_element.get_attribute('title') if username_element else ''

                    # 提取主页链接
                    homepage_link = username_element.get_attribute('href') if username_element else ''
                    
                    # 提取简介
                    intro_element = user.query_selector('.b_text.fs_5.text2.text_ellipsis')
                    intro_text = intro_element.get_attribute('title') if intro_element else ''
                    
                    # 解析简介
                    fans, videos, description = parse_intro(intro_text)
                    
                    # 写入CSV文件
                    writer.writerow({
                        '用户名': username,
                        '粉丝数量': fans,
                        '视频数量': videos,
                        '用户简介': description,
                        '主页链接': homepage_link
                    })
                    print(f"已爬取: {username} - {fans}粉丝 · {videos}个视频 · {description[:30]}...")
                
                # 查找按钮文本为"下一页"且没有disabled属性的按钮
                next_buttons = page.query_selector_all('button')
                next_button = None
                
                for button in next_buttons:
                    if button.inner_text().strip() == "下一页" and not button.get_attribute('disabled'):
                        next_button = button
                        break
                
                # 判断是否找到可点击的下一页按钮
                if next_button:
                    # 滚动到下一页按钮
                    next_button.scroll_into_view_if_needed()
                    
                    # 点击下一页
                    next_button.click()
                    
                    print("已点击下一页，等待2秒...")
                    time.sleep(2)  # 等待2秒，确保页面完全加载
                    
                    # 等待页面加载新内容
                    page.wait_for_load_state('networkidle')
                    print("页面加载完成，继续爬取")
                else:
                    print("已到达最后一页，爬取完成")
                    break
            
            # 关闭浏览器
            browser.close()

if __name__ == "__main__":
    main()