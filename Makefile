# Define variables
IMAGE_NAME_API := fake_adjust
IMAGE_TAG_API := latest
ENV := dev

#Fake Adjust API commands
# Build the Docker image and Run API Image
deploy_api:
	@echo "Building Docker image..."
	@if ! docker build -t $(IMAGE_NAME_API):$(IMAGE_TAG_API) -f fake_adjust_api/Dockerfile fake_adjust_api; then \
        echo "Docker image build failed."; \
        exit 1; \
	fi
	@echo "Running Docker container..."
	@if ! docker run -d -p 8000:8000 $(IMAGE_NAME_API):$(IMAGE_TAG_API); then \
        echo "Docker container failed to start."; \
        exit 1; \
	fi
	@echo "Docker container is running. API is available at http://127.0.0.1:8000"


# Clean up Docker resources
clean_api:
	@echo "Cleaning up Docker resources..."
	@docker rm -f $(shell docker ps -aq -f ancestor=$(IMAGE_NAME_API):$(IMAGE_TAG_API)) || true
	@docker rmi $(IMAGE_NAME_API):$(IMAGE_TAG_API) || true

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
all: deploy_api deploy_fass

.PHONY: deploy_api clean_api deploy_fass clean_fass all