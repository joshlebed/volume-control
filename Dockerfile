# NOTE: CURRENTLY NOT USING THIS 
# TODO: need to figure out how to talk to LIRC on the host machine

FROM python:3.11.3-slim
ADD scripts/volume_controller_evdev_lirc.py volume_controller_evdev_lirc.py
COPY scripts/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
EXPOSE 8000
ENTRYPOINT ["python3.11", "volume_controller_evdev_lirc.py"]