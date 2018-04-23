# encoding: UTF-8

'''
在本文件中引入所有希望在系统中使用的策略类

这个字典中保存了需要运行的策略的名称和策略类的映射关系，
用户的策略类写好后，先在该文件中引入，并设置好名称，然后
在CTA_setting.json中写入具体每个策略对象的类和合约设置。
'''
import os
import sys
import re
import imp
import glob
import talib
sys.path.append('./strategy')
allfile=[]
def getallfile(path):
    allfilelist=os.listdir(path)
    for f in allfilelist:
        filepath=os.path.join(path,f)
        #判断是不是文件夹
        if os.path.isdir(filepath):
            getallfile(filepath)
        allfile.append(filepath)
    return allfile

pattern = re.compile(r"[^\s]*.py$")
# 导入所有策略
ALL_STRATEGIES = []
strategyPath = os.getcwd() + '/strategy/'
#allPath = glob.glob(strategyPath+r'*.py')
allPath = getallfile(strategyPath)
for path in allPath:
    if pattern.match(path):
        fileName  = path.split("\\")[-1]
        modelName = fileName.split("/")[-1].split(".")[0]
        if not modelName == '__init__':
            ALL_STRATEGIES.append(modelName)
            imp.load_source("strategy", path)
STRATEGY_CLASS = {}
for s in ALL_STRATEGIES:
    cls_obj = getattr(sys.modules['strategy'], s)
    STRATEGY_CLASS[s] = cls_obj
