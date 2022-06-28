# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

#Set the locale
RUN apt update && apt dist-upgrade -y
RUN apt install -y locales libc-bin locales-all libmagic1

RUN sed -i '/pt_BR.UTF-8/s/^#//g' /etc/locale.gen \
    && locale-gen en_US en_US.UTF-8 pt_BR pt_BR.UTF-8 \
    && dpkg-reconfigure locales \
    && update-locale LANG=pt_BR.UTF-8 LANGUAGE=pt_BR.UTF-8 LC_ALL=pt_BR.UTF-8
ENV LANG pt_BR.UTF-8  
ENV LANGUAGE pt_BR:pt  
ENV LC_ALL pt_BR.UTF-8
ENV LC_CTYPE pt_BR.UTF-8
ENV LC_TIME pt_BR.UTF-8

# RUN dpkg-reconfigure locales

# pip Update
RUN /usr/local/bin/python -m pip install --upgrade pip

# Install pip requirements
COPY requirements.txt .
RUN pip install wheel
RUN python -m pip install -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 1000 --disabled-password --gecos "" appuser && chown -R appuser /home/appuser
USER appuser

WORKDIR /home/appuser
COPY ./app /home/appuser
RUN mkdir /home/appuser/outputs

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "main.py"]
