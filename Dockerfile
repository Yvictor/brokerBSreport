# Created on Dec, 18, 2016
# @author: Yvictor

FROM yvictor/docker_conda:bsreport
MAINTAINER yvictor

ENV PATH /opt/conda/bin:$PATH

ENTRYPOINT [ "/usr/bin/tini", "--" ]
CMD [ "/bin/bash" ]


# install python3.5 and essential
#RUN apt-get update && apt-get install -y python3.5 python-dev wget cron build-essential libxml2-dev libxslt1-dev
# install pip
#RUN wget https://bootstrap.pypa.io/get-pip.py -O- | python
# install python-lxml
# RUN apt-get update && apt-get install -y libxml2-dev libxslt-dev python-lxml
RUN conda install -c anaconda lxml=3.7.0 -y
RUN conda install -c anaconda beautifulsoup4=4.5.1

COPY . /brokerBSreport
WORKDIR /brokerBSreport


RUN python setup.py install

# RUN make test-captcha-rec
RUN make single-test

# RUN make get-bsreport
CMD make get-bsreport
