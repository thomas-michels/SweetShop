include ./.env

build:
	docker build -t sweet-shop-api --no-cache .

run:
	docker run --env-file .env --network ${DEV_CONTAINER_NETWORK} -p ${APPLICATION_PORT}:8000 --name sweet-shop-api -d sweet-shop-api
