import os
import json
from playwright.sync_api import sync_playwright

# 创建临时目录存放浏览器扩展
extension_dir = "temp_extension"
os.makedirs(extension_dir, exist_ok=True)

# 创建扩展的 manifest.json
manifest = {
    "manifest_version": 3,
    "name": "Tab Tracker",
    "version": "1.0",
    "permissions": ["tabs", "activeTab", "scripting"],
    "background": {
        "service_worker": "background.js"
    }
}

with open(f"{extension_dir}/manifest.json", "w") as f:
    json.dump(manifest, f)

# 创建扩展的后台脚本
background_js = """
// 监听所有标签页的创建
chrome.tabs.onCreated.addListener(tab => {
    console.log('[Tab Tracker] 新标签页创建:', tab.id, tab.url);
});

// 监听标签页 URL 变化
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.url) {
        console.log('[Tab Tracker] 标签页 URL 更新:', tabId, changeInfo.url);
    }
});

// 将标签页信息发送到控制台
function sendTabInfo() {
    chrome.tabs.query({}, tabs => {
        console.log('[Tab Tracker] 当前所有标签页:', JSON.stringify(
            tabs.map(t => ({id: t.id, url: t.url}))
        ));
    });
}

// 监听来自内容脚本的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message === "get_tabs") {
        sendTabInfo();
        sendResponse({status: "tabs_sent"});
    }
    return true;
});
"""

with open(f"{extension_dir}/background.js", "w") as f:
    f.write(background_js)

# 使用 Playwright 启动浏览器并加载扩展
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            f"--disable-extensions-except={extension_dir}",
            f"--load-extension={extension_dir}"
        ]
    )
    context = browser.new_context()
    page = context.new_page()
    
    # 打开百度
    page.goto("https://www.baidu.com")
    print("已打开百度，请在浏览器中自由打开新标签页")
    
    # 等待用户输入 start
    input("所有标签页加载完成后，输入 'start' 并回车：")
    
    # 执行 JavaScript 代码获取所有标签页信息
    print("正在获取所有标签页信息...")
    
    # 注入脚本获取标签页信息
    page.evaluate("""
        // 向扩展发送消息请求标签页信息
        chrome.runtime.sendMessage("get_tabs", response => {
            console.log('[Playwright] 收到标签页信息:', response);
        });
    """)
    
    # 从浏览器控制台捕获标签页信息
    tab_info = None
    def handle_console(msg):
        nonlocal tab_info
        if "[Tab Tracker] 当前所有标签页:" in msg.text:
            # 提取 JSON 部分
            json_str = msg.text.split(":", 1)[1].strip()
            tab_info = json.loads(json_str)
    
    page.on("console", handle_console)
    
    # 等待一段时间获取控制台输出
    time.sleep(2)
    
    # 打印所有标签页信息
    print("\n当前所有标签页的链接（包括手动打开的）：")
    if tab_info:
        for i, tab in enumerate(tab_info):
            print(f"标签页 {i+1}: {tab['url']}")
    else:
        print("未获取到标签页信息，请确保扩展已正确加载")
    
    input("按回车关闭浏览器...")
    browser.close()