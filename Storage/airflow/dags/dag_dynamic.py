#https://bigdata-etl.com/apache-airflow-create-dynamic-dag/

from airflow.models import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator
import json
import pandas as pd

def create_dag(dag_id,
               schedule,
               default_args,
               conf):
    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
    with dag:
        init = DummyOperator(
            task_id='Init',
            dag=dag
        )
        clear = DummyOperator(
            task_id='clear',
            dag=dag
        )
        for table in conf:
            tab = DummyOperator(
                task_id=table,
                dag=dag
            )
            init >> tab >> clear
        return dag
# with open("/usr/local/airflow/dags/process_configuration.json") as json_data:
#     conf = json.load(json_data)
#     schedule = conf['schedule']
#     dag_id = conf['name']
#     args = {
#         'owner': 'BigDataETL',
#         'depends_on_past': False,
#         'start_date': datetime.now(),
#         'email': ['bigdataetl@gmail.com'],
#         'email_on_failure': False,
#         'email_on_retry': False,
#         'retries': 1,
#         'retry_delay': timedelta(minutes=5),
#         'concurrency': 1,
#         'max_active_runs': 1
#     }
#     globals()[dag_id] = create_dag(dag_id, schedule, args, conf)
schedule = "@hourly"
dag_id = "Dynamic_DAG"
df=pd.read_csv('/usr/local/airflow/dags/strategy.csv')
args = {
    'owner': 'BigDataETL',
    'depends_on_past': False,
    'start_date': datetime.now(),
    'email': ['bigdataetl@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'concurrency': 1,
    'max_active_runs': 1
}
globals()[dag_id] = create_dag(dag_id, schedule, args, df['Strategy'])
