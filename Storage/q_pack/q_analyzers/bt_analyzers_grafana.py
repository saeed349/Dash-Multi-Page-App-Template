from __future__ import (absolute_import, division, print_function,
					unicode_literals)

import backtrader as bt
import pandas as pd
from influxdb import DataFrameClient

class GrafanaAn(bt.Analyzer):

def create_analysis(self):
	self.tradeBegV=0
	self.tradeEndV=0

def notify_trade(self, trade):
	t=self.datas[0].datetime.date(0).strftime('%Y-%m-%dT%H:%M:%SZ')
	if trade.justopened:
		self.tradeBegV=self.strategy.broker.getvalue()
		self.tradeBegTime=t
		self.tradeBegP=float(trade.price)
		self.tradeSize=float(trade.size)
		#Send a buy indicator to Grafana
		jsonBody=[{"measurement":"portfolio",
					"tags":{
					"stock":self.data._name,
					"market":self.strategy.params['market'],
					"ind":self.strategy.indName
					},
					"time":t,
					"fields":{
						"BuyPrice":float(trade.price),
						"Size":float(trade.size),
				}
				  }]
		ar=self.strategy.params['client'].write_points(jsonBody,database='simulation')
		assert ar
	elif trade.status == trade.Closed:
		self.tradeEndV = self.strategy.broker.getvalue()
		ret=(self.tradeEndV/self.tradeBegV-1)*100
		t=self.datas[0].datetime.date(0).strftime('%Y-%m-%dT%H:%M:%SZ')
		jsonBody=[{"measurement":"trade",
					"tags":{
					"stock":self.data._name,
					"market":self.strategy.params['market'],
					"ind":self.strategy.indName
					},
					"time":t,
					"fields":{
						"commission":float(trade.commission),
						"return":float(ret),
						"pnl":float(trade.pnl),
						"pnlcomm":float(trade.pnlcomm),
						"tradingTime":int(trade.barlen),
						"beginTime":self.tradeBegTime,
						"endTime":t
					}
				  }]
		ar=self.strategy.params['client'].write_points(jsonBody,database='simulation')
		assert ar
		jsonBody=[{"measurement":"portfolio",
					"tags":{
					"stock":self.data._name,
					"market":self.strategy.params['market'],
					"ind":self.strategy.indName
					},
					"time":t,
					"fields":{
						"SellPrice":float(trade.pnl/self.tradeSize+self.tradeBegP),
						"Size":float(trade.size),
				}
				  }]
		ar=self.strategy.params['client'].write_points(jsonBody,database='simulation')
		assert ar
		
def start(self):
	self._i=0
	self._dict={}

def next(self):
	_value=self.strategy.broker.getvalue()
	_pos=self.strategy.getposition().size
	self._dict[self._i]={'portv':_value,'pos':_pos}
	self._i+=1
	#for k,ind in self.strategy.ind.items():

def stop(self):
	portVFrame=pd.DataFrame.from_dict(self._dict,"index")
	portVFrame.columns=['portv','pos']
	priceFrame=self.data._dataname
	portVFrame.set_index(priceFrame.index,inplace=True)
	priceFrame['portv']=portVFrame['portv']
	priceFrame['pos']=portVFrame['pos']
	priceFrame=priceFrame.astype(float)
	client=DataFrameClient(database='simulation')
	ar=client.write_points(priceFrame,"portfolio",{"ind":self.strategy.indName,"market":self.strategy.params['market'],"stock":self.data._name},database='simulation')
	assert ar
	#Print Monthly return
	_mr=self.strategy.analyzers.TR.get_analysis()
	MonthlyReport=pd.DataFrame.from_dict(_mr,"index")
	ar=client.write_points(MonthlyReport,"monthlyReturn",{"ind":self.strategy.indName,"market":self.strategy.params['market'],"stock":self.data._name},database='simulation')
	assert ar

def get_analysis(self):
	return None