.SUFFIXES:
.PHONY: clean push image stage dist

PF9_VERSION ?= 1.0.0
BUILD_NUMBER ?= 0
GITHASH=$(shell git rev-parse --short HEAD)

SRCROOT = $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
BLDROOT = $(SRCROOT)/build
STAGE = $(BLDROOT)/container

$(shell mkdir -p $(STAGE))
ARTIFACTS=$(BLDROOT)/artifacts

MORS_DIST = $(STAGE)/mors-sdist.tgz
$(MORS_DIST): SETUP_ROOT = $(SRCROOT)

DISTS = $(MORS_DIST)

dist: $(DISTS)

Y2J = $(SRCROOT)/container/y2j.py
APP_METADATA_YAML = $(SRCROOT)/container/app_metadata.yaml
APP_METADATA_JSON = $(STAGE)/app_metadata.json

BUILD_ID := $(BUILD_NUMBER)
CONTAINER_IMG ?= quay.io/platform9/pf9-mors
IMAGE_TAG ?= $(or $(PF9_VERSION), "latest")-$(BUILD_ID)
BRANCH_NAME ?= $(or $(TEAMCITY_BUILD_BRANCH), $(TEAMCITY_BUILD_BRANCH), $(shell git symbolic-ref --short HEAD))

$(DISTS):
	cd $(SETUP_ROOT) && \
	rm -f dist/* && \
	python3 setup.py sdist && \
	cp -vf dist/* $@

stage-with-py-build-container: dist 
	cp -rv $(SRCROOT)/container/* $(STAGE)/
	pip3 install pyyaml
	python3 $(Y2J) $(APP_METADATA_YAML) > $(APP_METADATA_JSON)

stage:
	$(SRCROOT)/container/run-staging-in-container.sh

$(BLDROOT):
	mkdir -p $@

define image_build
	docker build -f Dockerfile --rm -t $(CONTAINER_IMG):$(1) \
		--build-arg BUILD_ID=$(BUILD_ID) \
		--build-arg VERSION=$(PF9_VERSION) \
		--build-arg BRANCH="$(BRANCH_NAME)" \
		--build-arg APP_METADATA=`cat $(APP_METADATA_JSON)` \
		$(STAGE)
	echo -ne "$(1)" >$(SRCROOT)/build/container-tag
endef

image: stage
	$(call image_build,$(IMAGE_TAG))

define image_push
	docker push $(CONTAINER_IMG):$(1) && \
	docker rmi $(CONTAINER_IMG):$(1) && \
	mkdir -p $(BLDROOT) && \
	echo -ne "$(1)" >$(BLDROOT)/container-tag
endef

push: image
	$(call image_push,$(IMAGE_TAG))

clean:
	rm -rf $(STAGE)
	images=$$(docker images -q -f dangling=true) && \
	if [ -n "$${images}" ]; then \
	    docker rmi $${images}; \
	fi
