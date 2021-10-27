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

http_code=$(
  curl -so /dev/null --head -w '%{http_code}' \
    -u "$CHRIS_STORE_USER" "$CHRIS_STORE_URL"
)

if [ "$http_code" != "200" ] ; then
  http_code=$(curl -so /dev/null --head -w '%{http_code}' $CHRIS_STORE_URL)
  if [ "$http_code" = "200" ]; then
    echo "CHRIS_STORE_USER is incorrect"
  else
    echo "cannot connect to $CHRIS_STORE_URL"
  fi
  exit 1
fi

# silence stderr for compatibility in Github Actions
color_red="$(tput setaf 1 2> /dev/null)"
color_blue="$(tput setaf 4 2> /dev/null)"
color_green="$(tput setaf 2 2> /dev/null)"
color_reset="$(tput sgr0 2> /dev/null)"

# e.g. FNNDSC/pl-simpledsapp
ghrepo=$1
ghurl="https://github.com/$ghrepo"

# docker image names must be all-lowercase
# FNNDSC/pl-ANTs -> fnndsc/pl-ants
dock_image=${ghrepo,,}
# ChRIS plugin names are case-sensitive
# FNNDSC/pl-ANTs -> pl-ANTs
plname=$(echo $ghrepo | sed 's/^.*\///')

dockerhub=$(curl -s "https://hub.docker.com/v2/repositories/$dock_image/tags/?ordering=last_updated")
recent_tag=$(
  echo "$dockerhub" \
    | jq -r '.results | map(select(.name != "latest" and .tag_status != "stale")) | first(.[]) | .name'
)

function quit_if_already_there () {
  existing_images=$(
    curl -s "${CHRIS_STORE_URL}plugins/search/?dock_image=$tagged_dock_image" \
      -H "accept:application/json"
  )

  if [ "$(jq -r '.count' <<< $existing_images)" -gt "0" ]; then
    existing_url="$(echo "$existing_images" | jq -r '.results[0].url')"
    printf "$color_blue%-60s %s$color_reset\n" "$tagged_dock_image" "$existing_url"
    exit 0
  fi
}

if [ -z "$recent_tag" ]; then
  stale_tag=$(
    echo "$dockerhub" \
      | jq -r '.results | map(select(.name != "latest")) | first(.[]) | .name'
  )
  if [ -n "$stale_tag" ]; then
    tagged_dock_image=$dock_image:$stale_tag
    quit_if_already_there
    printf "$color_red%-60s %s$color_reset\n" "$tagged_dock_image"  "stale"
  else
    printf "$color_red%-60s %s$color_reset\n" "$dock_image"  "no Dockerhub tags"
  fi
  exit 0
fi

tagged_dock_image=$dock_image:$recent_tag
quit_if_already_there

time_pull_start=$(date +%s)
docker pull -q $tagged_dock_image > /dev/null
time_pull_end=$(date +%s)

descriptor_file=$(mktemp --suffix .json)
script=$(docker inspect --format '{{ (index .Config.Cmd 0)}}' $tagged_dock_image)
docker run --rm $tagged_dock_image $script --json > $descriptor_file 2> /dev/null

# remove large, newly pulled images
if [ "$(($time_pull_end-$time_pull_start))" -gt '3' ]; then
  docker rmi $tagged_dock_image > /dev/null 2>&1 &
fi

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
  uploaded_url=$(jq -r '.collection.items[0].href' <<< "$res")
  if [ "$uploaded_url" != 'null' ]; then
    printf "$color_green%-60s %s$color_reset\n" "$tagged_dock_image" "$uploaded_url"
  else
    error_msg="$(jq '.collection.error' <<< "$res")"
    if [ "$error_msg" = 'null' ]; then
      error_msg="unknown error"
    fi
  fi
else
  error_msg="network/request error"
fi

if [ -n "$error_msg" ]; then
  printf "$color_red%-60s %s$color_reset\n" "$tagged_dock_image" "$res"
fi

wait
exit $result
