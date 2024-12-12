#!/bin/bash -x

ROOT_PATH=$(dirname $(dirname $(cd $(dirname ${BASH_SOURCE[0]:-$0}); pwd)))
ENV_FILE=${ROOT_PATH}/env.json

set_val_from_json_by_key()
{
	local v
	if [ "$2" != "" ]; then
		# -A 5 のところは、 env.json の子要素 (BASE/APISERVER/BATCH など) の深さに合わせる
		eval 'v=$(cat $ENV_FILE | grep -A 5 $2 | awk -F\\\" "/$1/{print \$4}")'
		eval "$2_$1=$v"
	else
		eval 'v=$(awk -F\\\" "/$1/{print \$4}" $ENV_FILE)'
		eval "$1=$v"
	fi
}

login_acr()
{
	az acr login --name $AZURE_CONTAINER_REGISTRY
}

build_docker_image()
{
	# python バージョンはいったん固定
	DOCKER_BUILDKIT=1 docker build \
	--build-arg registry=${AZURE_CONTAINER_REGISTRY} \
	--build-arg py_version=3.8.0-slim \
	--build-arg build_user=${HOST_USER}  \
	-t ${AZURE_CONTAINER_REGISTRY}.azurecr.io/${1}:${2} \
	-f ${ROOT_PATH}${3}Dockerfile${4} \
	${ROOT_PATH}${3}

}

run_api_server_locally()
{
	echo -e "running docker image locally for testing...\n"
	IMAGE_ID=$(docker images | grep ${AZURE_CONTAINER_REGISTRY}.azurecr.io/$APISERVER_IMAGE | grep $APISERVER_TAG | awk '{print $3}')

	if [ ! -z "$1" ]; then
		echo "Start Docker Container with CMD 'python $1'"
		docker run -d -p $SERVER_PORT_LOCAL:$SERVER_PORT_LOCAL $IMAGE_ID $1
	else
		echo "Start Docker Container by default CMD"
		docker run -d -p $SERVER_PORT_LOCAL:$SERVER_PORT_LOCAL $IMAGE_ID
	fi

	CONTAINER_ID=$(docker container ls | grep $IMAGE_ID | awk '{print $1}')
	sleep 10
	curl localhost:${SERVER_PORT_LOCAL}${API_LOCAL_ENDPOINT}
}

push_image_if_test_succeeded()
{
	local overridecmd
	eval "overridecmd=$3"
	run_api_server_locally $overridecmd

	# TODO Batch イメージをどうやってテストするか考える
	if [ $? = 0 ]; then
		docker kill $(docker ps | grep $IMAGE_ID | awk '{print $1}')

		echo -e "Local tesing has successfully finieshed. Push Docker Image to ACR\n"
		docker push ${AZURE_CONTAINER_REGISTRY}.azurecr.io/${BASE_IMAGE}:${BASE_TAG}
		docker push ${AZURE_CONTAINER_REGISTRY}.azurecr.io/${APISERVER_IMAGE}:${APISERVER_TAG}
		docker push ${AZURE_CONTAINER_REGISTRY}.azurecr.io/${BATCH_IMAGE}:${BATCH_TAG}
	else
		echo -e "Local testing failed. exit wit1"
		exit 1
	fi

}

# 事前準備
set_val_from_json_by_key HOST_USER
set_val_from_json_by_key AZURE_CONTAINER_REGISTRY
set_val_from_json_by_key SERVER_PORT_LOCAL
set_val_from_json_by_key API_LOCAL_ENDPOINT

set_val_from_json_by_key IMAGE BASE
set_val_from_json_by_key TAG BASE
set_val_from_json_by_key REL_PATH BASE
set_val_from_json_by_key FILE_SUFFIX BASE

set_val_from_json_by_key IMAGE APISERVER
set_val_from_json_by_key TAG APISERVER
set_val_from_json_by_key REL_PATH APISERVER
set_val_from_json_by_key FILE_SUFFIX APISERVER

set_val_from_json_by_key IMAGE BATCH
set_val_from_json_by_key TAG BATCH
set_val_from_json_by_key REL_PATH BATCH
set_val_from_json_by_key FILE_SUFFIX BATCH

# ACR にログイン
login_acr

# 必要な Docker イメージを build
build_docker_image $BASE_IMAGE $BASE_TAG $BASE_REL_PATH $BASE_FILE_SUFFIX
build_docker_image $APISERVER_IMAGE $APISERVER_TAG $APISERVER_REL_PATH $APISERVER_FILE_SUFFIX
build_docker_image $BATCH_IMAGE $BATCH_TAG $BATCH_REL_PATH $BATCH_FILE_SUFFIX

# ローカルでの動作確認・ACR への push
push_image_if_test_succeeded