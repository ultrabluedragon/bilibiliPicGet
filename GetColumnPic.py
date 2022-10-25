import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from lxml import etree
from tqdm import tqdm
import multitasking
import signal

path_save = 'PicSave'  # 创建空文件夹储存图片
frontName = 'https:'
if not os.path.exists(path_save):
    os.makedirs(path_save)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
    # 'cookie': '',  # 根据需要自己填写
    #  临时的cookie
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
}
# 个人请求头
requests.packages.urllib3.disable_warnings()  # 忽视警告

urlUp = input('输入专栏url')

chrome_options = Options()
# argument = '--user-data-dir=（这里要填写自己的路径）\\Google\\Chrome\\User Data'  # 调用本机浏览器设定
# chrome_options.add_argument(argument)  # 可以参考https://www.jianshu.com/p/32ed00caf22b
driver_chrome = webdriver.Chrome(chrome_options=chrome_options)
driver_chrome.get(urlUp)

dom01 = etree.HTML(driver_chrome.page_source)
linkList = []

for _ in tqdm(range(  # 先抓取所有专栏的url，并且保存在linkList
        int(
            re.findall(
                '(\\d+)', dom01.xpath('//*[@class="be-pager-total"]/text()')[0]
            )[0]) - 1)):
    dom02 = etree.HTML(driver_chrome.page_source)
    link = [_[2:] for _ in set(dom02.xpath('//*[@class="article-item clearfix"]//a/@href'))]
    linkList += link

    next_page = driver_chrome.find_element(
        By.CSS_SELECTOR,
        '#page-article > div > div.main-content > ul > li.be-pager-next > a')
    driver_chrome.execute_script('arguments[0].click()', next_page)
    time.sleep(5)

dom03 = etree.HTML(driver_chrome.page_source)
link = [frontName + http for http in set(dom03.xpath('//*[@class="article-item clearfix"]//a/@href'))]
linkList += link
driver_chrome.close()

picList = []
for Column in tqdm(linkList):  # 爬取所有专栏中图片的Url并且保存在picList中
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'
    # }
    if 'http' not in Column:
        response = requests.get('https://' + Column, headers=headers)
        dom04 = etree.HTML(response.text)
        picLink = []
        for perLink in dom04.xpath('//*[@id="read-article-holder"]//img/@data-src'):  # 判断是否已经有http头，没有就加上去
            if 'http' in perLink:
                picLink.append(perLink)
            else:
                picLink.append(frontName + perLink)
        picList += picLink
    else:
        response = requests.get('https://' + Column, headers=headers)
        dom05 = etree.HTML(response.text)
        picLink = []
        for perLink in dom05.xpath('//*[@id="read-article-holder"]//img/@data-src'):
            if 'http' in perLink:
                picLink.append(perLink)
            else:
                picLink.append(frontName + perLink)
        picList += picLink


@multitasking.task
def download(url: str, file_name: str) -> None:  # 定义多线程下载器
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'
    # }

    Pic = requests.get(url, headers=headers, stream=True)
    # 一块文件的大小
    chunk_size = 1024
    with open(os.path.join(path_save, file_name), mode='wb') as f:
        # 写入分块文件
        for chunk in Pic.iter_content(chunk_size=chunk_size):
            f.write(chunk)


def pythonDownloadLauncher(urlList: list) -> None:  # 传入图片url列表，调用多线程下载器，保存在Picsave文件夹中
    signal.signal(signal.SIGINT, multitasking.killall)

    start_time = time.time()
    for perPic in tqdm(range(1, len(urlList))):
        download(url=urlList[perPic], file_name=f'{perPic}.jpg')  # 循环调用多线程下载器
        if perPic % 5 == 0:
            multitasking.wait_for_tasks()
        multitasking.wait_for_tasks()

    end_time = time.time()
    print(f'耗时:{int((end_time - start_time) // 60)}分:{int((end_time - start_time) % 60)}秒')
    print('下载结束，图片已经保存在PicSave文件夹中')


if __name__ == '__main__':
    pythonDownloadLauncher(urlList=picList)
