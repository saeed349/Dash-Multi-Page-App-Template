FROM python:3.7-slim

# USER root
# COPY . ./

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/q_pack"

WORKDIR /app
    
# CMD gunicorn --bind :60 app:app
# CMD gunicorn app:app


# Another way to give root access without password in the compose
    # environment:
    #   GRANT_SUDO: "yes"
    # user:
    #   "root"