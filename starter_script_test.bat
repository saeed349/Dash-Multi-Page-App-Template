echo "Testing scripts on jupyter notebook"
REM docker ps -a
docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_schema/secmaster_db_schema_builder.py"
docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_schema/secmaster_db_symbol_loader.py"
docker exec -it jupyter-image /bin/sh -c "python /home/jovyan/work/q_pack/db_schema/risk_db_schema_builder.py"
echo "..."