# Trading-Infrastructure

## Instructions to Run


cd /d/Google\ drive/Business/Repos/trading-infrastructure/
docker-compose up -d


docker-machine ssh
cd persistant_volume/superset
touch superset.db
exit
docker-compose up -d # or docker-compose up -d superset
docker exec -it superset superset-init #this will go into the initial script later on, u will also have to "touch superset.db" if "superset.db" doenst exits, dont know how to do that yet".
# enter all credentials. ("saeed349" for everything)



docker exec -it minio-image /bin/sh -c "./mc mb mlflow-models"

docker exec -it mlflow-image /bin/sh -c "mlflow experiments create -n mlflow-minio-test --artifact-location s3://mlflow-models"

docker exec mlflow-image /bin/sh -c "mlflow models serve -m /mlflow-image/mlruns/0/09fc38392aa34c8593d91e45d64ccad3/artifacts/model --host=0.0.0.0 -p 2349"