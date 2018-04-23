# encoding: UTF-8

import numba as nb
import numpy as np
import pandas as pd
from ctaBase import *
from datetime import timedelta
from numpy import inf,nan,float32,float64
from dataFunction import loadStrategyData

#----------------------------------------------------------------------
def formatNumber(n):
    """格式化数字到字符串"""
    rn = round(n, 2)        # 保留两位小数
    return format(rn, ',')  # 加上千分符

#------------------------------------------------
def calc_sharpe_ratio(returns, periods=250):
    """计算夏普比率"""
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

#------------------------------------------------
def calc_drawdowns(caps):
    """计算最大回测和最大回测周期"""
    hwm = [0]
    eq_idxs = caps.index.values
    eq_idx  = len(caps.index.values)
    drawdown = pd.Series(index = range(1,eq_idx))
    duration = pd.Series(index = range(0,eq_idx))
    duration[0] = 0
    for t in range(1,eq_idx):
        cur_hwm = max(hwm[t-1], caps[eq_idxs[t]])
        hwm.append(cur_hwm)
        drawdown[t]= hwm[t] - caps[eq_idxs[t]]
        duration[t]= 0 if drawdown[t] == 0 else duration[t-1] + 1
    return drawdown.max(), int(duration.max())

#------------------------------------------------
def reshape_min(datas):
    """数据按分钟切片"""
    pnl_idxs  = datas.index
    start     = pnl_idxs[0].replace(second = 0,microsecond = 0)
    end       = pnl_idxs[-1].replace(second = 0,microsecond = 0)
    minutes   = int((end-start).total_seconds()/60)+2
    min_idx   = [start + timedelta(minutes=i) for i in xrange(minutes)]
    index     = 0
    datas_min = pd.Series(index = min_idx)
    for i in xrange(minutes):
        datas_min[start+timedelta(minutes=i)] = 0
        while index < len(pnl_idxs.values) and start+timedelta(minutes=i) > pnl_idxs[index]:
            datas_min[start+timedelta(minutes=i)] += datas[pnl_idxs.values[index]]
            index += 1
    return datas_min

# 计算结算表现
#------------------------------------------------
def calcPerf(times,pnls,fees):
    """数据按分钟切片"""
    pnlList = []            # 每笔盈亏序列
    capital = 0             # 资金
    maxCapital = 0          # 资金最高净值
    drawdown = 0            # 回撤
    
    totalResult = 0         # 总成交数量
    totalCommission = 0     # 总手续费
    
    timeList = []           # 时间序列
    capitalList = []        # 盈亏汇总的时间序列
    drawdownList = []       # 回撤的时间序列
    
    winningResult = 0       # 盈利次数
    losingResult = 0        # 亏损次数        
    totalWinning = 0        # 总盈利金额        
    totalLosing = 0         # 总亏损金额        
    
    for t,pnl,fee in zip(times,pnls,fees):
        if pnl !=0 :
            capital += pnl
            maxCapital = max(capital, maxCapital)
            drawdown = round(capital,2)
            pnlList.append(pnl)

            # 交易的时间戳使用平仓时间
            timeList.append(t)
            capitalList.append(capital)
            drawdownList.append(drawdown)
            
            totalResult += 1
            totalCommission += fee
            
            if pnl >= 0:
                winningResult += 1
                totalWinning += pnl
            else:
                losingResult += 1
                totalLosing += pnl
            
    # 计算盈亏相关数据
    averageWinning  = 0
    averageLosing   = 0
    profitLossRatio = 0
    winningRate     = 0 if totalResult==0 else winningResult*1.0/totalResult*100
    averageWinning  = 0 if winningResult==0 else totalWinning/winningResult
    averageLosing   = 0 if losingResult==0 else totalLosing/losingResult
    profitLossRatio = 0 if averageLosing==0 else -averageWinning/averageLosing 

    # 返回回测结果
    d = {}
    d['name']            = u'向量回测'
    d['capital']         = round(capital,2)
    d['maxCapital']      = maxCapital
    d['drawdown']        = drawdown
    d['totalResult']     = round(totalResult,2)
    d['totalCommission'] = round(totalCommission,2)
    d['timeList']        = timeList
    d['pnlList']         = pnlList
    d['capitalList']     = capitalList
    d['drawdownList']    = drawdownList
    d['winningRate']     = round(winningRate,2)
    d['averageWinning']  = round(averageWinning,2)
    d['averageLosing']   = round(averageLosing,2)
    d['profitLossRatio'] = round(profitLossRatio,2)
    d['datas']           = None

    return d

@nb.autojit
#------------------------------------------------
def get_capital_np(markets,signals,size,commiRate,climit = 4, wlimit = 2, op=True):
    """使用numpy回测，标签的盈亏, op 表示是否延迟一个tick以后撮合"""
    postions    = np.zeros(len(signals))
    actions     = np.zeros(len(signals))
    costs       = np.zeros(len(signals))
    pnls        = np.zeros(len(signals))
    fees        = np.zeros(len(signals))
    lastsignal  = 0
    lastpos     = 0
    lastcost    = 0
    num         = 0
    for num in range(1,len(signals)):
        postions[num]   = lastpos
        actions[num]    = 0
        costs[num]      = lastcost
        pnls[num]       = 0
        # 止盈止损
        if lastpos > 0 and \
            (markets[num,1]<=lastcost-climit or markets[num,1]>=lastcost+wlimit):
            postions[num]   = 0
            actions[num]    = -1
            costs[num]      = 0
            fees[num]       = (markets[num,1]+lastcost)*size*commiRate
            pnls[num]       = (markets[num,1]-lastcost)*size-fees[num]
        elif lastpos < 0 and \
            (markets[num,0]>=lastcost+climit or markets[num,0]<=lastcost-wlimit):
            postions[num]   = 0
            actions[num]    = 1
            costs[num]      = 0
            fees[num]       = (markets[num,0]+lastcost)*size*commiRate
            pnls[num]       = (lastcost-markets[num,0])*size-fees[num] 
        # 开仓
        if op:
            lastsignal      = signals[num]
        if lastsignal > 0 and lastpos == 0:
            postions[num]   = 1
            actions[num]    = 1
            costs[num]      = markets[num,0]
        elif lastsignal < 0 and lastpos == 0:
            postions[num]   = -1
            actions[num]    = -1
            costs[num]      = markets[num,1]
        lastpos     = postions[num]
        lastcost    = costs[num]
        lastsignal  = signals[num]
    return pnls,actions,fees

