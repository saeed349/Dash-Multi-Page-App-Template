<p align="center">
    <a href="https://appwrite.io" target="_blank"><img width="260" height="39" src="images/logo.png" alt="Appwrite Logo"></a>
    <br />
    <br />
    <b>Microservices Based Algorthmic Trading System</b>
    <br />
    <br />
</p>

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

---

MBATS is a simple platform for developing, testing and deploying algorthmic trading strategies with a focus on Machine Learning based algorithms.

MBATS aim to make a Quant's life a lot easier by providing a modular easy to setup trading infrastrucutre based on open source tools that can get his/her trading strategy from idea to production within few minutes.

Using MBATS, you can easily create Trading Strategies in Backtrader, manage machine learning models with Ml-Flow, a Posgress database for storing and querying Market data, storage and file management database based on Minio (S3 like), Superset to visualize performance of backtested and live strategies, schedule tasks using Apache Airflow and many other features to help you get more results in faster times and with a lot less code.

Note: MBATS is not meant to compete with any of the trading platforms, its meant for educational purpose and for that kid who's in a third world country who has a trading idea but no way to monetise it. 

[https://appwrite.io](https://appwrite.io) #linkedin article link here

![MBATS](images/components.png)  idea

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

[![infrakit+linuxkit](./docs/images/infrakit_linuxkit_screencap.png)](https://www.youtube.com/watch?v=Qw9zlE3t8Ko "InfraKit + LinuxKit")

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

Once the Docker installation completes, go you can access the following components from the webaddress
Jupyter Notebook:http://localhost:8888/
Airflow: http://localhost:8080
Mlflow: http://localhost:5500
PgAdmin: http://localhost:1234
Superset: http://localhost:8088
Minio: http://localhost:9000

You can get started with the notebooks in the Jupyter Notebooks. Examples 

Sample Strategy: qpack/q_strategy/sample_strategy_1

## Getting Started

![MBATS Architecture](images/architecture.png)

Getting started with Appwrite is as easy as creating a new project, choosing your platform and integrating its SDK in your code. You can easily get started with your platform of choice by reading one of our Getting Started tutorials.


### Backtrader

* [**Run**](https://appwrite.io/docs/auth) - Manage user authentication using multiple sign-in methods and account recovery.
* [**Strategy**](https://appwrite.io/docs/account) - Manage current user account. Track and manage the user sessions, devices, and security audit log.
* [**Logger Analyzer**](https://appwrite.io/docs/users) - Manage and list all project users when in admin mode.
* [**Performance Analyzer**](https://appwrite.io/docs/teams) - Manage and group users in teams. Manage memberships, invites and user roles within a team.
* [**Transaction Analyzer**](https://appwrite.io/docs/database) - Manage database collections and documents. Read, create, update and delete documents and filter lists of documents collections using an advanced filter with graph-like capabilities.
* [**Stategy ID Analyzer**](https://appwrite.io/docs/storage) - Manage storage files. Read, create, delete and preview files. Manipulate the preview of your files to fit your 

Since this is a docker environment you can completely swap the Backtester framework and use something that you are familiar with like
* [Zipline](https://github.com/quantopian/zipline)
* [QuantConnect Lean](https://github.com/QuantConnect/Lean)
* [QSTrader](https://github.com/mhallsmoore/qstrader)


### MLFLOW

MlflowWrite about why you choose MLFLOW
    
## Airflow

.What jobs are being done in Airflow. 

## Superset

## Minio

## Posgres

## Scalling to the Cloud
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

## Contributing

All code contributions must go through a pull request and approved by a core developer before being merged. This is to ensure proper review of all the code.

## License

This repository is available under the [BSD 3-Clause License](./LICENSE).