import os

# Main configuration for the Python script and FASS API interaction

config = {
    "base_url": os.environ.get(
        "FASS_API_URL", "https://fass-api-874544665874.us-central1.run.app/reporting"
    ),
    "project_id": os.environ.get("GCP_PROJECT_ID", "eighth-duality-457819-r4"),
}
