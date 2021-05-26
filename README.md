# ![ChRIS logo](https://github.com/FNNDSC/ChRIS_store/blob/master/docs/assets/logo_chris.png) ChRIS_store
[![Build Status](https://travis-ci.org/FNNDSC/ChRIS_store.svg?branch=master)](https://travis-ci.org/FNNDSC/ChRIS_store)
![License][license-badge]
![Last Commit][last-commit-badge]

Back end for the ChRIS store. This is a Django-MySQL project that houses descriptions of ChRIS plugin-apps and workflows for registering to a ChRIS CUBE instance.

## ChRIS store development, testing and deployment

### Abstract

This page describes how to quickly get the set of services comprising the backend up and running for development and how to run the automated tests. A production deployment of the ChRIS store backend services is also explained.

### Preconditions

#### Install latest Docker and Docker Compose. Currently tested platforms
* ``Ubuntu 18.04+ and MAC OS X 10.14+ and Fedora 31+`` ([Additional instructions for Fedora](https://github.com/mairin/ChRIS_store/wiki/Getting-the-ChRIS-Store-to-work-on-Fedora))
* ``Docker 18.06.0+``
* ``Docker Compose 1.27.0+``

#### On a Linux machine make sure to add your computer user to the ``docker`` group 

Consult this page: https://docs.docker.com/engine/install/linux-postinstall/

### TL;DR

If you read nothing else on this page, and just want to get an instance of the ChRIS store backend services up and 
running with no mess, no fuss:

```bash
git clone https://github.com/FNNDSC/ChRIS_store
cd ChRIS_store
./make.sh down ; ./make.sh up
```

The resulting instance uses the default Django development server and therefore is not suitable for production.

### Production deployment

#### To get the production system up:

Start a local Docker Swarm cluster if not already started:

```bash
docker swarm init --advertise-addr 127.0.0.1
```

Fetch source code:

```bash
git clone https://github.com/FNNDSC/ChRIS_store
cd ChRIS_store
```

Create ``secrets`` directory:

```bash
mkdir swarm/prod_deployments/secrets
```

Now copy all the required secret configuration files into the ``secrets`` directory, please take a look at 
[this](https://github.com/FNNDSC/ChRIS_store/wiki/ChRIS-store-backend-production-services-secret-configuration-files) 
wiki page to learn more about these files 

Deploy ChRIS store backend containers:

```bash
./deploy.sh up
```

#### To tear down:

Remove ChRIS store backend containers:

```bash
cd ChRIS_store
./deploy.sh down
```

Remove the local Docker Swarm cluster if desired:

```bash
docker swarm leave --force
```


### Development

#### Optionally setup a virtual environment

#### Install virtualenv
```bash
pip install virtualenv virtualenvwrapper
```

#### Setup your virtual environments
Create a directory for your virtual environments e.g.:
```bash
mkdir ~/Python_Envs
```

You might want to add to your .bashrc file these two lines:
```bash
export WORKON_HOME=~/Python_Envs
source /usr/local/bin/virtualenvwrapper.sh
```

Then you can source your ``.bashrc`` and create a new Python3 virtual environment:

```bash
mkvirtualenv --python=python3 chris_store_env
```

To activate chris_store_env:
```bash
workon chris_store_env
```

To deactivate chris_store_env:
```bash
deactivate
```

#### Install useful python tools in your virtual environment
```bash
cd ChRIS_store
workon chris_store_env
pip install httpie
pip install python-swiftclient
pip install django-storage-swift
```

You can also install some python libraries (not all of them) specified in the ``requirements/base.txt`` and 
``requirements/local.txt`` files in the source repo


To list installed dependencies in chris_store_env:
```
pip freeze --local
```

### Instantiate ChRIS Store dev environment

Start ChRIS Store services by running the make bash script from the repository source directory

```bash
git clone https://github.com/FNNDSC/ChRIS_store.git
./make.sh up
```
All the steps performed by the above script are properly documented in the script itself. 

After running this script all the automated tests should have successfully run and a Django development server should be running in interactive mode in this terminal.

#### Rerun automated tests after modifying source code

Open another terminal and find out the id of the container running the Django server in interactive mode:
```bash
chris_store=$(docker ps -f ancestor=fnndsc/chris_store:dev -f name=chris_store_dev -q)
```
and run the Unit and Integration tests within that container. 

To run only the Unit tests:

```bash
docker exec -it $chris_store python manage.py test --exclude-tag integration
```

To run only the Integration tests:

```bash
docker exec -it $chris_store python manage.py test --tag integration
```

To run all the tests:

```bash
docker exec -it $chris_store python manage.py test 
```

#### Check code coverage of the automated tests
Make sure the ``store_backend/`` dir is world writable. Then type:

```bash
docker exec -it $chris_store coverage run --source=plugins,users manage.py test
docker exec -it $chris_store coverage report
```

### Using [HTTPie](https://httpie.org/) to play with the REST API 

#### A simple GET request:
```bash
http http://localhost:8010/api/v1/
```

#### A simple POST request to register a new plugin app in the store:
First save the plugin representation json file by running the plugin with the `--savejson` flag:
```bash
docker run --rm -v /tmp/json:/json fnndsc/pl-simplefsapp simplefsapp --savejson /json
```
Then upload the plugin representation json file to the ChRIS Store as part of the `POST` request:
```bash
http -a cubeadmin:cubeadmin1234 -f POST http://localhost:8010/api/v1/plugins/ dock_image=fnndsc/pl-simplefsapp descriptor_file@/tmp/json/SimpleFSApp.json public_repo=https://github.com/FNNDSC/pl-simplefsapp name=pl-simplefsapp
```

#### An unauthenticated POST request to create a new ChRIS store user account:
```bash
http POST http://localhost:8010/api/v1/users/ Content-Type:application/vnd.collection+json Accept:application/vnd.collection+json template:='{"data":[{"name":"email","value":"developer@babymri.org"}, {"name":"password","value":"newstoreuser1234"}, {"name":"username","value":"newstoreuser"}]}'
```

### Using swift client to list files in the store_users bucket
```bash
swift -A http://127.0.0.1:8080/auth/v1.0 -U chris:chris1234 -K testing list store_users
```

### Destroy ChRIS Store dev environment

Stop and remove ChRIS Store services by running the make bash script from the repository source directory

```bash
./make.sh down
```

### REST API Documentation

Available [here](https://fnndsc.github.io/ChRIS_store).

Install Sphinx and the http extension (useful to document the REST API)
```
pip install Sphinx
pip install sphinxcontrib-httpdomain
```

Build the html documentation
```
cd docs/
make html
```


[license-badge]: https://img.shields.io/github/license/fnndsc/chris_store.svg
[last-commit-badge]: https://img.shields.io/github/last-commit/fnndsc/chris_store.svg

### Learn More

If you are interested in contributing or joining us, Check [here](http://chrisproject.org/join-us).
