#!/bin/bash
ADDRESS=$1
USERNAME=$2

test -f build.pem && chmod 600 build.pem
apt-get update && apt-get install -y ssh
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i build.pem $USERNAME@$ADDRESS "mkdir -p /git && git clone $GIT_REPO /git/ats; cd /git/ats && git pull && docker-compose up --build"
