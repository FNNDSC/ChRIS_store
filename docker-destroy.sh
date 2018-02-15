#!/bin/bash

source ./decorate.sh

title -d 1 "Destroying ChRIS store containerized development environment" "from ./docker-compose.yml"
windowBottom

title -d 1 "Stopping services..."
    docker-compose stop
windowBottom

title -d 1 "Removing all containers..."
    docker-compose rm -vf 
windowBottom

title -d 1 "Destroying persistent volumes..."
    a_PVOLS=(
        "chrisstore_chris_store_dev_db_data"
        "chrisstore_swift_storage"
    )
    for VOL in ${a_PVOLS[@]} ; do 
        read -p  "Do you want to remove persistent volume $VOL? " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            docker volume rm $VOL
        fi
    done
windowBottom