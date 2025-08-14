from playwright.sync_api import sync_playwright
import csv
import time
import random
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page_total = 50  # 假设总页数为50
    cur_page = 1  # 当前页数从1开始
    page_size = 10  # 每页10条数据
    username = "18219514598"
    password = "246587"

    # 计算CSV文件已有行数（已爬取数量）
    csv_path = 'mcn.csv'
    start_index = 0
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            existing_rows = sum(1 for row in reader)  # 计算行数
            start_index = existing_rows - 1  # 减去表头行
            print(f"发现已有 {start_index} 条数据，将从第 {start_index+1} 条开始爬取")
            cur_page = start_index // page_size + 1  
            start_index = start_index % page_size 
    else:
        # 创建CSV文件并写入表头
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['综合']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    # 全局变量存储所有新打开的窗口
    new_windows = []
    
    # 1. 访问初始链接
    page.goto("http://121.4.63.28/front/main")
    page.wait_for_load_state("load")
    print("已打开初始页面")

    # 2. 输入手机号和密码
    try:
        phone_input = page.locator('input[placeholder="手机号"]')
        phone_input.wait_for(timeout=10000)
        phone_input.fill(username)
        
        pwd_input = page.locator('input[placeholder="密码"]')
        pwd_input.wait_for(timeout=10000)
        pwd_input.fill(password)
        print("已输入登录信息")
        login_btn = page.locator('.login-btn')  # 定位ID为loginbtn的按钮
        login_btn.click()
    except Exception as e:
        print(f"输入登录信息失败：{e}")
        browser.close()
        exit()

    # 3. 等待10秒
    print("等待10秒...")
    time.sleep(3)

    # 4. 点击第一个按钮
    # try:
    #     fg_button = page.locator('button:has-text("飞瓜入口")')
    #     fg_button.wait_for(state="visible", timeout=5000)
    #     fg_button.click()
    # except Exception as e:
    #     browser.close()
    #     exit()

    # 5. 处理iframe内按钮
    # try:
    #     # 定位iframe（支持动态名称）
    #     target_iframe = None
    #     for frame in page.frames:
    #         if frame.name and "layui-layer-iframe1" in frame.name:
    #             target_iframe = page.frame_locator(f'iframe[name="{frame.name}"]')
    #             print(f"使用iframe：{frame.name}")
    #             break
    #     if not target_iframe:
    #         target_iframe = page.frame_locator("iframe").nth(0)
    #         print("使用第一个iframe（通过索引）")

    #     # 选择第一个匹配按钮
    #     all_buttons = target_iframe.locator(".layui-btn.layui-btn-danger.layui-btn-small")
    #     target_btn = all_buttons.nth(0)
        
    #     # 等待并点击目标按钮
    #     target_btn.wait_for(state="visible", timeout=10000)
    #     with context.expect_page() as new_page_info:
    #         target_btn.click()
    #     new_page = new_page_info.value
    #     new_page.wait_for_load_state("load")
    #     new_windows.append(new_page)  # 添加到全局新窗口列表
    #     print(f"成功捕获新标签页: {new_page.url}")

    # except Exception as e:
    #     print(f"点击iframe内按钮失败：{e}")
    #     browser.close()
    #     exit()
    
    jump_button = page.locator(".fg-btn.fgdy-btn-succ")
    with context.expect_page() as new_page_info:
        jump_button.click()
    new_page = new_page_info.value
    new_page.wait_for_load_state("load")
    new_windows.append(new_page)  # 添加到全局新窗口列表


    # 6. 等待并切换到新窗口（使用全局监听的窗口）
    try:
        # 等待新窗口打开（超时设置为15秒）
        start_time = time.time()
        while time.time() - start_time < 15:
            if new_windows:
                new_window = new_windows[-1]  # 获取最新打开的窗口
                new_window.bring_to_front()
                new_window.wait_for_load_state("load")
                print(f"已切换到新窗口，URL：{new_window.url}")
                break
            time.sleep(1)
        else:
            print("错误：未检测到新窗口打开")
            # 调试：打印所有已知窗口
            print(f"当前已知窗口数量：{len(context.pages)}")
            for i, p in enumerate(context.pages):
                print(f"窗口 {i+1}: {p.url}")
            browser.close()
            exit()

    except Exception as e:
        print(f"切换到新窗口失败：{e}")
        browser.close()
        exit()

    # 7. 点击"MCN库"
    try:
        talent_element = new_window.locator('[title="达人"]')
        talent_element.hover()
        mcn_div = new_window.locator('div.child-label:has-text("MCN库")')
        mcn_div.wait_for(timeout=10000)
        mcn_div.click()
        # 移除hover状态
        talent_element.hover()  # 再次hover以移除hover状态
    
    except Exception as e:
        print(f"点击'MCN库'失败：{e}")
        browser.close()
        exit()

    time.sleep(5)

    # 8. 点击"影视娱乐"
    # try:
    #     movie_span = new_window.locator('div.skeleton-content span:has-text("影视娱乐")')
    #     movie_span.wait_for(timeout=10000)
    #     movie_span.click()
    #     print("已点击'影视娱乐'")
    # except Exception as e:
    #     print(f"点击'影视娱乐'失败：{e}")
    #     browser.close()
    #     exit()

    # time.sleep(1)

    def jump_to_page(new_window, start_page):
        try:
            page_input = new_window.locator('div.is-in-pagination input')
            page_input.wait_for(state="visible")
            
            # 清空输入框并输入目标页码
            page_input.click()
            page_input.fill("")  # 清空现有内容
            page_input.type(str(start_page))  # 输入目标页码
            print(f"跳转到第 {start_page} 页")
            
            # 模拟按下回车键
            page_input.press("Enter")
            time.sleep(3)
            get_user_info(new_window)# 等待跳转完成
        
        except Exception as e:
            print(f"翻页失败: {e}")

    def get_user_info(new_window, first_run=False):
        global cur_page
        global start_index
        
        # 6. 循环点击每个用户信息，处理新页签
        for i in range(page_size):
            if i < start_index and  not first_run:
                print(f"跳过已处理的用户 {i+1}（索引：{start_index}）")
                continue
            
            # 重新定位元素（避免DOM刷新导致的失效）
            current_user = new_window.locator(".mcn-name").nth(i)
            
            # 点击用户信息并等待新页签
            with context.expect_page() as profile_page_info:
                current_user.click()
                print(f"已点击用户信息，等待新页签打开...")
            
            profile_page = profile_page_info.value
            profile_page.wait_for_load_state("load")
            print(f"新页签已打开：{profile_page.url}")
            
            # 7. 在新页签中提取数据
            try:
                random_sleep = random.uniform(10, 20)
                time.sleep(random_sleep)  # 等待页面加载
                top_wrapper = profile_page.locator(".mcn-top-wrapper").nth(0)
                full_text = top_wrapper.text_content()  # 返回所有文本，按DOM顺序拼接

                # 分割并清理文本
                all_texts = [line.strip() for line in full_text.splitlines() if line.strip()]
                
                # 8. 写入CSV文件
                with open(csv_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['综合']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({
                        '综合': all_texts[0] if all_texts else '无文本'
                    })
                    
            except Exception as e:
                print(f"提取数据失败：{e}")
            
            # 8. 关闭当前页签并切换回主页面
            profile_page.close()
            print(f"已关闭用户 {i+1} 的页签")
            new_window.bring_to_front()  # 切换回主页面
            time.sleep(random.uniform(2, 5))  # 等待2-5秒，避免操作过快
            
        # 可选：添加间隔时间避免操作过快
        time.sleep(random.uniform(60, 120))

        start_index = 0  # 重置起始索引
        cur_page += 1
        jump_to_page(new_window, cur_page)  # 跳转到指定页数

        
    if cur_page > 1:
        jump_to_page(new_window, cur_page)
    else:
        get_user_info(new_window, True)
    browser.close()