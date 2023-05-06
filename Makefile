DOCKER_NAME = microprofiler

docker-build:
	docker build -t $(DOCKER_NAME) .

docker-run:
	docker run -i -t $(DOCKER_NAME) /bin/bash
