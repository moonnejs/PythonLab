# encoding: UTF-8
"""
包含一些CTA因子的可视化函数
"""
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Qt4Agg')
#import matplotlib as mpl
#mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei"]#
#mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt 
from calcFunction import get_capital_np,calcPerf,formatNumber

#----------------------------------------------------------------------
def showBtResult(d):
    """
    显示回测结果
    """
    name = d.get('name')
    timeList = d['timeList']
    pnlList = d['pnlList']
    capitalList = d['capitalList']
    drawdownList = d['drawdownList']

    print(u'显示回测结果')
    # 输出
    if len(timeList)>0:
        print('-' * 30)
        print(u'第一笔交易：\t%s' % d['timeList'][0])
        print(u'最后一笔交易：\t%s' % d['timeList'][-1])
        
        print(u'总交易次数：\t%s' % formatNumber(d['totalResult']))        
        print(u'总盈亏：\t%s' % formatNumber(d['capital']))
        print(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))                
        
        print(u'平均每笔盈亏：\t%s' %formatNumber(d['capital']/d['totalResult']))
        print(u'平均每笔佣金：\t%s' %formatNumber(d['totalCommission']/d['totalResult']))
        
        print(u'胜率\t\t%s%%' %formatNumber(d['winningRate']))
        print(u'平均每笔盈利\t%s' %formatNumber(d['averageWinning']))
        print(u'平均每笔亏损\t%s' %formatNumber(d['averageLosing']))
        print(u'盈亏比：\t%s' %formatNumber(d['profitLossRatio']))
        print(u'显示回测结果')

        # 绘图
        import matplotlib.pyplot as plt
        from matplotlib.dates import AutoDateLocator, DateFormatter  
        autodates = AutoDateLocator()  
        yearsFmt = DateFormatter('%m-%d')  
                
        pCapital = plt.subplot(3, 1, 1)
        pCapital.set_ylabel("capital")
        pCapital.plot(timeList,capitalList)
        plt.gcf().autofmt_xdate()        #设置x轴时间外观  
        plt.gcf().subplots_adjust(bottom=0.1)
        plt.gca().xaxis.set_major_locator(autodates)       #设置时间间隔  
        plt.gca().xaxis.set_major_formatter(yearsFmt)      #设置时间显示格式  
                
        pDD = plt.subplot(3, 1, 2)
        pDD.set_ylabel("dd")
        pDD.bar(range(len(drawdownList)), drawdownList)         
        
        pPnl = plt.subplot(3, 1, 3)
        pPnl.set_ylabel("pnl")
        pPnl.hist(pnlList, bins=20)
        
        plt.subplots_adjust(bottom=0.05,hspace=0.3)
        plt.show()

#----------------------------------------------------------------------
def plotSigCaps(timeList,signals,markets,climit=4,wlimit=2,size=1,rate=0.0001,op=True):
    """
    打印某一个信号的资金曲线
    """
    plt.close()
    pnls,poss,fees = get_capital_np(markets,signals,size,rate,\
            climit=climit, wlimit=wlimit,op=op)
    d = calcPerf(timeList,pnls,fees)
    showBtResult(d)

#----------------------------------------------------------------------
def plotFactors(datas,factors=None):
    """打印因子数据到一张图上"""
    plt.close()
    factors = datas.columns.tolist() if factors is None else factors
    if 'pnl' in factors:
        factors.remove('pnl')
    sns.pairplot(datas, vars=factors, hue="pnl", size=1.5)
    plt.show()

#----------------------------------------------------------------------
def plotSigHeats(signals,markets,start=0,step=2,size=1,iters=6):
    """
    打印信号回测盈损热度图,寻找参数稳定岛
    """
    sigMat = pd.DataFrame(index=range(iters),columns=range(iters))
    for i in range(iters):
        for j in range(iters):
            climit = start + i*step
            wlimit = start + j*step
            pnls,poss,fees = get_capital_np(markets,signals,size,0.0001,climit=climit,wlimit=wlimit,op=False)
            caps = np.cumsum(pnls[pnls!=0])
            sigMat[i][j] = caps[-1]
    #ratioDict = {}
    #for i in range(iters):
    #    for j in range(iters):
    #        climit = start + i*step
    #        wlimit = start + j*step
    #        ratio = wlimit/climit
    #        if ratio in ratioDict:
    #            ratioDict[ratio] += sigMat[i][j] 
    #        else:
    #            ratioDict[ratio] = sigMat[i][j] 
    #ratioList = []
    #capList = []
    #ratioDict0 = sorted(ratioDict.iteritems(),key=lambda d:d[0])
    #for k,v in ratioDict0:
    #    ratioList.append(k)
    #    capList.append(v)
    #plt.plot(ratioList,capList)
    #plt.xlabel(u'盈亏比')
    #plt.ylabel(u'盈利')
    sns.heatmap(sigMat.values.astype(np.float64),annot=True,fmt='.2f',annot_kws={"weight": "bold"})
    xTicks   = [i+0.5 for i in range(iters)]
    yTicks   = [iters-i-0.5 for i in range(iters)]
    xyLabels = [str(start+i*step) for i in range(iters)]
    _, labels = plt.yticks(yTicks,xyLabels)
    plt.setp(labels, rotation=0)
    _, labels = plt.xticks(xTicks,xyLabels)
    plt.setp(labels, rotation=90)
    plt.xlabel('LossStop @')
    plt.ylabel('ProfitTarget  @')
    return sigMat

#----------------------------------------------------------------------
def plotVarVPnl(pdData,s):
    """
    展示策略状态的10分位盈亏
    """
    data  = pdData.copy()
    minV  = min(data[s])
    maxV  = max(data[s])
    data[s+'_split'] = data[s].apply(lambda x:round(x*10/(maxV-minV))*(maxV-minV)/10)
    data.groupby(s+'_split').pnl.sum().plot(kind='bar')
    plt.show()

#------------------------------------------------
def plotPortfolioCurve(cap_table,weis):
    """输出策略组合的资金曲线"""
    plt.close()
    names = weis.index.tolist()
    cap_table['tol']=1
    for n in names:
        cap_table['tol'] += cap_table[n]*weis['weight'][n]
    cap_table['tol'].plot()
    plt.show()
