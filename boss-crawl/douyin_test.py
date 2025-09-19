from playwright.sync_api import sync_playwright
import time


def get_dynamic_text(target_url):
    with sync_playwright() as p:
        # 启动浏览器（显示界面以便手动登录）
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])

        # 创建新页面（移除timeout参数，此方法不支持）
        page = browser.new_page()
        # 可以为页面设置默认的导航超时时间
        page.set_default_navigation_timeout(30000)  # 导航超时30秒
        page.set_default_timeout(30000)  # 其他操作默认超时30秒

        try:
            # 访问目标链接
            print(f"正在打开链接：{target_url}")
            page.goto(target_url)

            # 等待用户登录确认
            input("请在浏览器中完成登录，登录成功后按【回车键】继续...")
            print("已确认登录，开始监测目标元素...")

            # 等待目标div元素出现
            target_div = page.wait_for_selector(
                selector="div.DW9FqY4N",
                state="visible",
                timeout=60000,  # 单独设置此操作的超时时间
            )
            print("已找到目标div元素，准备移动鼠标...")

            # 鼠标悬停在目标元素上
            target_div.hover()
            print("鼠标已移动到目标元素，等待动态p元素生成...")

            # 等待动态p元素出现并获取文本
            dynamic_p = page.wait_for_selector(
                selector="p.rOmiw4gg", state="visible", timeout=15000
            )

            p_text = dynamic_p.text_content().strip()
            print("\n" + "=" * 50)
            print(f"成功提取动态文本：\n{p_text}")
            print("=" * 50)

        except Exception as e:
            print(f"\n执行过程中出现错误：{str(e)}")
        finally:
            input("按【回车键】关闭浏览器...")
            browser.close()


# 目标链接
TARGET_URL = "https://www.douyin.com/user/MS4wLjABAAAA_py8TGmFe6t8KDY04LU0JH9Yr9ml54dCjRFi0mc1lwI?from_tab_name=main"

if __name__ == "__main__":
    try:
        get_dynamic_text(TARGET_URL)
    except ImportError:
        print("请先安装依赖：pip install playwright && playwright install")
