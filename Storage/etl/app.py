import os
import subprocess

from flask import Flask, request
from flask_restful import Resource, Api
import db_pack.alpaca.alpaca_daily as alpaca_daily
import db_pack.alpaca.alpaca_symbol_loader as alpaca_symbol_loader

import db_pack.oanda.oanda_daily as oanda_daily
import db_pack.oanda.oanda_symbol_loader as oanda_symbol_loader

app = Flask(__name__)
api = Api(app)

class load_symbols(Resource):
    def get(self,vendor):
        if vendor=='alpaca':
            alpaca_symbol_loader.main()
            return {'Success':'Alpaca Symbols Loaded'}
        elif vendor=='oanda':
            oanda_symbol_loader.main()
            return {'Success':'Oanda Symbols Loaded'}

class load_daily_data(Resource):
    def get(self,vendor):
        if vendor=='alpaca':
            alpaca_daily.main()
            return {'Success':'Alpaca Daily Data Loaded'}
        elif vendor=='oanda':
            oanda_daily.main()
            return {'Success':'Oanda Daily Data Loaded'}
class load_indicator_data(Resource):
    def get(self,vendor):
        cmd_str="""python q_pack/q_run/run_BT.py --todate='2020-03-31'"""
        subprocess.run(cmd_str, shell=True)
        return {'Success':'Indicator Data Loaded'}

class test(Resource):
    def get(self,vendor):
        cmd_str="""echo poda'"""
        subprocess.run(cmd_str, shell=True)
        return {'Success':'Test'}


api.add_resource(load_symbols,'/load_symbols/<string:vendor>')
api.add_resource(load_daily_data,'/load_daily_data/<string:vendor>')
api.add_resource(load_indicator_data,'/load_indicator_data/<string:vendor>')
api.add_resource(test,'/test/<string:vendor>')

class HelloWorld(Resource):
    def get(self):
        return {'about':'Hellooo World'}

    def post(self):
        some_json=request.get_json()
        return{'you sent':some_json}, 201

# class Multi(Resource):
#     def get(self,num):
#         return {'result':num*10}

api.add_resource(HelloWorld,'/')
# api.add_resource(Multi,'/mulit/<int:num>')



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port=8060)
            # port=int(os.environ.get(
            #          'PORT', 8080)))