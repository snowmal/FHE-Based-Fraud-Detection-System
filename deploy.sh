#!/bin/bash

#### CONFIGURATION ####
PROJECT_ID="server-carol"
REGION="us-east1"
FUNCTION_NAME="carol-listener"
BUCKET_NAME="alice_data"
SOURCE_DIR="./carol_function"
ENTRY_POINT="carol_entry"
REQUIREMENTS_FILE="$SOURCE_DIR/requirements.txt"

#### LOGIN & SETUP ####
echo "======================"
echo "[STEP] Authenticating with gcloud..."
gcloud auth login
echo "======================"
echo "[STEP] Setting project to '$PROJECT_ID'..."
gcloud config set project $PROJECT_ID

#### FETCH PROJECT NUMBER ####
PROJECT_ID_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUDFN_AGENT="service-${PROJECT_ID_NUMBER}@gcf-admin-robot.iam.gserviceaccount.com"

#### GRANT EVENTARC PERMISSIONS TO CLOUD FUNCTIONS SERVICE AGENT ####
echo "======================"
echo "[STEP] Granting Eventarc Admin role to Cloud Functions service agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-${PROJECT_ID_NUMBER}@gcf-admin-robot.iam.gserviceaccount.com" \
  --role="roles/eventarc.admin"

#### GRANT PUBSUB PUBLISHER TO GCS SERVICE ACCOUNT ####
GCS_SERVICE_ACCOUNT="service-${PROJECT_ID_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"
echo "======================"
echo "[STEP] Granting Pub/Sub Publisher role to GCS service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${GCS_SERVICE_ACCOUNT}" \
  --role="roles/pubsub.publisher"

#### INSTALL LOCAL DEPENDENCIES ####
echo "======================"
echo "[STEP] Installing Python dependencies locally..."
pip install -r "$REQUIREMENTS_FILE"

#### DEPLOY FUNCTION ####
echo "======================"
echo "[STEP] Deploying Cloud Function: $FUNCTION_NAME"
gcloud functions deploy $FUNCTION_NAME \
  --runtime python310 \
  --trigger-resource $BUCKET_NAME \
  --trigger-event google.storage.object.finalize \
  --entry-point $ENTRY_POINT \
  --memory=1GB \
  --timeout=540s \
  --allow-unauthenticated \
  --project=$PROJECT_ID \
  --gen2 \
  --region=$REGION \
  --source=$SOURCE_DIR
