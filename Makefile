# # Define variables
# IMAGE_NAME_API := fake_adjust
# IMAGE_NAME_TEST := python_testing
# IMAGE_TAG := latest
# ENV := dev
# GAR_LOCATION := us-central1-docker.pkg.dev/eighth-duality-457819-r4/data-ecr

# #Terraform Unit-tests
# terraform_unit_tests:
# 	@echo "Running terraform unit-tests..."
# 	@source .venv/bin/activate && \
# 	cd deploy && \
# 	( terraform init -backend-config=${ENV}.gcs.tfbackend || terraform init -backend-config=${ENV}.gcs.tfbackend -reconfigure) && \
# 	( terraform workspace select ${ENV} || terraform workspace new ${ENV} ) && \
# 	terraform plan -out=plan.out && \
# 	terraform show -json plan.out > plan.json && \
# 	cd ../test/unit_tests && \
# 	python3 -m unittest check_terraform_plan.py

# #Python Unit-tests
# python_unit_tests:
# 	@echo "Running python unit-tests..."
# 	@if ! docker build -t $(IMAGE_NAME_TEST):$(IMAGE_TAG) -f test/Dockerfile .; then \
#         echo "Docker image build failed."; \
# 		docker rmi -f $(IMAGE_NAME_TEST):$(IMAGE_TAG) || true; \
#         exit 1; \
# 	fi
# 	@echo "Cleaning up Docker resources..."
# 	@docker rmi $(IMAGE_NAME_TEST):$(IMAGE_TAG) || true

# #Fake Adjust API commands
# # Build the Docker image and Run API Image
# deploy_api:
# 	@echo "Building Docker image..."
# 	@if ! docker build fake_adjust_api --file fake_adjust_api/Dockerfile --tag $(GAR_LOCATION)/$(IMAGE_NAME_API):$(IMAGE_TAG); then \
#         echo "Docker image build failed."; \
# 		docker rmi -f $(IMAGE_NAME_API):$(IMAGE_TAG) || true; \
#         exit 1; \
# 	fi
# 	@echo "Pushing Docker container..."
# 	@if ! docker push $(GAR_LOCATION)/$(IMAGE_NAME_API):$(IMAGE_TAG); then \
#         echo "Docker container failed to be pushed."; \
#         exit 1; \
# 	fi
# 	@echo "Destroy existing version on Cloud Run if it exists"
# 	@gcloud run services delete fake_adjust_api \
# 		--region us-central1 \
# 		--platform managed --quiet || true
# 	@echo "Deploy new version to Cloud Run"
# 	@gcloud run deploy fake_adjust_api \
# 		--image $(GAR_LOCATION)/$(IMAGE_NAME_API):$(IMAGE_TAG) \
# 		--region us-central1 \
# 		--set-env-vars GCS_BUCKET=fass-${ENV},SERVICE_NAME=fake_adjust_api \
# 		--platform managed \
# 		--allow-unauthenticated


# # Clean up Docker resources
# clean_api:
# 	@echo "Destroy existing version on Cloud Run if it exists"
# 	@gcloud run services delete fake_adjust_api \
# 		--region us-central1 \
# 		--platform managed --quiet || true

# #FASS GCP Deployment
# #Build FASS
# deploy_fass:
# 	@echo "Deploying to GCP..."
# 	@cd deploy && \
# 	( terraform init -backend-config=${ENV}.gcs.tfbackend || terraform init -backend-config=${ENV}.gcs.tfbackend -reconfigure) && \
# 	( terraform workspace select ${ENV} || terraform workspace new ${ENV} ) && \
# 	terraform apply --parallelism=1

# #Clean FASS
# clean_fass:
# 	@echo "Cleaning up GCP resources..."
# 	@cd deploy && \
# 	( terraform init -backend-config=${ENV}.gcs.tfbackend || terraform init -backend-config=${ENV}.gcs.tfbackend -reconfigure) && \
# 	( terraform workspace select ${ENV} || terraform workspace new ${ENV} ) && \
# 	terraform destroy

# # Default target
# deploy-all: deploy_api deploy_fass
# test-all: terraform_unit_tests python_unit_tests

# .PHONY: deploy_api clean_api deploy_fass clean_fass terraform_unit_tests python_unit_tests deploy-all test-all