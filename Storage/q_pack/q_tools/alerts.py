import boto3
import pandas as pd
import io
import datetime
import psycopg2
import requests
import json
from io import StringIO, BytesIO 


import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.db_indicator_cred as db_indicator_cred

conn_indicator = psycopg2.connect(host=db_indicator_cred.dbHost , database=db_indicator_cred.dbName, user=db_indicator_cred.dbUser, password=db_indicator_cred.dbPWD)
conn_secmaster = psycopg2.connect(host=db_secmaster_cred.dbHost , database=db_secmaster_cred.dbName, user=db_secmaster_cred.dbUser, password=db_secmaster_cred.dbPWD)
webhook='https://hooks.slack.com/services/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'

# from twilio.rest import Client
# account_sid = 'AC212a9d358d91860c6ad2d96d892ba62f' # Found on Twilio Console Dashboard
# auth_token = '3679727df6a1cefb275c11382c94fb0f' # Found on Twilio Console Dashboard
# myPhone = '+15512083809'
# TwilioNumber = '+12058467764' 
# client = Client(account_sid, auth_token)
# def twilio_msg(msg):
#     client.messages.create(to=myPhone,from_=TwilioNumber, body=msg)


def price_candle_alerts():
    s3 = boto3.client('s3', endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    Bucket="airflow-files"
    Key="alerts.csv"
    read_file = s3.get_object(Bucket=Bucket, Key=Key)
    df = pd.read_csv(read_file['Body'],sep=',')
    df

    for i,row in df[df['Sent']!=True].iterrows(): # only take the one where sent is not true
        if row['Type']=='Price':
            sql="select d.date_price as date, open_price as open, high_price as high, low_price as low , close_price as close,volume from %s d join symbol s on d.symbol_id = s.id where s.ticker='%s' and d.date_price > '%s' order by date desc limit 1" %('h1_data', row['Ticker'], row['Time'])
            df_price=pd.read_sql(sql,con=conn_secmaster)
            if row['Price']<=df_price['low'][0]:
                result= row['Ticker'] + " has reached your price target of "+ str(row['Price'])
    #             twilio_msg(result)
                data={'text':result}
                print(data)
                requests.post(webhook,json.dumps(data))
                df.loc[i,'Sent']=True
        elif row['Type']=='Candle':
            result=""
            for t in row['Frequency'].split(","):
                for ind in ['candle_1','candle_2','candle_3']:
                    sql="select d.date_price as date, d.value from %s d join symbol s on d.symbol_id = s.id join indicator i on i.id=d.indicator_id where s.ticker='%s' and i.name = '%s' and d.date_price > '%s' order by date desc limit 1" %((t+'_data'),row['Ticker'], ind, row['Time'])
                    df_ind=pd.read_sql(sql,con=conn_indicator)
                    if df_ind['value'][0]['level']!=0:
                        result+= "\n" + (row["Ticker"]+"-"+t+"-Pattern="+df_ind['value'][0]['pattern_name'])
                        df.loc[i,'Sent']=True
            if result:
    #             twilio_msg(result)
                data={'text':result}
                print(data)
                requests.post(webhook,json.dumps(data))

    csv_buffer = StringIO()
    df.to_csv(csv_buffer,index=False)
    s3.put_object(Bucket=Bucket, Key=Key,Body=csv_buffer.getvalue())