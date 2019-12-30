import mlflow
import mlflow.pyfunc
import boto3

def test():
    # mlflow.tracking.set_tracking_uri('http://mlflow-image:5500')
    # s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    model_predict=mlflow.pyfunc.load_model(model_uri="s3://mlflow-models/b5c9975d81c64bc3b662654007e1c20d/artifacts/model")
    print(model_predict.predict([[40,50]])[0])