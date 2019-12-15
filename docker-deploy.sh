#!/bin/bash

G_SYNOPSIS="

 NAME

	docker-deploy.sh

 SYNOPSIS

	docker-deploy.sh [up|down]

 ARGS

	[up|down]
	Denotes whether to fire up or tear down the production set of services.

 DESCRIPTION

	docker-deploy.sh script will depending on the argument deploy the Chris store set
    of services in production or tear down the system.

"

if [[ "$#" -eq 0 ]] || [[ "$#" -gt 1 ]]; then
    echo "$G_SYNOPSIS"
    exit 1
fi

source ./decorate.sh

declare -i STEP=0


if [[ "$1" == 'up' ]]; then
    title -d 1 "Starting containerized production environment using " " ./docker-compose.yml"
    docker pull mysql:5
    docker pull fnndsc/docker-swift-onlyone
    docker pull fnndsc/chris_store
    echo "docker-compose up -d"
    docker-compose up -d
    windowBottom

    title -d 1 "Waiting until ChRIS store is ready to accept connections..."
    docker-compose exec chris_store sh -c 'while ! curl -sSf http://localhost:8010/api/v1/users/ 2> /dev/null; do sleep 5; done;'
    windowBottom

    title -d 1 "Creating superuser chris"
    docker-compose exec chris_store sh -c 'python manage.py createsuperuser --username chris --email dev@babymri.org'
    windowBottom
fi

if [[ "$1" == 'down' ]]; then
    title -d 1 "Destroying containerized production environment" "from ./docker-compose.yml"
    echo
    printf "Do you want to also remove persistent volumes?"
    read -p  " [y/n] " -n 1 -r
    echo
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] ; then
        docker-compose down -v
    else
        docker-compose down
    fi
    windowBottom
fi
