<p align="center">
    <a href="https://appwrite.io" target="_blank"><img width="260" height="39" src="./images/logo.png" alt="Appwrite Logo"></a>
    <br />
    <br />
    <b>Microservices Based Algorthmic Trading System</b>
    <br />
    <br />
</p>

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

---

MBATS is a simple platform for developing, testing and deploying Algorthmic Trading strategies with a focus on Machine Learning based algorithms.

MBATS aim to make a Quant's life a lot easier by providing a modular easy to setup trading infrastrucutre based on open source tools that can get his/her trading strategy from idea to production within few minutes.

Using MBATS, you can easily create Trading Strategies in Backtrader, manage machine learning models with Ml-Flow, a Posgress database for storing and querying Market data, storage and file management database based on Minio, Superset to visualize performance of backtested and live strategies, schedule tasks using Apache Airflow and many other features to help you get more results in faster times and with a lot less code.

Note: MBATS is not meant to compete with any of the trading platforms, its meant for educational purpose and for that kid who's in a third world country who has a trading idea but no way to monetise it. 

[https://appwrite.io](https://appwrite.io) #linkedin article link here

![MBATS](./images/components.png)  idea

Table of Contents:

- [Quickstart](#Quickstart)
- [Getting Started](#getting-started)
  - [Backtrader](#Backtrader)
  - [Mlflow](#services)
  - [Airflow](#sdks)
  - [Superset](#sdks)
  - [Minio](#sdks)
  - [Postgres](#sdks)
- [Cloud First](#security)
- [Current Features](#follow-us)
- [Planned Features](#follow-us)
- [Contributing](#contributing)
- [License](#license)
      
## Quickstart

[![infrakit+linuxkit](./images/architecture.png)](https://www.youtube.com/watch?v=Qw9zlE3t8Ko "InfraKit + LinuxKit")

MBATS is based on Docker containers. Running your Infrastructure is as easy as running one command from your terminal. You can either run MBATS on your local machine or on the cloud using docker-compose.

The easiest way to start running your MBATS is by running our docker-compose file. Before running the installation command make sure you have [Docker](https://www.docker.com/products/docker-desktop) installed on your machine:

1. Downlod/Clone the Github Repository (Make sure your Docker Machine has access to the location):
- ```git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY```
2. Update the 'WD' variable in .env file to the location of the Cloned directory:
- ```docker-compose up```
3. Run the script to setup up the database schema 
- ```.\starter_script.bat```
4. Run the Docker containers:
- ```docker-compose up -d --build```
    First time would take some time to download all the required images. 

Once the Docker installation completes, you can access the following components from the webaddress
* Jupyter Notebook:http://localhost:8888/
* Airflow: http://localhost:8080
* Mlflow: http://localhost:5500
* PgAdmin: http://localhost:1234
* Superset: http://localhost:8088
* Minio: http://localhost:9000

You can get started with the notebooks in the Jupyter Notebooks. Examples 

Sample Strategy: qpack/q_strategy/sample_strategy_1

## Getting Started

![MBATS Architecture](images/architecture.png)

MBATS is a collection of 9 docker containers acting synchronously to create an environment to develop and productinise trading strategies with ease. The main parts of the MBATS are as follows.

### [Backtrader](https://www.backtrader.com/)
[Backtrader](https://www.backtrader.com/) is an python based opensource event-driven trading strategy backtester with support for live trading. The reason why I choose Backtrader over other opensource backtesters like * [Zipline](https://github.com/quantopian/zipline) and * [QuantConnect Lean](https://github.com/QuantConnect/Lean) is because of the great the great documentation and its community driven. 
Here's a list of subclasses I have written for this project that are derived classed from Backtrader package. 
* [**Run**](https://appwrite.io/docs/auth) - Script that combines the strategy, analyzers and the datafeeds. 
* [**Strategy**](https://appwrite.io/docs/account) - A simple Daily trading strategy that initiates bracket orders based on RSI and Stochastic Indicator.
* [**Logger Analyzer**](https://appwrite.io/docs/users) - Logs the price data and the technical indicator which is used for training the Machine Learning model
* [**Performance Analyzer**](https://appwrite.io/docs/teams) - Measures difference performance metrics of round trip trades and save it in the database which can be later consumed in BI tool (Superset).
* [**Transaction Analyzer**](https://appwrite.io/docs/database) - Records the executed orders into the database. 
* [**Stategy ID Analyzer**](https://appwrite.io/docs/storage) - Keep a record of the metadata of the backtest or live strategy ran.
* [**Oanda Broker**](https://github.com/ftomassetti/backtrader-oandav20)
* [**Postgress Data Feed**](point to the feed)

<p align="center">
  <img width="700" height="500" src="images/backtrader.png">
</p>


### [MLflow](https://mlflow.org/)

Anyone who has worked in the Datascience field would have heard about [Spark](https://spark.apache.org/), well they have brought about a similar disruptive tool to revolutinize the Machine Learning model development and deployement space and that is [MLflow]. Mlflow is an open source platform to manage the ML lifecycle, including experimentation, reproducibility and deployment. It currently offers four components:
* MLflow Tracking
* MLflow Projects
* MLflow Models
* MLflow Registry (Released in 1.4)

There are a few other organizations that try to address this problem but what seperates MLflow from the likes of [Google-TFX](https://www.tensorflow.org/tfx), [Facebook-FBLearner Flow](https://engineering.fb.com/core-data/introducing-fblearner-flow-facebook-s-ai-backbone/) and [Uber-Michelangelo](https://eng.uber.com/michelangelo/) is that MLFlow try to address the concerns of the crowd rather than a single organization and therefore they are more universal and community driven to an extend that [AWS](https://aws.amazon.com/blogs/machine-learning/build-end-to-end-machine-learning-workflows-with-amazon-sagemaker-and-apache-airflow/) and [Azure](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow) has provided integration for MLflow. 

In this project all the ML model can be tracked by the MLflow Tracker and the model artifacts are stored in Minio, the main reason for doing so is that later on I can swap Minio for a Cloud object store like S3. The ML models are served using MLflow pyfunc. We also have the option to serve the model as Rest API using MLFlow (code in sample jupyter notebook)
    
## [Airflow](https://airflow.apache.org/)
Apache Airflow is an open-source workflow management platform, basically Chron on steroids and it has wide array of integration with popular platforms and data stores. 
In this this project we use airflow for scheduling two tasks mainly. One [DAG]() for downloading daily and minute data into the Database controlled by an excel file and another [Dynamic DAG]() for schedulling live strategies controlled by a csv file. 

## [Apache Superset](https://superset.apache.org/)
From the creators of Apache Airflow, Apache Superset is a Data Visualization tool initially designed by Airbnb and later open sourced for the community.
Superset is an interactive Data Exploration toll that will let you slice, dice and visualize data. Why pay for Tableau and PowerBi when you can use something that opensource. We use Superset to visualize Backtesting and Live trading performance.  

## [Minio](https://min.io/)
MinIO is pioneering high performance object storage. With READ/WRITE speeds of 55 GB/s and 35 GB/s on standard hardware, object storage can operate as the primary storage tier for a diverse set of workloads. Amazon’s S3 API is the defacto standard in the object storage world and represents the most modern storage API in the market. MinIO adopted S3 compatibiity early on and was the first to extend it to support S3 Select. Because of this S3 Compatibility by using Minio we have an upperhand of moving towards the Cloud on a later stage when it comes time for scaling and move into the cloud. 

## [PostgreSQL](https://www.postgresql.org/)
We have 2 Databases in our PosgresSQL server, 1 is the Security Master database that stores the Daily and Minute data for Forex Symbols in 2 seperate tables. 
Another Database is used for storing the position information and the performance metrics. 

## Scalling to the Cloud
MLFlow has been developed by the Databricks team and therefore its native in their environment, but also the popularity and adoption of this tool has also ensured it a place in AWS Sage Maker and Azure. Every technology used in this project has a synonymus managed service offered in the cloud.
And the best part of scalling such an microsservices based architecture is that you can do it step by step rather than do it as a whole. Moreover if the cloud is using the same technology then the migration can happen with minimal changes. A simple example for this would be GCP Cloud Composer which is built on top of Apache Airflow and Kubernettes which means that all the DAG's that we are using in this project can be used in cloud composer as well. Similarly I have found GCP has a better strategy and technology in place for building a hybrid cloud based infrastrucure and for that reason here's architecture if this project has to be transfered into the GCP platform. 
![MBATS Cloud Architecture](images/architecture-cloud.png)

## Current Features
* Backtesting and Live trading Forex using Oanda
* Multiple strategy support.
* Machine Learning model development and deployment using MLflow.
* BI Dashboard for real-time monitoring of Live trading and backtesting performance results.
* Easily extensible to support any kind of structured data.
* Infrastructure as Code – less than 5 minutes from scratch to a fully functional trading infrastructure.


## Planned Features

* Support for Equity Database (Backtrader supports [Interactive Brokers out of the box](https://www.backtrader.com/docu/live/ib/ib/]))
* Celery/Kubernetes cluster support for Airflow
* More performance and trade analytics dashboards on Superset 
* Dynamic DAG for model retraining. 
* Automatic Model Selection for Strategies based on ML performance metrics

## Contributing

All code contributions must go through a pull request and approved by a core developer before being merged. This is to ensure proper review of all the code.

## License

This repository is available under the [BSD 3-Clause License](./LICENSE).