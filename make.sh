#!/bin/bash

G_SYNOPSIS="

 NAME

	docker-make.sh

 SYNOPSIS

	docker-make.sh [up|down]

 ARGS

	[up|down]
	Denotes whether to fire up or tear down the set of services for the development env.

 DESCRIPTION

	docker-make.sh script will depending on the argument fire up or tear down the
	Chris store development environment.

"

if [[ "$#" -eq 0 ]] || [[ "$#" -gt 1 ]]; then
    echo "$G_SYNOPSIS"
    exit 1
fi

source ./decorate.sh

declare -i STEP=0

if [[ "$1" == 'up' ]]; then
    title -d 1 "Changing permissions to 755 on" " $(pwd)"
    echo "chmod -R 755 $(pwd)"
    chmod -R 755 $(pwd)
    windowBottom

    title -d 1 "Starting containerized development environment using " " ./docker-compose_dev.yml"
    docker pull mysql:5
    docker pull fnndsc/docker-swift-onlyone
    docker pull fnndsc/chris_store:dev
    echo ""
    echo "docker-compose -f docker-compose_dev.yml up -d"
    docker-compose -f docker-compose_dev.yml up -d
    windowBottom

    title -d 1 "Waiting until ChRIS store database server is ready to accept connections..."
    docker-compose -f docker-compose_dev.yml exec chris_store_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;'
    # Give all permissions to chris user on the test DB. This is required for the Django tests:
    docker-compose -f docker-compose_dev.yml exec chris_store_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON test_chris_store_dev.* TO "chris"@"%"'
    windowBottom

    title -d 1 "Running Django Unit tests..."
    docker-compose -f docker-compose_dev.yml exec chris_store_dev python manage.py test --exclude-tag integration
    windowBottom

    title -d 1 "Running Django Integration tests..."
    docker-compose -f docker-compose_dev.yml exec chris_store_dev python manage.py test --tag integration
    windowBottom

    title -d 1 "Creating two ChRIS store API users"
    echo ""
    echo "Setting superuser chris:chris1234..."
    docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c 'python manage.py createsuperuser --noinput --username chris --email dev@babymri.org 2> /dev/null;'
    docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c \
    'python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username=\"chris\"); user.set_password(\"chris1234\"); user.save()"'
    echo ""
    echo "Setting normal user cubeadmin:cubeadmin1234..."
    docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c 'python manage.py createsuperuser --noinput --username cubeadmin --email cubeadmin@babymri.org 2> /dev/null;'
    docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c \
    'python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username=\"cubeadmin\"); user.set_password(\"cubeadmin1234\"); user.save()"'
    echo ""
    windowBottom

    title -d 1 "Automatically uploading some plugins to the ChRIS STORE..."
    # Declare an array variable for the list of plugin names to be automatically registered
    # Add a new plugin name to the list if you want it to be automatically registered
    declare -a plugins=( "pl-simplefsapp"
                         "pl-simpledsapp"
                         "pl-pacsquery"
                         "pl-pacsretrieve"
                         "pl-s3retrieve"
                         "pl-s3push"
                         "pl-dircopy"
    )
    declare -i i=1
    declare -i STEP=7
    for plugin in "${plugins[@]}"; do
        echo ""
        echo "${STEP}.$i: Uploading $plugin representation to the ChRIS store..."
        PLUGIN_DOCK="fnndsc/${plugin}"
        PLUGIN_MODULE="${plugin:3}"
        docker pull "$PLUGIN_DOCK"
        PLUGIN_REP=$(docker run --rm "$PLUGIN_DOCK" "${PLUGIN_MODULE}.py" --json 2> /dev/null;)
        docker-compose -f docker-compose_dev.yml exec chris_store_dev python plugins/services/manager.py add "${plugin}" cubeadmin https://github.com/FNNDSC "$PLUGIN_DOCK" --descriptorstring "$PLUGIN_REP" >/dev/null
        ((i++))
    done
    windowBottom

    title -d 1 "Automatically creating a locked pipeline in the ChRIS STORE" "(mutable by the owner and not available to other users)"
    S3_PLUGIN_VER=$(docker run --rm fnndsc/pl-s3retrieve s3retrieve.py --version)
    SIMPLEDS_PLUGIN_VER=$(docker run --rm fnndsc/pl-simpledsapp simpledsapp.py --version)
    PIPELINE_NAME="s3retrieve_v${S3_PLUGIN_VER}-simpledsapp_v${SIMPLEDS_PLUGIN_VER}"
    echo "Creating pipeline named '$PIPELINE_NAME'"

    STR1='[{"plugin_name": "pl-s3retrieve", "plugin_version": "'
    STR2='", "plugin_parameter_defaults": [{"name": "awssecretkey", "default": "somekey"},{"name": "awskeyid", "default": "somekeyid"}], "previous_index": null},
    {"plugin_name": "pl-simpledsapp", "plugin_version": "'
    STR3='", "previous_index": 0}]'
    PLUGIN_TREE=${STR1}${S3_PLUGIN_VER}${STR2}${SIMPLEDS_PLUGIN_VER}${STR3}

    docker-compose -f docker-compose_dev.yml exec chris_store_dev python pipelines/services/manager.py add "${PIPELINE_NAME}" cubeadmin "${PLUGIN_TREE}"
    windowBottom

    title -d 1 "Automatically creating an unlocked pipeline in the ChRIS STORE" "(unmutable and available to all users)"
    PIPELINE_NAME="simpledsapp_v${SIMPLEDS_PLUGIN_VER}-simpledsapp_v${SIMPLEDS_PLUGIN_VER}-simpledsapp_v${SIMPLEDS_PLUGIN_VER}"
    echo "Creating pipeline named '$PIPELINE_NAME'"

    STR4='[{"plugin_name": "pl-simpledsapp", "plugin_version": "'
    STR5='", "previous_index": null},{"plugin_name": "pl-simpledsapp", "plugin_version": "'
    STR6='", "previous_index": 0},{"plugin_name": "pl-simpledsapp", "plugin_version": "'
    STR7='", "previous_index": 0}]'
    PLUGIN_TREE=${STR4}${SIMPLEDS_PLUGIN_VER}${STR5}${SIMPLEDS_PLUGIN_VER}${STR6}${SIMPLEDS_PLUGIN_VER}${STR7}

    docker-compose -f docker-compose_dev.yml exec chris_store_dev python pipelines/services/manager.py add "${PIPELINE_NAME}" cubeadmin "${PLUGIN_TREE}" --unlock
    windowBottom

    title -d 1 "Restarting ChRIS store's Django development server" "in interactive mode..."
    docker-compose -f docker-compose_dev.yml stop chris_store_dev
    docker-compose -f docker-compose_dev.yml rm -f chris_store_dev
    docker-compose -f docker-compose_dev.yml run --service-ports chris_store_dev
    echo ""
    windowBottom
fi

if [[ "$1" == 'down' ]]; then
    title -d 1 "Destroying containerized development environment" "from ./docker-compose_dev.yml]"
    echo
    printf "Do you want to also remove persistent volumes?"
    read -p  " [y/n] " -n 1 -r
    echo
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] ; then
        docker-compose -f docker-compose_dev.yml down -v
    else
        docker-compose -f docker-compose_dev.yml down
    fi
    windowBottom
fi
