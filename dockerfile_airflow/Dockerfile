FROM puckel/docker-airflow

COPY requirements.txt /requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/usr/local/airflow/dags/q_pack"
# ENV PYTHONPATH "${PYTHONPATH}:${AIRFLOW_HOME}"