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