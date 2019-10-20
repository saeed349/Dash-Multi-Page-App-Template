FROM puckel/docker-airflow

COPY requirements.txt /requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/usr/local/airflow/dags/pack"
# ENV PYTHONPATH "${PYTHONPATH}:${AIRFLOW_HOME}"