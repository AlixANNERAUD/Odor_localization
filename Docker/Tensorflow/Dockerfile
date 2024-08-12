FROM tensorflow/tensorflow:latest-gpu-jupyter

COPY ./requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt    

RUN apt update && apt install -y ffmpeg

CMD ["bash", "-c", "source /etc/bash.bashrc && jupyter notebook --notebook-dir=/tf --ip 0.0.0.0 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"]