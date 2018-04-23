# encoding: UTF-8
import os,urllib2,urllib  
import multiprocessing
from multiprocessing import freeze_support
from utils import *

currentP = 0

#设置下载后存放的存储路径'C:\Users\yinyao\Desktop\Python code'    
path=r'.\historyData'    
  
#设置下载链接的路径 
#baseurl="http://120.136.172.92:52300/dclevel2/{}/{}/"  
#baseurl="http://120.136.172.92:52300/es/{}/{}/"  
#baseurl="http://120.136.172.92:52300/szse/{}/{}/"  
baseurl="http://120.136.172.92:52300/sse/{}/{}/"  
#baseurl="http://120.136.172.92:52300/shfe/{}/{}/"  

  
#定义下载函数downLoadPicFromURL（本地文件夹，网页URL）  
def downLoadCSVFromURL(dest_dir,URL):  
    try:  
        #urllib.urlretrieve(URL , dest_dir)  
        with open(dest_dir,'wc') as f:
            f.write(getHTML(URL).read())
        return dest_dir
    except Exception, e:
        print(u'出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()

def downSymbolLevel2(symbol,year,month):
    global currentP 
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    urls = []
    files = []
    URL = baseurl.format(year,month)
    html = getHTML(URL)
    soup = BeautifulSoup(html, 'html.parser')
    #soup = get_page(URL)
    links = soup.find_all('a')
    for link in links:
        file_name = link.get_text()[1:]
        if symbol+'_' == file_name[0:len(symbol)+1]:
            url = URL+file_name
            dest_dir=os.path.join(path,file_name)
            urls.append(url)
            print u'开始下载 : '+url
            files.append(dest_dir)
    l = []
    currentP=0
    #----------------------------------------------------------------------
    def showProcessBar(result):
        """显示进度条"""
        global currentP 
        currentP+=1
        print(result+u' 下载完成!')
    for url,filename in zip(urls,files):
        l.append(pool.apply_async(downLoadCSVFromURL, args=(filename,url,), callback=showProcessBar))
    pool.close()
    pool.join()
  
#运行  
if __name__ == '__main__':
    freeze_support()
    symbols = ['600547']
    months = ['04','05','06','07','08','09']
    for symbol in symbols:
        for month in months:
            downSymbolLevel2(symbol,'2017',month)
#downLoadPicFromURL(dest_dir,url)  

