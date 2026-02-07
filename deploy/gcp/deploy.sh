#!/bin/bash
# =============================================================================
# GCP Cloud Run Deployment Script
# Stock Anomaly Detection System
# =============================================================================
# Usage: ./deploy.sh [PROJECT_ID] [REGION]
# Example: ./deploy.sh my-gcp-project us-central1
# =============================================================================

set -e

# Configuration
PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-"us-central1"}
BACKEND_SERVICE="anomaly-backend"
FRONTEND_SERVICE="anomaly-frontend"
DB_INSTANCE="anomaly-db"
DB_NAME="stock_db"
DB_USER="stockuser"

echo "=========================================="
echo "🚀 GCP Cloud Run Deployment"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Authenticate if needed
echo "📝 Checking authentication..."
gcloud auth print-access-token > /dev/null 2>&1 || gcloud auth login

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# =============================================================================
# Step 1: Create Cloud SQL Instance (if not exists)
# =============================================================================
echo ""
echo "📦 Step 1: Setting up Cloud SQL PostgreSQL..."

if ! gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating Cloud SQL instance..."
    
    # Generate random password
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
    
    # Create instance (smallest tier for cost savings)
    gcloud sql instances create $DB_INSTANCE \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-size=10GB \
        --storage-type=HDD \
        --no-assign-ip \
        --network=default
    
    # Set root password
    gcloud sql users set-password postgres \
        --instance=$DB_INSTANCE \
        --password="$DB_PASSWORD"
    
    # Create application user
    gcloud sql users create $DB_USER \
        --instance=$DB_INSTANCE \
        --password="$DB_PASSWORD"
    
    # Create database
    gcloud sql databases create $DB_NAME \
        --instance=$DB_INSTANCE
    
    # Store password in Secret Manager
    echo -n "$DB_PASSWORD" | gcloud secrets create anomaly-db-password \
        --data-file=- \
        --replication-policy="automatic"
    
    echo "✅ Cloud SQL instance created"
    echo "⚠️  Database password stored in Secret Manager: anomaly-db-password"
else
    echo "✅ Cloud SQL instance already exists"
    DB_PASSWORD=$(gcloud secrets versions access latest --secret="anomaly-db-password" 2>/dev/null || echo "")
fi

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE --format='value(connectionName)')
echo "Connection Name: $CONNECTION_NAME"

# =============================================================================
# Step 2: Build and Deploy Backend
# =============================================================================
echo ""
echo "🔨 Step 2: Building and deploying Backend..."

cd backend

# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest .

# Deploy to Cloud Run
gcloud run deploy $BACKEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME,LOG_LEVEL=INFO,LOG_FORMAT=json" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --port 8000 \
    --timeout 300

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --format='value(status.url)')
echo "✅ Backend deployed: $BACKEND_URL"

cd ..

# =============================================================================
# Step 3: Build and Deploy Frontend
# =============================================================================
echo ""
echo "🔨 Step 3: Building and deploying Frontend..."

cd frontend

# Build with backend URL
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest \
    --substitutions=_REACT_APP_API_URL="$BACKEND_URL" .

# Deploy to Cloud Run
gcloud run deploy $FRONTEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 2 \
    --port 80

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format='value(status.url)')
echo "✅ Frontend deployed: $FRONTEND_URL"

cd ..

# =============================================================================
# Step 4: Update Backend CORS (optional)
# =============================================================================
echo ""
echo "🔧 Step 4: Updating CORS settings..."

gcloud run services update $BACKEND_SERVICE \
    --region $REGION \
    --update-env-vars "CORS_ORIGINS=$FRONTEND_URL"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  $FRONTEND_URL"
echo "   Backend:   $BACKEND_URL"
echo "   API Docs:  $BACKEND_URL/docs"
echo ""
echo "🗄️ Database:"
echo "   Instance:  $DB_INSTANCE"
echo "   Database:  $DB_NAME"
echo "   User:      $DB_USER"
echo ""
echo "💡 Next Steps:"
echo "   1. Visit $FRONTEND_URL to access your app"
echo "   2. Check $BACKEND_URL/api/health for backend status"
echo "   3. View logs: gcloud run logs read --service=$BACKEND_SERVICE --region=$REGION"
echo ""
echo "💰 Cost Optimization Tips:"
echo "   - With min-instances=0, you pay nothing when idle"
echo "   - Cloud SQL db-f1-micro: ~\$9/month"
echo "   - Consider pausing SQL instance when not in use"
echo ""
echo "=========================================="
