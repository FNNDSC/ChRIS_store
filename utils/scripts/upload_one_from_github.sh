#!/bin/bash
# given a plugin repository name (e.g. fnndsc/pl-app)
# get the most recently pushed tag* from dockerhub
# and upload it into ChRIS_store
# caveat: stale images and ":latest" are not considered.
# most recently pushed tag might not be the latest version,
# for example in the case where v2.0 is latest by version but
# the most recent push was a backported hotfix to v1.1

CHRIS_STORE_URL="${CHRIS_STORE_URL:-https://chrisstore.co/api/v1/}"
CHRIS_STORE_USER="${CHRIS_STORE_USER:-chris:chris1234}"

# e.g. FNNDSC/pl-simpledsapp
ghrepo=$1
ghurl="https://github.com/$ghrepo"

# FNNDSC/pl-simpledsapp -> fnndsc/pl-simpledsapp
dock_image=${ghrepo,,}
# FNNDSC/pl-simpledsapp -> pl-simpledsapp
plname=$(echo $ghrepo | sed 's/^.*\///')

recent_tag=$(
  curl -s "https://hub.docker.com/v2/repositories/$dock_image/tags/?ordering=last_updated" \
    | jq -r '.results | map(select(.name != "latest" and .tag_status != "stale")) | first(.[]) | .name'
)

if [ -z "$recent_tag" ]; then
  printf "$(tput setaf 1)%-60s %s$(tput sgr0)\n" "$dock_image" "no Dockerhub tags"
  exit 1
fi

tagged_dock_image=$dock_image:$recent_tag

existing_images=$(
  curl -s "${CHRIS_STORE_URL}plugins/search/?dock_image=$tagged_dock_image" \
    -H "accept:application/json"
)

if [ "$(echo "$existing_images" | jq -r '.count')" -gt "0" ]; then
  existing_url="$(echo "$existing_images" | jq -r '.results[0].url')"
  printf "$(tput setaf 4)%-60s %s$(tput sgr0)\n" "$tagged_dock_image" "$existing_url"
  exit 0
fi

descriptor_file=$(mktemp --suffix .json)
docker pull -q $tagged_dock_image > /dev/null
script=$(docker inspect --format '{{ (index .Config.Cmd 0)}}' $tagged_dock_image)
docker run --rm $dock_image $script --json > $descriptor_file 2> /dev/null
docker rmi $tagged_dock_image > /dev/null 2>&1 &

res=$(
  curl -s -u "$CHRIS_STORE_USER" "${CHRIS_STORE_URL}plugins/" \
    -F "name=$plname" \
    -F "dock_image=$tagged_dock_image"  \
    -F "descriptor_file=@$descriptor_file" \
    -F "public_repo=$ghurl"
)
result=$?
rm $descriptor_file

if [ "$result" = "0" ]; then
  uploaded_url=$(echo $res | jq -r '.collection.items[0].href')
  printf "$(tput setaf 2)%-60s %s$(tput sgr0)\n" "$tagged_dock_image" "$uploaded_url"
else
  printf "$(tput setaf 1)%-60s %s$(tput sgr0)\n" "$tagged_dock_image" "$res"
fi

wait
exit $result
