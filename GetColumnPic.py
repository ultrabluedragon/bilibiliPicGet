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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    'cookie': '''buvid3=27004B18-7172-495A-AFBE-E6C92713AE6952850infoc; nostalgia_conf=-1; i-wanna-go-back=-1; _uuid=DB9B2EDE-281E-5F47-84FA-AFB71E44B27A98989infoc; buvid4=CE565E95-91C0-17C5-223E-5684966AEA6B05490-022073009-DsswV1JjVn6NEkwBvys0Ww%3D%3D; CURRENT_BLACKGAP=0; theme_style=light; blackside_state=0; rpdid=|(u|JkYJk|ml0J'uYlmuRJmkk; LIVE_BUVID=AUTO9716591487303688; is-2022-channel=1; buvid_fp_plain=undefined; DedeUserID=487364686; DedeUserID__ckMd5=3f86b8024e83e23c; b_ut=5; hit-dyn-v2=1; b_timer=%7B%22ffp%22%3A%7B%22333.1007.fp.risk_27004B18%22%3A%22182AB31FDCF%22%2C%22333.337.fp.risk_27004B18%22%3A%22182AB32280F%22%2C%22333.788.fp.risk_27004B18%22%3A%22182CD73A2CD%22%2C%22333.976.fp.risk_27004B18%22%3A%22182D2AE857E%22%2C%22333.42.fp.risk_27004B18%22%3A%2218270F0BD3D%22%2C%22333.999.fp.risk_27004B18%22%3A%2218294D38D2A%22%2C%22333.1193.fp.risk_27004B18%22%3A%22182D2AE8CF6%22%2C%22444.42.fp.risk_27004B18%22%3A%2218294D4644C%22%2C%22888.55048.fp.risk_27004B18%22%3A%22182A4840091%22%7D%7D; b_nut=100; SL_GWPT_Show_Hide_tmp=1; SL_wptGlobTipTmp=1; fingerprint=859da9024250f5f73dec44b9076074b6; buvid_fp=ffe9a05b87c220ddc3806b90f86bfdd4; bp_video_offset_487364686=713351977374842900; SL_G_WPT_TO=zh-CN; CURRENT_QUALITY=0; CURRENT_FNVAL=4048; bsource=search_baidu; SESSDATA=55d52f14%2C1681812546%2Cdcc4d%2Aa2; bili_jct=88f34688793f8fdb70fdb3ec168337b0; sid=g68z1wcy; b_lsid=5F918A6A_183F984B4E7; PVID=2; innersign=0''',
    #  临时的cookie
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
}
# 个人请求头
requests.packages.urllib3.disable_warnings()  # 忽视警告

urlUp = input('输入专栏url')

chrome_options = Options()
argument = '--user-data-dir=C:\\Users\\45007\\AppData\\Local\\Google\\Chrome\\User Data'
chrome_options.add_argument(argument)
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
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
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
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
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
