#!/bin/bash
#
# NAME
#
#   docker-make.sh
#

source ./decorate.sh

title -d 1 "Changing permissions to 755 on" " $(pwd)"
echo "chmod -R 755 $(pwd)"
chmod -R 755 $(pwd)
windowBottom

title -d 1 "Starting containerized development environment using " " ./docker-compose.yml"
docker pull fnndsc/chris_store:dev
echo "docker-compose up -d"
docker-compose up -d
windowBottom

title -d 1 "Waiting until mysql server is ready to accept connections..."
docker-compose exec chris_store_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;'
# Give all permissions to chris user in the DB. This is required for the Django tests:
docker-compose exec chris_store_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON *.* TO "chris"@"%"'
windowBottom

title -d 1 "Applying migrations..."
docker-compose exec chris_store_dev python manage.py migrate
windowBottom

title -d 1 "Running Django Unit tests..."
docker-compose exec chris_store_dev python manage.py test --exclude-tag integration
windowBottom

title -d 1 "Running Django Integration tests..."
docker-compose exec chris_store_dev python manage.py test --tag integration
windowBottom

title -d 1 "Creating two ChRIS store API users"
echo ""
echo "Setting superuser chris:chris1234 ..."
docker-compose exec chris_store_dev /bin/bash -c 'python manage.py createsuperuser --noinput --username chris --email dev@babymri.org 2> /dev/null;'
docker-compose exec chris_store_dev /bin/bash -c \
'python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username=\"chris\"); user.set_password(\"chris1234\"); user.save()"'
echo ""
echo "Setting normal user cubeadmin:cubeadmin1234 ..."
docker-compose exec chris_store_dev /bin/bash -c 'python manage.py createsuperuser --noinput --username cubeadmin --email cubeadmin@babymri.org 2> /dev/null;'
docker-compose exec chris_store_dev /bin/bash -c \
'python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username=\"cubeadmin\"); user.set_password(\"cubeadmin1234\"); user.save()"'
echo ""
windowBottom

title -d 1 "Automatically uploading some plugins to the ChRIS STORE ..."
# Declare an array variable for the list of plugin names to be automatically registered
# Add a new plugin name to the list if you want it to be automatically registered
declare -a plugins=( "simplefsapp"
                     "simpledsapp"
                     "pacsquery"
                     "pacsretrieve"
                     "s3retrieve"
                     "s3push"
                     "dircopy"
)
declare -i i=1
declare -i STEP=7
for plugin in "${plugins[@]}"; do
    echo "${STEP}.$i: Uploading $plugin representation to the ChRIS store ..."
    PLUGIN_DOCK="fnndsc/pl-${plugin}"
    PLUGIN_REP=$(docker run --rm "$PLUGIN_DOCK" "${plugin}.py" --json 2> /dev/null;)
    docker-compose exec chris_store_dev python plugins/services/manager.py add "${plugin}" cubeadmin https://github.com/FNNDSC "$PLUGIN_DOCK" --descriptorstring "$PLUGIN_REP"
    ((i++))
done
windowBottom

title -d 1 "Restarting ChRIS store's Django development server in interactive mode..."
docker-compose stop chris_store_dev
docker-compose rm -f chris_store_dev
docker-compose run --service-ports chris_store_dev
echo ""
windowBottom
