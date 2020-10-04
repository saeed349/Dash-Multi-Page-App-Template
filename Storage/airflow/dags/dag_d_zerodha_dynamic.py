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

from db_pack.zerodha import zerodha_historical
import q_run.run_BT_dynamic as run_BT_dynamic

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
        number_of_dages = 4
        symbol_subset = 5

        def chunker_list(seq, size):
            return (seq[i::size] for i in range(size))
        symbol_chunks=list(chunker_list(ticker_list,number_of_dages))
        tasks=[]
        for i in range(len(symbol_chunks)):
            symbols=symbol_chunks[i]
            list_ticker_list = [symbols[x:x+symbol_subset] for x in range(0, len(symbols), symbol_subset)]
            task=PythonOperator(task_id=(str(i)+'_DAG'),python_callable=run_BT_dynamic.dag_function,op_kwargs={'list_ticker_list':list_ticker_list})
            tasks.append(task)   
        # update_secmaster_db >> tasks >> clear
        init >> tasks >> clear
        return dag

schedule = None #"@daily"
dag_id = "zerodha_dynamic"
universe='Indian Equity'
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
