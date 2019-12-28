#https://bigdata-etl.com/apache-airflow-create-dynamic-dag/

from airflow.models import DAG
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from datetime import date, timedelta, datetime
import json
import pandas as pd

def create_dag(dag_id,
               schedule,
               default_args,
               conf):
    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
    with dag:
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
        command={}
        for i,row in df.iterrows():
            command['--strat_name']=row['Strategy']
            command['--mode']=str(row['Mode'])
            command['--tickers']=row['Securities']
            command['--broker_token']=row['Token']
            command['--broker_account']=row['Account']
            command['--strat_param']=row['Strategy Parameters']
            final_commmand='python /usr/local/airflow/dags/12_Clean_Strategy_BT.py '+' '.join([(k+"="+v) for k, v in command.items() if v!=''])
            tab = BashOperator(
                bash_command=final_commmand,
                task_id=(row['Strategy']+str(i)),
                dag=dag
            )
            init >> tab >> clear
        # for table in conf:
        #     tab = DummyOperator(
        #         task_id=table,
        #         dag=dag
        #     )
            # init >> tab >> clear
        return dag
schedule = None #"@daily"
dag_id = "Dynamic_DAG"
df=pd.read_csv('/usr/local/airflow/dags/strategy.csv')
df.fillna('', inplace=True)
args = {
    'owner': 'BigDataETL',
    'depends_on_past': False,
    'email': ['bigdataetl@gmail.com'],
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
