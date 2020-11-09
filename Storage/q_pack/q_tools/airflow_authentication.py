
# docker exec -it my_airflow python /usr/local/airflow/dags/q_pack/q_tools/airflow_authentication.py
# docker exec -it microservices-based-algorithmic-trading-system_airflow_1 python
from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
from sqlalchemy import create_engine
user = PasswordUser(models.User())
user.username = 'admin'
user.email = 'admin@admin.com'
user.password = 'quant@cloud'
engine = create_engine("postgresql://airflow:airflow@postgres:5432/airflow")
session = settings.Session(bind=engine)
session.add(user)
session.commit()
exit()

