FROM ubuntu:24.04

RUN apt-get update

RUN apt-get install -y \
    bash \
    gfortran \
    python3 \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-boto3

WORKDIR /app

COPY hades/ ./hades/
COPY hades_batch_runner/ ./hades_batch_runner/

WORKDIR /app/hades
RUN chmod +x compile.sh
RUN ./compile.sh

WORKDIR /app/hades_batch_runner
RUN chmod +x job.sh

CMD ["python3", "main.py"]