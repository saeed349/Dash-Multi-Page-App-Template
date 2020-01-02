# Trading-Infrastructure - Testing 

## Docker Toolbox
docker-machine rm default
docker-machine create -d virtualbox --virtualbox-cpu-count=2 --virtualbox-memory=3750 --virtualbox-disk-size=75000 default
docker-machine ssh
sudo vi /var/lib/boot2docker/bootlocal.sh
esc i
mkdir /home/docker/persistant_volume
esc o
sudo mount -t vboxsf -o uid=1000,gid=50 Quantinfra /home/docker/persistant_volume   #### PS: the space after "uid=1000, gid=50" messed up by not mounting the folder. 
esc, :wq

set shared folder in Virtual Box as D:\Google drive\Business\Repos\Quant-Trading-Infrastructure
docker-machine restart


## Instructions to Run

docker volume create pg_data
docker volume create pg_data_airflow
docker volume create redis

cd /d/Google\ drive/Business/Repos/Quant-Trading-Infrastructure/
docker-compose up -d --build


docker-machine ssh
cd persistant_volume/superset
touch superset.db  (only works in bash, so I open a bash terminal and created one)
exit
docker-compose up -d # or docker-compose up -d superset
docker exec -it superset superset-init #this will go into the initial script later on, u will also have to "touch superset.db" if "superset.db" doenst exits, dont know how to do that yet".
Superset connectiones
postgres://postgres:posgres349X@postgres_secmaster/securities_master
postgres://postgres:posgres349@postgres_secmaster/risk_db
# enter all credentials. ("saeed349" for everything)



docker exec -it minio-image /bin/sh -c "./mc mb mlflow-models"

docker exec -it mlflow-image /bin/sh -c "mlflow experiments create -n mlflow-minio-test --artifact-location s3://mlflow-models"

docker exec mlflow-image /bin/sh -c "mlflow models serve -m /mlflow-image/mlruns/0/09fc38392aa34c8593d91e45d64ccad3/artifacts/model --host=0.0.0.0 -p 2349"