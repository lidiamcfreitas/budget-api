#!/bin/bash
set -e

echo "Starting Cloud Run services deletion..."

# Function to delete Cloud Run service
delete_service() {
    local service_name=$1
    local region=$2
    
    echo "Deleting $service_name in region $region..."
    
    if gcloud run services delete "$service_name" \
        --region="$region" \
        --quiet 2>/dev/null; then
        echo "✓ Successfully deleted $service_name"
    else
        echo "⚠ Failed to delete $service_name"
        return 1
    fi
}

# Delete frontend
if ! delete_service "frontend" "europe-west1"; then
    echo "Error occurred while deleting frontend"
fi

# Delete backend
if ! delete_service "backend" "europe-west4"; then
    echo "Error occurred while deleting backend"
fi

echo "Cloud Run services deletion process completed."
