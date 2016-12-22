# Created on Dec, 18, 2016
# @author: Yvictor

FROM yvictor/docker_conda:miniconda3
MAINTAINER yvictor

ENV PATH /opt/conda/bin:$PATH

ENTRYPOINT [ "/usr/bin/tini", "--" ]
CMD [ "/bin/bash" ]

#RUN [ "/bin/bash" , "conda install numpy -y"]
RUN conda install numpy -y
RUN conda install h5py pytables -y
RUN conda install pillow -y
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