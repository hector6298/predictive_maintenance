FROM apache/airflow:latest

USER root

ENV PIP_USER false

RUN apt-get update && \
     apt-get -y install apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    lsb-release\
    software-properties-common

RUN curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg > /tmp/dkey

RUN curl -sL https://packages.microsoft.com/keys/microsoft.asc | \
    gpg --dearmor | \
    tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null

RUN AZ_REPO=$(lsb_release -cs) &&\
    echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | \
    tee /etc/apt/sources.list.d/azure-cli.list

RUN apt-key add /tmp/dkey && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
    $(lsb_release -cs) \
    stable"

RUN curl -fsSL https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb > packages-microsoft-prod.deb &&\
    dpkg -i packages-microsoft-prod.deb &&\
    rm packages-microsoft-prod.deb

RUN apt-get update && \
    apt-get -y install docker-ce \
    azure-cli \
    dotnet-sdk-2.1 \
    dotnet-runtime-2.1

RUN az upgrade

ADD requirements.txt .

RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir  -r requirements.txt


RUN usermod -aG docker airflow
