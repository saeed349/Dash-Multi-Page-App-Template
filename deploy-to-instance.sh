#!/bin/bash
ADDRESS=$1
USERNAME=$2

apt-get update && apt-get install -y ssh
ssh -i build.pem $USERNAME@$ADDRESS "mkdir -p /git && git clone $GIT_REPO /git/ats; cd /git/ats && git pull && docker-compose up --build"
