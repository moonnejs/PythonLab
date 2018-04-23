# encoding: UTF-8
import requests
import lxml
import time
from bs4 import BeautifulSoup
import time  
import sys  
import gzip  
import socket  
import urllib2

user = 'admin'
password = 'Qxy475'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8'
}

header = {
    'Connection' : 'keep-alive',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
    'Accept-Language' : 'en-US,en;q=0.5',
    'Accept-Encoding' : 'gzip, deflate'
}


def get_page(url):
    r = requests.get(url, headers=headers)
    try:
        soup = BeautifulSoup(r.content.decode("utf-8"), 'lxml')
    except UnicodeDecodeError:
        soup = BeautifulSoup(str(r.content,encoding="gbk"), 'lxml')
    return soup

def getHTML(URL):
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, URL, user, password)
    handler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    html = urllib2.urlopen(urllib2.Request(URL, None, header))
    return html
