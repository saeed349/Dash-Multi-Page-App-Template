echo "scripts on jupyter notebook"
docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_pack/schema/secmaster_db_schema_builder.py"
REM docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_pack/schema/secmaster_db_symbol_loader.py"
docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_pack/schema/risk_db_schema_builder.py"
docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_pack/schema/indicator_db_schema_builder.py"
echo "..."



from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
from sqlalchemy import create_engine
user = PasswordUser(models.User())
user.username = 'admin'
user.email = 'admin@admin.com'
user.password = 'admin'
engine = create_engine("postgresql://airflow:airflow@postgres:5432/airflow")
session = settings.Session(bind=engine)
session.add(user)
session.commit()
exit()