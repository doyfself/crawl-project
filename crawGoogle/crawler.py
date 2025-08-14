import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import threading
import os
from urllib.parse import quote
import random

class GooglePlayCrawler:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Play应用信息爬虫")
        self.root.geometry("600x800")
        self.root.resizable(False, False)
        
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TProgressbar", thickness=25)
        
        # 创建界面元素
        self.create_widgets()
        
        # 存储爬取结果
        self.results = []
    
    def create_widgets(self):
        # 标题
        ttk.Label(self.root, text="Google Play应用信息爬虫", font=("SimHei", 14, "bold")).pack(pady=20)
        
        # 状态框
        self.status_frame = ttk.LabelFrame(self.root, text="状态", padding="10 10 10 10")
        self.status_frame.pack(fill="x", expand=False, padx=20, pady=10)
        
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        ttk.Label(self.status_frame, textvariable=self.status_var).pack(anchor="w")
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=560, mode="determinate")
        self.progress.pack(pady=10)
         
        # 日志框
        self.log_frame = ttk.LabelFrame(self.root, text="日志", padding="10 10 10 10")
        self.log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.log_text = tk.Text(self.log_frame, wrap="word", width=70, height=10)
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 按钮
        self.button_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.button_frame.pack(fill="x", expand=False)
        
        self.crawl_button = ttk.Button(self.button_frame, text="开始爬虫", command=self.start_crawling)
        self.crawl_button.pack(side="right", padx=5)
    
    def log(self, message):
        """向日志框添加消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def start_crawling(self):
        """开始爬取数据的主函数"""
        # 检查文件是否存在
        if not os.path.exists("list.xlsx"):
            messagebox.showerror("错误", "未找到list.xlsx文件，请确保文件在程序同一目录下！")
            return
        
        # 更新状态
        self.status_var.set("正在读取数据...")
        self.crawl_button.config(state="disabled")
        self.progress["value"] = 0
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行爬虫，避免界面卡顿
        threading.Thread(target=self.run_crawler, daemon=True).start()
    
    def run_crawler(self):
        try:
            # 读取Excel文件
            self.log("正在读取list.xlsx...")
            df = pd.read_excel("list.xlsx", header=None)
            
            # 获取第一列的应用名称
            app_names = df.iloc[:, 0].tolist()
            total_apps = len(app_names)
            self.log(f"找到 {total_apps} 个应用名称")
            
            # 爬取每个应用的数据
            self.results = []
            for i, app_name in enumerate(app_names, 1):
                self.status_var.set(f"正在爬取: {app_name} ({i}/{total_apps})")
                self.progress["value"] = int(i / total_apps * 100)
                
                self.log(f"正在爬取: {app_name} ({i}/{total_apps})")
                app_data = self.get_app_info(app_name)
                
                if app_data:
                    self.results.append(app_data)
                    self.log(f"成功获取: {app_name}")
                else:
                    self.log(f"获取失败: {app_name}")
                
                # 随机延时，避免被封
                delay = random.uniform(2, 5)
                self.status_var.set(f"等待中 ({delay:.1f}秒)...")
                time.sleep(delay)
            
            # 将结果写入Excel
            self.status_var.set("正在写入Excel文件...")
            print(self.results)
            self.write_to_excel(df, self.results)
            
            # 完成提示
            self.status_var.set("爬取完成！")
            self.log(f"已成功爬取 {len(self.results)} 个应用的数据")
            messagebox.showinfo("成功", f"爬取完成！共获取 {len(self.results)} 个应用的数据")
            
        except Exception as e:
            self.log(f"发生错误: {str(e)}")
            self.status_var.set("爬取失败！")
            messagebox.showerror("错误", f"爬取失败: {str(e)}")
        finally:
            self.crawl_button.config(state="normal")
    
    def get_app_info(self, app_name):
        """获取单个应用的信息"""
        self.log(f"正在获取 {app_name} 的信息...")
        
        # 检查应用名称是否为空
        if not app_name:
            self.log("应用名称为空，跳过")
            return None
        
        # 替换特殊字符
        app_name = re.sub(r"[^\w\s]", "", app_name)
        try:
            # 搜索应用
            search_url = f"https://play.google.com/store/search?q={quote(app_name)}&c=apps"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            }
            
            # 获取搜索结果页面
            search_response = requests.get(search_url, headers=headers)
            if search_response.status_code != 200:
                self.log(f"搜索请求失败，状态码: {search_response.status_code}")
                return None
            
            search_soup = BeautifulSoup(search_response.text, "html.parser")
            
            # 查找应用链接
            app_link = search_soup.select_one('a[href*="/store/apps/details?id="]')
            if not app_link:
                self.log("未找到应用链接")
                return None
            
            app_url = "https://play.google.com" + app_link["href"]
            
            # 获取应用详情页面
            app_response = requests.get(app_url, headers=headers)
            if app_response.status_code != 200:
                self.log(f"应用详情请求失败，状态码: {app_response.status_code}")
                return None
            
            app_soup = BeautifulSoup(app_response.text, "html.parser")
            
            # 提取评分
            rating = app_soup.select_one('div.fd五星评分 div.TT9eCd')
            rating = rating.text.strip() if rating else "N/A"
            
            # 提取下载数量
            downloads = app_soup.select_one('div.wVqUob span.htlgb:nth-child(2)')
            downloads = downloads.text.strip() if downloads else "N/A"
            
            # 提取评价数量
            reviews = app_soup.select_one('div.fd五星评分 a span')
            reviews = reviews.text.strip() if reviews else "N/A"
            
            # 提取应用简介 (div class="bARER")
            description = app_soup.select_one('div.bARER')
            description = description.text.strip() if description else "N/A"
            
            # 提取更新日期 (第三个 div class="xg1aie")
            update_date_elements = app_soup.select('div.xg1aie')
            update_date = update_date_elements[2].text.strip() if len(update_date_elements) >= 3 else "N/A"
            
            # 提取支持团队邮箱 (div class="pSEeg")
            support_email = "N/A"
            email_element = app_soup.select_one('div.pSEeg')
            if email_element:
                email_text = email_element.text.strip()
                email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
                email_match = re.search(email_pattern, email_text)
                support_email = email_match.group(0) if email_match else "N/A"
            
            # 提取开发者信息 (div class="HhKIQc")
            developer_info = app_soup.select_one('div.HhKIQc')
            developer_info = developer_info.text.strip() if developer_info else "N/A"
            
            # 返回结果
            return {
                "应用名称": app_name,
                "评分": rating,
                "下载数量": downloads,
                "评价数量": reviews,
                "应用简介": description,
                "更新日期": update_date,
                "支持团队邮箱": support_email,
                "开发者信息": developer_info
            }
            
        except Exception as e:
            self.log(f"获取 {app_name} 信息时出错: {str(e)}")
            return None
    def write_to_excel(self, original_df, results):
        """将爬取结果写入Excel文件"""
        # 创建结果DataFrame
        result_df = pd.DataFrame(results)
        
        # 将结果合并到原始DataFrame
        merged_df = pd.concat([original_df, result_df], axis=1)
        
        # 保存到Excel
        with pd.ExcelWriter("list.xlsx", engine="openpyxl", mode="w") as writer:
            merged_df.to_excel(writer, index=False, header=False)
        
        self.log("Excel文件写入完成")

if __name__ == "__main__":
    root = tk.Tk()
    app = GooglePlayCrawler(root)
    root.mainloop()    
