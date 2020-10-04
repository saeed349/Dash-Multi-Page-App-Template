from kiteconnect import KiteConnect
import requests
import re
import time

def zerodha_authentication(api_key,api_secret,userid,password,pin):
    kite=KiteConnect(api_key,api_secret)
    login_url=kite.login_url()
    url = "http://etl-image:8060/zerodha_api"
    payload = {'userid': userid, 'password': password,'pin':pin,'url':login_url}
    regex_token = re.compile("request_token=(.*)&action=login")
    access_token = None
    while access_token is None:
        try:
            r = requests.get(url=url,params=payload)
            access_token=regex_token.search(r.text).group(1)
        except:
            print("DIDNT GET FUCKING TOKEN")
            time.sleep(3)
            pass    
    print("HEREs you FUCKING ToKeNNN",access_token)
    data = kite.generate_session(access_token, api_secret=api_secret)
    kite.set_access_token(data["access_token"])
    return kite


