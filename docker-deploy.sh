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

	docker-deploy.sh script will depending on the argument deploy the ChRIS store set
    of services in production or tear down the system.

"

if [[ "$#" -eq 0 ]] || [[ "$#" -gt 1 ]]; then
    echo "$G_SYNOPSIS"
    exit 1
fi

source ./decorate.sh

declare -i STEP=0


if [[ "$1" == 'up' ]]; then

    title -d 1 "Starting containerized production environment on using " " ./docker-compose.yml"
    echo ""
    echo "docker stack deploy -c docker-compose.yml chris_store_stack"
    docker stack deploy -c docker-compose.yml chris_store_stack
    windowBottom

    title -d 1 "Waiting until chris store stack containers are running on swarm"
    for i in {1..30}; do
        sleep 5
            chris_store=$(docker ps -f name=chris_store.1. -q)
        if [ -n "$chris_store" ]; then
          echo "Success: chris store container is up"
          break
        fi
    done
    if [ -z "$chris_store" ]; then
        echo "Error: couldn't start chris store container"
        exit 1
    fi
    windowBottom

    title -d 1 "Waiting until ChRIS store is ready to accept connections..."
    docker exec $chris_store sh -c 'while ! curl -sSf http://localhost:8010/api/v1/users/ 2> /dev/null; do sleep 5; done;'
    windowBottom

    title -d 1 "Creating superuser chris"
    docker exec -it $chris_store sh -c 'python manage.py createsuperuser --username chris --email dev@babymri.org'
    windowBottom

    title -d 1 "Uploading the plugin fnndsc/pl-dircopy"
    docker exec $chris_store python plugins/services/manager.py add pl-dircopy chris https://github.com/FNNDSC/pl-dircopy fnndsc/pl-dircopy --descriptorstring "$(docker run --rm fnndsc/pl-dircopy dircopy --json 2> /dev/null)"
    windowBottom

    title -d 1 "Uploading the plugin fnndsc/pl-topologicalcopy"
    docker exec $chris_store python plugins/services/manager.py add pl-topologicalcopy chris https://github.com/FNNDSC/pl-topologicalcopy fnndsc/pl-topologicalcopy --descriptorstring "$(docker run --rm fnndsc/pl-topologicalcopy topologicalcopy --json 2> /dev/null)"
    windowBottom
fi

if [[ "$1" == 'down' ]]; then
    title -d 1 "Destroying containerized production environment" "from ./docker-compose.yml"
    echo
    docker stack rm chris_store_stack
    sleep 10
    echo
    printf "Do you want to also remove persistent volumes?"
    read -p  " [y/n] " -n 1 -r
    echo
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] ; then
        sleep 10
        docker volume rm chris_store_stack_chris_store_db_data
        docker volume rm chris_store_stack_swift_storage
    fi
    windowBottom
fi
