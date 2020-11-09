#https://bigdata-etl.com/apache-airflow-create-dynamic-dag/

from airflow.models import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import date, timedelta, datetime
import json
import pandas as pd
import boto3
import io
import numpy as np

from db_pack.zerodha import zerodha_historical
import q_run.run_BT_dynamic as run_BT_dynamic

import q_credentials.db_secmaster_cred as db_secmaster_cred
import psycopg2
db_host=db_secmaster_cred.dbHost 
db_user=db_secmaster_cred.dbUser
db_password=db_secmaster_cred.dbPWD
db_name=db_secmaster_cred.dbName

def create_dag(dag_id,
               schedule,
               default_args,
               conf):
    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
    with dag:

        # update_secmaster_db = PythonOperator(task_id="update_secmaster_db",python_callable=zerodha_historical.main,op_kwargs={'freq':'d','initial_start_date':datetime(2016,1,1)})

        init = BashOperator(
            bash_command='echo START' ,
            task_id='Init',
            dag=dag
        )
        clear = BashOperator(
            bash_command='echo STOPPING',
            task_id='clear',
            dag=dag
        )
        number_of_dags = 4
        # symbol_subset = 5
        tasks=[]
        sub_df=np.array_split(df_ticker_last_day, number_of_dags)
        for i in range(len(sub_df)):
            task=PythonOperator(task_id=(str(i)+'_DAG'),python_callable=run_BT_dynamic.dag_function,op_kwargs={'df':sub_df[i],'time_frame':'m'})
            tasks.append(task)   
        # update_secmaster_db >> tasks >> clear
        init >> tasks >> clear
        return dag

schedule = None #"@daily"
dag_id = "alpaca_dynamic_monthly"
universe='US Equity'
s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
Bucket="airflow-files"
if universe=='US Equity':
    Key="interested_tickers_alpaca.xlsx"
elif universe=='Forex':
    Key="interested_tickers_oanda.xlsx"
elif universe=='Indian Equity':
    Key="interested_tickers_india.xlsx"
read_file = s3.get_object(Bucket=Bucket, Key=Key)
df = pd.read_excel(io.BytesIO(read_file['Body'].read()),sheet_name="d")

ticker_list = list(df['Tickers'])

# Getting the last date for each interested tickers
conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
sql="""select a.min_date, a.max_date, b.id as symbol_id, b.ticker from
    (select min(date_price) as min_date, max(date_price) as max_date, symbol_id
    from {}_data 
    group by symbol_id) a right join symbol b on a.symbol_id = b.id 
    where b.ticker in {} """.format('d',str(tuple(df['Tickers'])).replace(",)", ")"))
df_ticker_last_day=pd.read_sql(sql,con=conn)
conn.close()
df.fillna('', inplace=True)

args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date':datetime(2019,1,1),
    # 'start_date': datetime.now(),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'concurrency': 1,
    'max_active_runs': 1
}
globals()[dag_id] = create_dag(dag_id, schedule, args, df)
