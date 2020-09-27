from kiteconnect import KiteConnect
import requests
import re

def zerodha_authentication(api_key,api_secret,userid,password,pin):
    kite=KiteConnect(api_key,api_secret)
    login_url=kite.login_url()
    url = "http://etl-image:8060/zerodha_api"
    payload = {'userid': userid, 'password': password,'pin':pin,'url':login_url}
    r = requests.get(url=url,params=payload)
    regex_token = re.compile("request_token=(.*)&action=login")
    access_token=regex_token.search(r.text).group(1)
    data = kite.generate_session(access_token, api_secret=api_secret)
    kite.set_access_token(data["access_token"])
    return kite