#!/bin/sh
#
# -wvh- Build production RPMs using a three-step multistage Docker image (go + js --> final)
#

set -ex


### get git repo information for backend

pushd .
cd qvain-api

API_COMMIT_HASH=$(git rev-parse HEAD 2>/dev/null)
API_COMMIT_TAG=$(git describe --tags --always --dirty="-dev" 2>/dev/null)
API_COMMIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
API_VERSION=$(git describe --abbrev=0 2>/dev/null | sed 's/^v//')
API_REPO=$(git ls-remote --get-url 2>/dev/null)
popd


### get git repo information for frontend

pushd .
cd qvain-js

JS_COMMIT_HASH=$(git rev-parse HEAD 2>/dev/null)
JS_COMMIT_TAG=$(git describe --tags --always --dirty="-dev" 2>/dev/null)
JS_COMMIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
JS_VERSION=$(git describe --abbrev=0 2>/dev/null | sed 's/^v//')
JS_REPO=$(git ls-remote --get-url 2>/dev/null)
popd


### create output directory

if [ ! -d ./rpms/ ]; then
	mkdir -p rpms
fi


### build

docker build -t qvain-rpm -f docker/Dockerfile.rpms \
	--build-arg API_COMMIT_HASH=${API_COMMIT_HASH} \
	--build-arg API_COMMIT_TAG=${API_COMMIT_TAG} \
	--build-arg API_COMMIT_BRANCH=${API_COMMIT_BRANCH} \
	--build-arg API_VERSION=${API_VERSION} \
	--build-arg API_REPO=${API_REPO} \
	--build-arg JS_COMMIT_HASH=${JS_COMMIT_HASH} \
	--build-arg JS_COMMIT_TAG=${JS_COMMIT_TAG} \
	--build-arg JS_COMMIT_BRANCH=${JS_COMMIT_BRANCH} \
	--build-arg JS_VERSION=${JS_VERSION} \
	--build-arg JS_REPO=${JS_REPO} \
	.


### copy rpms out of image

docker run -it -u $(id -u):$(id -g) -v "$(pwd)"/rpms:/mnt --rm qvain-rpm sh -c 'cp -av /build/RPMS/*/qvain-* /mnt/'
