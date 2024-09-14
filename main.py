import json
import time
import os

import dashscope
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import requests

current_directory = os.path.dirname(os.path.abspath(__file__))

opt = Options()
opt.binary_location = rf'{current_directory}\Chrome\chrome.exe'
opt.add_argument('--no-sandbox')
opt.add_experimental_option('detach', True)
ser = Service()
ser.executable_path = rf'{current_directory}\Chrome\chromedriver.exe'

wjx_url = input("请输入问卷星考试链接：")
model = input("答案获取方式：1.本地ollama 2.通义千问（自行配置API）")

modelAi = ""
if model == "1":
    modelAi = "ollama"
elif model == "2":
    tongyiApi = input("请输入通义千问api token：")
    modelAi = "tongyi"
else:
    print("输入有误")
    exit(0)

browser = webdriver.Chrome(service=ser,options=opt)
browser.maximize_window()

browser.get(wjx_url)
time.sleep(2)

def ollama(text):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "gemma2:27b",
        "prompt": f"这是题目：{text} 直接返回给我答案的对应选项 不要描述其他的",
        "stream": False
    }
    response = requests.post(url, json=data)
    res = response.text
    data = json.loads(res)
    ans = data.get("response")
    return ans

def tongyi(text):
    dashscope.api_key = tongyiApi
    text = f"这是题目：{text} 直接返回给我答案的对应字母 不要描述其他的"
    messages = [{'role': 'user', 'content': text}]
    response = dashscope.Generation.call(dashscope.Generation.Models.qwen_max, messages=messages,
                                         result_format='message')
    content = response['output']['choices'][0]['message']['content']

    return content

def read_que():

    info = browser.find_elements(By.XPATH,"//div[@class='field ui-field-contain']")
    for i in info:
        # print(i.get_attribute('outerHTML'))
        que = i.find_element(By.XPATH,".//div[@class='topichtml']")
        # print(que.text)
        chose = i.find_elements(By.XPATH,".//div[@class='ui-controlgroup column1']")
        choose_info = ""
        for c in chose:
            # print(c.text)
            choose_info += c.text + "\n"
        if choose_info == "":
            print("不支持的题型！")
        else:
            label = ""
            if "对" in choose_info and "错" in choose_info and "A" not in choose_info:
                label = "判断题"
            elif "【多选题】" in que.text:
                label = "多选题"
            elif "A" in choose_info:
                label = "单选题"
            else:
                print("未知题型")
            que_all = que.text + "\n" + choose_info
            print(label)
            print(que_all)
            browser.execute_script("arguments[0].scrollIntoView();", i)
            time.sleep(1)
            if label == "单选题" or label == "多选题":
                if modelAi == "tongyi":
                    ans = tongyi(label + que_all)
                else:
                    ans = ollama(label + que_all)
                print("AI参考答案:" + ans)
                if 'A' in ans:
                    A = i.find_element(By.XPATH, ".//div[@class='ui-controlgroup column1']/div[1]/span/a")
                    A.click()

                if 'B' in ans:
                    B = i.find_element(By.XPATH, ".//div[@class='ui-controlgroup column1']/div[2]/span/a")
                    B.click()

                if 'C' in ans:
                    C = i.find_element(By.XPATH, ".//div[@class='ui-controlgroup column1']/div[3]/span/a")
                    C.click()

                if 'D' in ans:
                    D = i.find_element(By.XPATH, ".//div[@class='ui-controlgroup column1']/div[4]/span/a")
                    D.click()

                if 'A' not in ans and 'B' not in ans and 'C' not in ans and 'D' not in ans:
                    print("答案获取失败")
            elif label == "判断题":
                if modelAi == "tongyi":
                    ans = tongyi(label + que_all)
                else:
                    ans = ollama(label + que_all)
                print("AI参考答案:" + ans)
                if '对' in ans or 'A' in ans:
                    A = i.find_element(By.XPATH, ".//div[@class='ui-controlgroup column1']/div[1]/span/a")
                    A.click()

                if '错' in ans or 'B' in ans:
                    B = i.find_element(By.XPATH, ".//div[@class='ui-controlgroup column1']/div[2]/span/a")
                    B.click()

                if 'A' not in ans and 'B' not in ans and '对' not in ans and '错' not in ans:
                    print("答案获取失败")

read_que()
print("答题已完成，请手动填写不支持的题目类型")