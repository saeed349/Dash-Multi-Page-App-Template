import os

from flask import Flask, request
from flask_restful import Resource, Api
import db_pack.alpaca as alpaca_db

app = Flask(__name__)
api = Api(app)

class load_symbol(Resource):
    def get(self,vendor):
        alpaca_db.alpaca_symbol_loader()
        return {'vendor':vendor}


class HelloWorld(Resource):
    def get(self):
        return {'about':'Hellooo World'}

    def post(self):
        some_json=request.get_json()
        return{'you sent':some_json}, 201

class Multi(Resource):
    def get(self,num):
        return {'result':num*10}

api.add_resource(load_symbol,'/load_symbol/<string:vendor>')

api.add_resource(HelloWorld,'/')
api.add_resource(Multi,'/mulit/<int:num>')



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port=8060)
            # port=int(os.environ.get(
            #          'PORT', 8080)))