from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from datetime import date, timedelta, datetime

import fx_oanda_daily
import fx_oanda_minute

DAG_DEFAULT_ARGS={
    'owner':'airflow',
    'depends_on_past':False,
    'retries':1,
    'retry_delay':timedelta(minutes=1)
}

with DAG('fx_data_download', start_date=datetime(2019,1,1), schedule_interval='@daily',default_args=DAG_DEFAULT_ARGS, catchup=False) as dag:
    waiting_file_task = FileSensor(task_id="waiting_file_task",fs_conn_id="fs_default",filepath="/usr/local/airflow/dags/interested_tickers.xlsx", poke_interval=1)
    
    updating_db_daily = PythonOperator(task_id="updating_db_daily",python_callable=fx_oanda_daily.main)

    updating_db_minute = PythonOperator(task_id="updating_db_minute",python_callable=fx_oanda_minute.main)

    waiting_file_task >> updating_db_daily >> updating_db_minute
