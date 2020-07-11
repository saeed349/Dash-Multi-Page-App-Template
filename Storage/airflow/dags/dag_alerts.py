from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from datetime import date, timedelta, datetime

from q_tools import alerts


DAG_DEFAULT_ARGS={
    'owner':'airflow',
    'depends_on_past':False,
    'retries':1,
    'retry_delay':timedelta(minutes=5)
}

with DAG('pattern_alerts', start_date=datetime(2020,1,1), schedule_interval=timedelta(hours=1,minutes=1),default_args=DAG_DEFAULT_ARGS, catchup=False) as dag:
    
    slack_alerts= PythonOperator(task_id="slack_alerts",python_callable=alerts.price_candle_alerts)

    slack_alerts

