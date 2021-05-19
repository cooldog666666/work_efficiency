# Automatos Dockerfile

FROM		ubuntu:14.04
MAINTAINER	lance.selvidge@emc.com

RUN apt-get update -y && apt-get install -y \
	curl \
	wget \
	git \
 	libssh2-1-dev \
 	libssl0.9.8 \
	openjdk-6-jre \
	libssl0.9.8 \
	net-tools \
	pkg-config \
	python-dev \
	python-pip \
	mysql-server-core-5.5 \
	mysql-server-5.5 \
	mysql-client-5.5 \
	rsyslog \
	cron \
        portmap \
        nis \
	autofs \
	socket \
	software-properties-common \
        jq \
        docker.io \
	vim 


RUN wget -qO - http://packages.confluent.io/deb/3.3/archive.key | sudo apt-key add -
RUN add-apt-repository "deb [arch=amd64] http://packages.confluent.io/deb/3.3 stable main"

RUN apt-get update -y && sudo apt-get install -y \
	confluent-platform-2.11 \
	librdkafka-dev 


# SETUP WORKDIR
ENV WORK /opt/workingdir
ENV ARCHIVE_BASE_URL=http://10.244.18.149
ENV ARCHIVE_URL=http://10.244.18.149/opt/Automatos/fileshare/archives/
ENV AUTOMATOS=/opt/Automatos/x/Automatos
ENV AUTOMATOS_TEST=/opt/Automatos/dev
WORKDIR $WORK


# Get ActiveState perl
ENV PERL_VERSION=ActivePerl-5.16
ENV PERL_ARCHIVE=ActivePerl-5.16.3.1603-x86_64-linux-glibc-2.3.5-296746
ENV PERL_HOME=/opt/perl
RUN echo "curl -fsSl \"${ARCHIVE_URL}${PERL_ARCHIVE}.tar.gz\" | tar -xzC /opt "
RUN curl -fsSl "${ARCHIVE_URL}${PERL_ARCHIVE}.tar.gz" \
        | tar -xzC /opt

RUN echo "cd /opt/$PERL_ARCHIVE && ./install.sh --prefix /opt/$PERL_VERSION --license-accepted  --no-install-html"

RUN cd /opt/$PERL_ARCHIVE && ./install.sh \
        --prefix /opt/$PERL_VERSION \
        --license-accepted  \
        --no-install-html

RUN ln -s /opt/$PERL_VERSION $PERL_HOME
ENV PATH=$PERL_HOME/bin:$PATH


# Add required cpan perl packages
RUN export PERL_MM_USE_DEFAULT=1
RUN cpan install CPAN
RUN perl -MCPAN -e 'install CPAN'
RUN perl -MCPAN -e 'install aliased'


# Add required ActiveSite perl packages
ENV PPMINSTALL=ppminstall.pl
env LATEST_PPMINSTALL_DIR=/opt/Automatos/x/Automatos/Framework/Dev/bin/
RUN curl -sSO http://10.244.18.149/opt/Automatos/x/Automatos/Framework/Dev/bin/$PPMINSTALL
#RUN curl -sSO \"${ARCHIVE_BASE_URL}${LATEST_PPMINSTALL_DIR}${PPMINSTALL}\"

RUN perl $WORK/$PPMINSTALL
RUN perl $WORK/$PPMINSTALL --automatos
RUN perl $WORK/$PPMINSTALL --db


# Setup ssh keys
ADD config/opt/ssh_keys/id_rsa.pub /opt/ssh_keys/vnxe/id_rsa.pub
ADD config/opt/ssh_keys/id_rsa.root /opt/ssh_keys/vnxe/id_rsa.root
ADD config/opt/ssh_keys/id_rsa.pub /root/.ssh/id_rsa.pub
ADD config/opt/ssh_keys/id_rsa.root /root/.ssh/id_rsa

RUN chmod 600 /root/.ssh/id_rsa
RUN chmod 755 /root/.ssh/id_rsa.pub
RUN echo '        StrictHostKeyChecking no' >> /etc/ssh/ssh_config 

ADD config/opt/ssh_keys/id_rsa.pub /root/.ssh/id_rsa.pub
ADD config/opt/ssh_keys/id_rsa.root /root/.ssh/id_rsa


# Setup cron jobs
ADD config/var/spool/cron/crontabs/root /var/spool/cron/crontabs
RUN chmod 600 /var/spool/cron/crontabs/root

# Setup bash startup script
ADD config/root/.bashrc /root/.bashrc

# enable cron logging
RUN sed -i.bak s/^#cron/cron/ /etc/rsyslog.d/50-default.conf


# configure NIS and autofs
ADD config/etc/auto.master /etc/auto.master
ADD config/etc/nsswitch.conf /etc/nsswitch.conf
ADD config/etc/resolv.conf /etc/resolv.conf
ADD config/etc/yp.conf /etc/yp.conf


ADD work/dockerSetup.sh $WORK/dockerSetup.sh


ENV PERL5LIB /opt/Automatos/x/Automatos/Framework/Execution/lib:\
/opt/Automatos/x/Automatos/Framework/Execution/ExecutionService/lib:\
/opt/Automatos/x/Automatos/Framework/Dev/lib:\
/opt/Automatos/dev/latest/Automatos/Tests/Dev


ADD README.md $WORK/README.md
CMD ["bash"]
