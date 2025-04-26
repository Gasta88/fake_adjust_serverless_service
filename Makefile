# Define variables
IMAGE_NAME_API := fake_adjust
IMAGE_TAG := latest
ENV := dev
GAR_LOCATION := us-central1-docker.pkg.dev/eighth-duality-457819-r4/data-ecr
REGION := us-central1
SERVICE_NAME := fass-api

#Fake Adjust API commands
# Build the Docker image and Run API Image
deploy_api:
	@echo "Building Docker image..."
	@if ! docker build fake_adjust_api --file fake_adjust_api/Dockerfile --tag $(GAR_LOCATION)/$(IMAGE_NAME_API):$(IMAGE_TAG); then \
        echo "Docker image build failed."; \
		docker rmi -f $(IMAGE_NAME_API):$(IMAGE_TAG) || true; \
        exit 1; \
	fi
	@echo "Pushing Docker container..."
	@if ! docker push $(GAR_LOCATION)/$(IMAGE_NAME_API):$(IMAGE_TAG); then \
        echo "Docker container failed to be pushed."; \
        exit 1; \
	fi
	@echo "Destroy existing version on Cloud Run if it exists"
	@gcloud run services delete ${SERVICE_NAME} \
		--region ${REGION} \
		--platform managed --quiet || true
	@echo "Deploy new version to Cloud Run"
	@gcloud run deploy ${SERVICE_NAME} \
		--image $(GAR_LOCATION)/$(IMAGE_NAME_API):$(IMAGE_TAG) \
		--region ${REGION} \
		--set-env-vars GCS_BUCKET=fass-${ENV},SERVICE_NAME=${SERVICE_NAME} \
		--platform managed \
		--allow-unauthenticated


# Clean up Docker resources
clean_api:
	@echo "Destroy existing version on Cloud Run if it exists"
	@gcloud run services delete ${SERVICE_NAME} \
		--region ${REGION} \
		--platform managed --quiet || true

#FASS GCP Deployment
#Build FASS
deploy_fass:
	@echo "Deploying to GCP..."
	@cd deploy && \
	( terraform init -backend-config=${ENV}.gcs.tfbackend || terraform init -backend-config=${ENV}.gcs.tfbackend -reconfigure) && \
	( terraform workspace select ${ENV} || terraform workspace new ${ENV} ) && \
	terraform apply --parallelism=1

#Clean FASS
clean_fass:
	@echo "Cleaning up GCP resources..."
	@cd deploy && \
	( terraform init -backend-config=${ENV}.gcs.tfbackend || terraform init -backend-config=${ENV}.gcs.tfbackend -reconfigure) && \
	( terraform workspace select ${ENV} || terraform workspace new ${ENV} ) && \
	terraform destroy

# Default target
deploy-all: deploy_api deploy_fass

.PHONY: deploy_api clean_api deploy_fass clean_fass deploy-all