#------------------------------------------------
def get_perf(datas,signals,size,commiRate):
    """并行回测，标签的盈亏"""

    # 计算交易信号，并整理数据
    predatas = datas[datas.columns.drop(['askPrice1','bidPrice1'])].values
    datas = datas[['askPrice1','bidPrice1']]
    datas['signals'] = signals

    # 计算仓位信息
    datas = datas[datas['signals']!=0]
    datas['position'] = datas['signals'].diff()
    datas = datas.dropna(axis=0, how='any')
    posInfo = datas[datas['position']!=0]

    #　根据仓位信息计算开仓成本
    posInfo['cost'] = posInfo.apply(lambda x:x['position']*x['askPrice1'] if x['position']>0 else -x['position']*x['bidPrice1'],axis=1)

    # 计算每笔的手续费，第一笔被重复计算
    posInfo['feeP'] = abs(posInfo['cost'])*size*commiRate

    # 计算每笔盈亏，第一笔是错误的
    posInfo['pnl'] = (posInfo['cost']-posInfo['cost'].shift(1))/2
    posInfo['pnl'] = posInfo.apply(lambda x:-x['pnl'] if x['position']>0 else x['pnl'],axis=1) - (posInfo['feeP'] + posInfo['feeP'].shift(1))/2
    
    # 修正错误信息
    posInfo['position'].iloc[0]  = posInfo['position'].iloc[0]/2
    posInfo['position'].iloc[-1] = posInfo['position'].iloc[-1]/2
    posInfo['pnl'][0] = 0

    # 计算总手续费和总资金
    posInfo['fee'] = posInfo.apply(np.cumsum)['feeP']
    posInfo['cap'] = posInfo.apply(np.cumsum)['pnl']
    pnl_min = reshape_min(posInfo['pnl'])
    cap_min = reshape_min(posInfo['cap'])
    period = posInfo['pnl'].count()
    mdd, ddt = calc_drawdowns(posInfo['cap'])
    return posInfo['cap'][-1],mdd

#------------------------------------------------
def get_daily_rtn(strategyNames,strategyBases,startDate='20100101',endDate='20181030'):
    """获取每日盈亏"""
    fields = ['name','date','pnl']
    rtns = pd.DataFrame()
    caps = pd.DataFrame()
    for name,base in zip(strategyNames,strategyBases):
        datas = loadStrategyData(CAPITAL_DB_NAME,name,startDate,endDate,fields)
        datas['pnl']=datas['pnl']/base
        rtns = pd.concat([rtns,datas],axis = 0)
        datas=datas.set_index('date')
        datas['cap']=datas.apply(np.cumsum)['pnl']
        #datas.plot(kind='line',title = name)
        datas.reset_index(drop=False,inplace=True)
        caps = pd.concat([caps,datas],axis = 0)
    rtn_table = pd.crosstab(rtns['date'],rtns['name'], values = rtns['pnl'], aggfunc = sum)  #  一维表变为二维表
    rtn_table.fillna(0, inplace = True)
    cap_table = pd.crosstab(caps['date'],caps['name'], values = caps['cap'], aggfunc = sum)  #  一维表变为二维表
    cap_table.fillna(method='pad', inplace = True)  #  将NaN置换为0
    cap_table.fillna(0, inplace = True)  #  将NaN置换为0
    return rtn_table,cap_table
    #plt.show()
    #cap_table.head(20)
    

#------------------------------------------------
def get_best_wei(rtn_table,risk_aversion):
    """获取指定风险厌恶系数下的最优策略配置组合"""
    from cvxopt import matrix, solvers
    cov_mat = rtn_table.cov() * 250    # 协方差矩阵(1年250个交易日)
    exp_rtn = rtn_table.mean() * 250   # 标的预期收益(1年250个交易日)
    P = risk_aversion * matrix(cov_mat.values)
    q = -1 * matrix(exp_rtn.values)
    G = matrix(np.vstack((np.diag(np.ones(len(exp_rtn))),np.diag(-np.ones(len(exp_rtn))))))
    h = matrix(np.array([np.ones(len(exp_rtn)),np.zeros(len(exp_rtn))]).reshape(len(exp_rtn)*2,1))
    A = matrix(np.ones(len(exp_rtn)),(1,len(exp_rtn)))
    b = matrix([1.0])
    solvers.options['show_progress'] = True
    sol = solvers.qp(P, q, G, h, A, b)
    weis=pd.DataFrame(index=exp_rtn.index,data = np.round(sol['x'],2), columns = ['weight'])  # 权重精确到小数点后两位
    return weis

