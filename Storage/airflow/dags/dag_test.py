from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from datetime import date, timedelta, datetime
import time

from db_pack.oanda import oanda_historical

def test():
    i=0
    while i<10:
        print(i)
        time.sleep(1)
        i=i+1

DAG_DEFAULT_ARGS={
    'owner':'airflow',
    'depends_on_past':False,
    'retries':1,
    'retry_delay':timedelta(minutes=5)
}

with DAG('fx_test', start_date=datetime(2020,1,1), schedule_interval=timedelta(minutes=1),default_args=DAG_DEFAULT_ARGS, catchup=False) as dag:
    
    update_secmaster_db = PythonOperator(task_id="update_secmaster_db",python_callable=test)

    update_ind_db = BashOperator(
            bash_command='echo STOPPING',
            task_id='clear',
            dag=dag)

    update_secmaster_db >> update_ind_db

