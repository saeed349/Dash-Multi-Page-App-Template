from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from datetime import date, timedelta, datetime

from db_pack.oanda import oanda_historical


DAG_DEFAULT_ARGS={
    'owner':'airflow',
    'depends_on_past':False,
    'retries':1,
    'retry_delay':timedelta(minutes=5)
}

with DAG('fx_d_data_download', start_date=datetime(2020,1,1), schedule_interval=timedelta(days=1,minutes=1),default_args=DAG_DEFAULT_ARGS, catchup=False) as dag:
    
    update_secmaster_db = PythonOperator(task_id="update_secmaster_db",python_callable=oanda_historical.main,op_kwargs={'freq':'d','initial_start_date':datetime(2010,1,1)})

    update_ind_db = BashOperator(
        bash_command="""python /usr/local/airflow/dags/q_pack/q_run/run_BT.py --fromdate='2010-1-1' --timeframe='d' --load_symbol='True'""",
        task_id='update_ind_db')

    update_secmaster_db >> update_ind_db

