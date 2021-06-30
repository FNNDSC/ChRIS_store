#!/bin/bash

G_SYNOPSIS="

 NAME

	make.sh

 SYNOPSIS

	make.sh [up|down]

 ARGS

	[up|down]
	Denotes whether to fire up or tear down the set of services for the development env.

 DESCRIPTION

	make.sh script will depending on the argument fire up or tear down the
	Chris store development environment.

"

if [[ "$#" -eq 0 ]] || [[ "$#" -gt 1 ]]; then
    echo "$G_SYNOPSIS"
    exit 1
fi

source ./decorate.sh
source ./cparse.sh

declare -i STEP=0

HERE=$(pwd)

if [[ "$1" == 'up' ]]; then
    title -d 1 "Changing permissions to 755 on" " $HERE"
        echo "chmod -R 755 $HERE"                     | ./boxes.sh
        chmod -R 755 $HERE
    windowBottom

    title -d 1 "Pulling core containers where needed..."
        printf "${LightCyan}%40s${Green}%-40s${Yellow}\n"                   \
                "docker pull" " mysql:8"                                    | ./boxes.sh
        docker pull mysql:8                                                 | ./boxes.sh
        echo ""                                                             | ./boxes.sh
        printf "${LightCyan}%40s${Green}%-40s${Yellow}\n"                   \
                "docker pull " "fnndsc/docker-swift-onlyone"                | ./boxes.sh
        docker pull fnndsc/docker-swift-onlyone                             | ./boxes.sh
        echo ""                                                             | ./boxes.sh
        printf "${LightCyan}%40s${Green}%-40s${Yellow}\n"                   \
                "docker pull " "fnndsc/chris_store:dev"                     | ./boxes.sh
        docker pull fnndsc/chris_store:dev                                  | ./boxes.sh
        echo ""                                                             | ./boxes.sh
    windowBottom

    title -d 1 "Starting containerized development environment using " " ./docker-compose_dev.yml"
        echo "docker-compose -f docker-compose_dev.yml up -d"     | ./boxes.sh  ${LightCyan}
        windowBottom
        docker-compose -f docker-compose_dev.yml up -d     >& dc.out > /dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | sed -E 's/(.{80})/\1\n/g'                    | ./boxes.sh ${LightGreen}
    windowBottom

    title -d 1 "Waiting until ChRIS store database server is ready to accept connections..."
        docker-compose -f docker-compose_dev.yml exec chris_store_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;' >& dc.out > /dev/null
        echo -en "\033[2A\033[2K"
        sed -E 's/[[:alnum:]]+:/\n&/g' dc.out | ./boxes.sh
        # Give all permissions to chris user on the test DB. This is required for the Django tests:
        echo "Granting <chris> user all DB permissions...."             | ./boxes.sh ${LightCyan}
        echo "This is required for the Django tests."                   | ./boxes.sh ${LightCyan}
        docker-compose -f docker-compose_dev.yml exec chris_store_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON test_chris_store_dev.* TO "chris"@"%"'  >& dc.out > /dev/null
        cat dc.out                                                      | ./boxes.sh
    windowBottom

    title -d 1 "Running Django Unit tests..."
        docker-compose -f docker-compose_dev.yml exec chris_store_dev python manage.py test --exclude-tag integration
        status=$?
        title -d 1 "Unit tests' results"
        if (( $status == 0 )) ; then
            printf "%40s${LightGreen}%40s${NC}\n"                       \
                "Unit tests" "[ success ]"                         | ./boxes.sh
        else
            printf "%40s${Red}%40s${NC}\n"                              \
                "Unit tests" "[ failure ]"                         | ./boxes.sh
        fi
    windowBottom

    title -d 1 "Running Django Integration tests..."
        docker-compose -f docker-compose_dev.yml exec chris_store_dev python manage.py test --tag integration
        status=$?
        title -d 1 "Integration tests' results"
        if (( $status == 0 )) ; then
            printf "%40s${LightGreen}%40s${NC}\n"                       \
                "Integration tests" "[ success ]"                  | ./boxes.sh
        else
            printf "%40s${Red}%40s${NC}\n"                              \
                "Integration tests" "[ failure ]"                  | ./boxes.sh
        fi
    windowBottom

    title -d 1 "Creating two ChRIS store API users"
        echo ""                                         | ./boxes.sh
        echo "Setting superuser chris:chris1234..."     | ./boxes.sh ${LightCyan}
        docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c 'python manage.py createsuperuser --noinput --username chris --email dev@babymri.org 2> /dev/null;'
        docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c \
        'python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username=\"chris\"); user.set_password(\"chris1234\"); user.save()"'
        echo ""                                                   | ./boxes.sh
        echo "Setting normal user cubeadmin:cubeadmin1234..."     | ./boxes.sh ${LightCyan}
        docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c 'python manage.py createsuperuser --noinput --username cubeadmin --email cubeadmin@babymri.org 2> /dev/null;'
        docker-compose -f docker-compose_dev.yml exec chris_store_dev /bin/bash -c \
        'python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username=\"cubeadmin\"); user.set_password(\"cubeadmin1234\"); user.save()"'
        echo ""                                                   | ./boxes.sh
    windowBottom

    title -d 1 "Automatically uploading some plugins to the ChRIS STORE..."
        # Declare an array variable for the list of plugin names to be automatically registered
        # Add a new plugin name to the list if you want it to be automatically registered
        declare -a plugins=( "pl-simplefsapp"
                             "pl-simpledsapp"
                             "pl-s3retrieve"
                             "pl-dircopy"
                             "pl-topologicalcopy"
        )
        declare -i i=1
        for plugin in "${plugins[@]}"; do
            echo ""              | ./boxes.sh
            echo "${STEP}.$i: Uploading $plugin representation to the ChRIS store..."     | ./boxes.sh ${LightCyan}
            PLUGIN_DOCK="fnndsc/${plugin}"
            PLUGIN_MODULE="${plugin:3}"
            docker pull "$PLUGIN_DOCK"
            PLUGIN_REP=$(docker run --rm "$PLUGIN_DOCK" "${PLUGIN_MODULE}" --json 2> /dev/null;)
            docker-compose -f docker-compose_dev.yml exec chris_store_dev python plugins/services/manager.py add "${plugin}" cubeadmin https://github.com/FNNDSC "$PLUGIN_DOCK" --descriptorstring "$PLUGIN_REP" >/dev/null
            ((i++))
        done
    windowBottom

    title -d 1 "Automatically creating a locked pipeline in the ChRIS STORE" "(mutable by the owner and not available to other users)"
        S3_PLUGIN_VER=$(docker run --rm fnndsc/pl-s3retrieve s3retrieve --version)
        SIMPLEDS_PLUGIN_VER=$(docker run --rm fnndsc/pl-simpledsapp simpledsapp --version)
        PIPELINE_NAME="s3retrieve_v${S3_PLUGIN_VER}-simpledsapp_v${SIMPLEDS_PLUGIN_VER}"
        printf "%20s${LightBlue}%60s${NC}\n"                            \
                    "Creating pipeline..." "[ $PIPELINE_NAME ]"         | ./boxes.sh ${LightCyan}
        STR1='[{"plugin_name": "pl-s3retrieve", "plugin_version": "'
        STR2='", "plugin_parameter_defaults": [{"name": "awssecretkey", "default": "somekey"},{"name": "awskeyid", "default": "somekeyid"}], "previous_index": null},
        {"plugin_name": "pl-simpledsapp", "plugin_version": "'
        STR3='", "previous_index": 0}]'
        PLUGIN_TREE=${STR1}${S3_PLUGIN_VER}${STR2}${SIMPLEDS_PLUGIN_VER}${STR3}
        windowBottom
        docker-compose -f docker-compose_dev.yml exec chris_store_dev python pipelines/services/manager.py add "${PIPELINE_NAME}" cubeadmin "${PLUGIN_TREE}"  >& dc.out >/dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | ./boxes.sh
    windowBottom

    title -d 1 "Automatically creating an unlocked pipeline in the ChRIS STORE" "(unmutable and available to all users)"
        PIPELINE_NAME="simpledsapp_v${SIMPLEDS_PLUGIN_VER}-simpledsapp_v${SIMPLEDS_PLUGIN_VER}-simpledsapp_v${SIMPLEDS_PLUGIN_VER}"
        printf "%20s${LightBlue}%60s${NC}\n"                            \
                    "Creating pipeline..." "[ $PIPELINE_NAME ]"         | ./boxes.sh ${LightCyan}
        STR4='[{"plugin_name": "pl-simpledsapp", "plugin_version": "'
        STR5='", "previous_index": null},{"plugin_name": "pl-simpledsapp", "plugin_version": "'
        STR6='", "previous_index": 0},{"plugin_name": "pl-simpledsapp", "plugin_version": "'
        STR7='", "previous_index": 0}]'
        PLUGIN_TREE=${STR4}${SIMPLEDS_PLUGIN_VER}${STR5}${SIMPLEDS_PLUGIN_VER}${STR6}${SIMPLEDS_PLUGIN_VER}${STR7}
        windowBottom
        docker-compose -f docker-compose_dev.yml exec chris_store_dev python pipelines/services/manager.py add "${PIPELINE_NAME}" cubeadmin "${PLUGIN_TREE}" --unlock  >& dc.out >/dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | ./boxes.sh
    windowBottom

    title -d 1 "Restarting ChRIS store's Django development server..."
        printf "${LightCyan}%40s${LightGreen}%40s\n"                \
                    "Restarting" "chris_dev"                        | ./boxes.sh
        windowBottom
        docker-compose -f docker-compose_dev.yml restart chris_store_dev  >& dc.out >/dev/null
        echo -en "\033[2A\033[2K"
        cat dc.out | ./boxes.sh
    windowBottom

    title -d 1 "Attaching interactive terminal (ctrl-c to detach)"
    chris_store_dev=$(docker ps -f name=chris_store_dev_1 -q)
    docker attach --detach-keys ctrl-c $chris_store_dev
fi

if [[ "$1" == 'down' ]]; then
    title -d 1 "Destroying containerized development environment" "from ./docker-compose_dev.yml]"
    echo "Do you want to also remove persistent volumes? [y/n]"             | ./boxes.sh ${LightCyan}
    windowBottom
    old_stty_cfg=$(stty -g)
    stty raw -echo ; REPLY=$(head -c 1) ; stty $old_stty_cfg
    echo -en "\033[2A\033[2K"
    # read -p  " " -n 1 -r REPLY
    if [[ $REPLY =~ ^[Yy]$ ]] ; then
        printf "Removing persistent volumes...\n"                           | ./boxes.sh ${Yellow}
        windowBottom
        docker-compose -f docker-compose_dev.yml down -v >& dc.out >/dev/null
    else
        printf "Keeping persistent volumes...\n"                            | ./boxes.sh ${Yellow}
        windowBottom
        docker-compose -f docker-compose_dev.yml down >& dc.out >/dev/null
    fi
    echo -en "\033[2A\033[2K"
    cat dc.out | ./boxes.sh
    windowBottom
fi
