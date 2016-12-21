# Created on Dec, 18, 2016
# @author: Yvictor

FROM ubuntu:16.04
MAINTAINER yvictor

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-4.1.11-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

RUN apt-get install -y curl grep sed dpkg && \
    TINI_VERSION=`curl https://github.com/krallin/tini/releases/latest | grep -o "/v.*\"" | sed 's:^..\(.*\).$:\1:'` && \
    curl -L "https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini_${TINI_VERSION}.deb" > tini.deb && \
    dpkg -i tini.deb && \
    rm tini.deb && \
    apt-get clean

ENV PATH /opt/conda/bin:$PATH


ENTRYPOINT [ "/usr/bin/tini", "--" ]
RUN [ "/bin/bash" ]
CMD [ "/bin/bash" ]

#RUN [ "/bin/bash" , "conda install numpy -y"]
RUN conda install numpy -y
RUN conda install Cython -y
# install python3.5 and essential
#RUN apt-get update && apt-get install -y python3.5 python-dev wget cron build-essential libxml2-dev libxslt1-dev
# install pip
#RUN wget https://bootstrap.pypa.io/get-pip.py -O- | python
# install python-lxml
#RUN apt-get update && apt-get install -y python-lxml

COPY . /brokerBSreport
WORKDIR /brokerBSreport

RUN python setup.py install

CMD make get-bsreport