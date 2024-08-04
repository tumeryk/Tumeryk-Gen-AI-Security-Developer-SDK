SHELL = /usr/bin/env bash
IMAGE=831603647943.dkr.ecr.us-west-2.amazonaws.com

all: build 
test: build

build:
	docker buildx build --platform=linux/x86_64 -t proxy -f Dockerfile .

