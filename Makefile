# Local helpers for the Fake Adjust Serverless Service.
#
# The stage-1 Fake Adjust API lives in a separate repository:
#   https://github.com/Gasta88/fake_adjust
# Deploy it there first, then set FASS_API_URL when applying Terraform.

ENV ?= dev
TF_DIR := deploy
TF_BACKEND := $(notdir $(ENV).gcs.tfbackend)
WORKSPACE ?= $(ENV)

.PHONY: help test plan deploy docs

help:
	@echo "make test                 Run the Python unit tests"
	@echo "make plan  [ENV=dev]      Terraform init + plan in the $(ENV) workspace"
	@echo "make deploy [ENV=prod]    Terraform init + apply in the $(ENV) workspace"
	@echo "make docs                 Regenerate the architecture diagram"

test:
	python -m unittest discover -s orchestrator_func/test
	python -m unittest discover -s executor_func/test

plan:
	cd $(TF_DIR) && terraform init -backend-config=$(TF_BACKEND)
	cd $(TF_DIR) && terraform workspace select $(WORKSPACE) || terraform workspace new $(WORKSPACE)
	cd $(TF_DIR) && terraform plan

deploy:
	cd $(TF_DIR) && terraform init -backend-config=$(TF_BACKEND)
	cd $(TF_DIR) && terraform workspace select $(WORKSPACE) || terraform workspace new $(WORKSPACE)
	cd $(TF_DIR) && terraform apply

docs:
	cd docs && pip install -r requirements.txt && python infrastructure.py
