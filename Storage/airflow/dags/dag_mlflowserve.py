from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import date, timedelta, datetime

import mlflow_test

DAG_DEFAULT_ARGS={
    'owner':'airflow',
    'depends_on_past':False,
    'retries':1,
    'retry_delay':timedelta(minutes=1)
}

with DAG('mlflow_test', start_date=datetime(2019,1,1), schedule_interval=None,default_args=DAG_DEFAULT_ARGS, catchup=False) as dag:
    
    updating_db_daily = PythonOperator(task_id="testing_ml_flow",python_callable=mlflow_test.test)

    init = BashOperator(bash_command='echo START',task_id='Init')

    updating_db_daily >> init
