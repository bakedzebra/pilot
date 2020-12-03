FROM python:3.7
RUN mkdir /src
ADD pilot-controller/pilot.py /src

RUN pip install kopf
RUN pip install kubernetes

CMD kopf run /src/pilot.py --verbose