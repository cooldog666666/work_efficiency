# automatos-run
Automatos Executon Enviornment Docker Image v1.0
Maintainer: sleepless.knights.scrum@emc.com

-------------------------
How to build docker image
-------------------------
Run the following command to build latest stable image:
$> sudo docker build -t automatos-run .


This will download the required layers and build an image with name 'automatos-run'

---------------------------
How to run the docker image
---------------------------
The image can be run interactively or used to run a single execution if provided with the correct volume information. The image requires that your ctt workspace is connected to the container via a volume and it is advised that a volume is connected for automatos logging.

To run the container interactivly use the following command:
$> sudo docker run -it \
	-v /host/path/to/ctt-workspace/Automatos:/opt/Automatos/x \
	-v /host/path/to/ctt-test-workspace/Automatos:/opt/Automatos/dev \
	automatos-run /bin/bash

Subsequent interactive runs can be done by starting the container
$> sudo docker -it start automatos-run

To run the container to execute the a single run of dropin tests use the following commands:
$> sudo docker run -d \
	-v /host/path/to/ctt-workspace/Automatos:/opt/Automatos/x \
	-v /host/path/to/ctt-test-workspace/Automatos:/opt/Automatos/dev \
	automatos-run automatos.pl

Subsequent non-interactive runs can be done by rerunning the container:
$> sudo docker start automatos-run

-----------------
Setting up shares
-----------------
Some of tests or testset configurations require access to c4shares, automatos shares, or CI-Build in order to execute. Here is an example of linking a volume to these shares that maps to the hosts volume when the host is a SLES12 dev vm.
$> sudo docker run -d \
	-v /host/path/to/ctt-workspace/Automatos:/opt/Automatos/x \
	-v /host/path/to/ctt-test-workspace/Automatos:/opt/Automatos/dev \
	-v /c4shares/Public:/c4shares/Public:ro \
	-v /CI-Build:/CI-Build:ro \
        automatos-run automatos.pl


------------------------------------------------------------------
Setting up enviornment variables that will exist inside the docker
------------------------------------------------------------------
 docker run -it -v /opt/Automatos/x:/opt/Automatos/x -e DOCKER_HOST=10.244.102.59 automatos-run bash


--------------------------------
Example of running a sanity test 
--------------------------------
docker run -v /opt/logs:/opt/logs \
	-v /opt/Automatos:/opt/Automatos \
	-v /mnt/automatos_hop:/mnt/automatos_hop \
	-v /var/run/docker.sock:/var/run/docker.sock \
	automatos-run \
	bash -c "cd /opt/Automatos/dev/latest/Automatos/Framework/Dev; perl bin/automatos.pl --configFile SanityTests/mainConfigFileVnxe.xml"



