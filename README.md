# ![ChRIS logo](https://github.com/FNNDSC/ChRIS_store/blob/master/docs/assets/logo_chris.png) ChRIS_store
[![Build Status](https://travis-ci.org/FNNDSC/ChRIS_store.svg?branch=master)](https://travis-ci.org/FNNDSC/ChRIS_store)
![License][license-badge]
![Last Commit][last-commit-badge]

Back end for ChRIS Store. This is a Django-MySQL project.

## ChRIS Store development and testing

### Abstract

This page describes how to quickly get the set of services comprising the backend up and running for development and how to run the automated tests.

### Preconditions

#### Install latest Docker and Docker Compose. Currently tested platforms
* ``Ubuntu 16.04+ and MAC OS X 10.11+``
* ``Docker 17.04.0+``
* ``Docker Compose 1.10.0+``

#### On a Linux machine make sure to add your computer user to the ``docker`` group 

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

#### Checkout the Github repo
```bash
git clone https://github.com/FNNDSC/ChRIS_store.git
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
./make.sh up
```
All the steps performed by the above script are properly documented in the script itself. 

After running this script all the automated tests should have successfully run and a Django development server should be running in interactive mode in this terminal.

### Rerun automated tests after modifying source code

Open another terminal and run 
```bash
docker ps
```
Find out from the previous output the name of the container running the Django server in interactive mode (usually *chris_store_chris_store_dev_run_1*) and run the Unit tests and Integration tests within that container. For instance to run only the Unit tests:

```bash
docker exec -it chris_store_chris_store_dev_run_1 python manage.py test --exclude-tag integration
```

To run only the Integration tests:

```bash
docker exec -it chris_store_chris_store_dev_run_1 python manage.py test --tag integration
```

To run all the tests:

```bash
docker exec -it chris_store_chris_store_dev_run_1 python manage.py test
```

### Check code coverage of the automated tests
Make sure the **store_backend/** dir is world writable. Then type:

```bash
docker exec -it chris_store_chris_store_dev_run_1 coverage run --source=plugins,users manage.py test
docker exec -it chris_store_chris_store_dev_run_1 coverage report
```

### Using [HTTPie](https://httpie.org/) to play with the REST API 

#### A simple GET request:
```bash
http http://localhost:8010/api/v1/
```

#### A simple POST request to register a new plugin app in the store:
First save the plugin representation json file by running the plugin with the `--savejson` flag:
```bash
docker run --rm -v /tmp/json:/json fnndsc/pl-simplefsapp simplefsapp.py --savejson /json
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
