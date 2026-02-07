# 🌐 GCP Cloud Run Deployment Guide

Deploy the Stock Anomaly Detection System to Google Cloud Platform.

## 💰 Cost Estimate

| Service                 | Free Tier         | Estimated Monthly Cost      |
| ----------------------- | ----------------- | --------------------------- |
| Cloud Run (Backend)     | 2M requests/month | **$0** (scales to zero)     |
| Cloud Run (Frontend)    | 2M requests/month | **$0** (scales to zero)     |
| Cloud SQL (PostgreSQL)  | None              | **~$9/month** (db-f1-micro) |
| Container Registry      | 0.5 GB free       | **$0**                      |
| **Total (low traffic)** |                   | **~$9/month**               |

> 💡 **Tip**: For truly free hosting, use [Supabase](https://supabase.com) or [Neon](https://neon.tech) for PostgreSQL (free tier) instead of Cloud SQL.

---

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed: [Install Guide](https://cloud.google.com/sdk/docs/install)
3. **Docker** installed locally (for testing)

### Install gcloud CLI (Windows)

```powershell
# Download and run installer
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:TEMP\GoogleCloudSDKInstaller.exe")
& "$env:TEMP\GoogleCloudSDKInstaller.exe"
```

---

## 🚀 Quick Deploy (Automated)

### Option 1: Using Deploy Script (Linux/Mac/WSL)

```bash
# Make executable
chmod +x deploy/gcp/deploy.sh

# Deploy (replace with your project ID)
./deploy/gcp/deploy.sh your-gcp-project-id us-central1
```

### Option 2: Manual Deployment (Windows/Any)

Follow the step-by-step guide below.

---

## 📖 Step-by-Step Manual Deployment

### Step 1: Initial Setup

```powershell
# Login to GCP
gcloud auth login

# Create new project (or use existing)
gcloud projects create anomaly-detection-2026 --name="Anomaly Detection"

# Set as active project
gcloud config set project anomaly-detection-2026

# Enable billing (required for Cloud Run)
# Do this in the Console: https://console.cloud.google.com/billing

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com containerregistry.googleapis.com secretmanager.googleapis.com
```

### Step 2: Create Cloud SQL Database

```powershell
# Create PostgreSQL instance (smallest tier)
gcloud sql instances create anomaly-db `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=us-central1 `
    --storage-size=10GB `
    --storage-type=HDD

# Set password (save this!)
$DB_PASSWORD = "YourSecurePassword123!"
gcloud sql users set-password postgres --instance=anomaly-db --password=$DB_PASSWORD

# Create database
gcloud sql databases create stock_db --instance=anomaly-db

# Create app user
gcloud sql users create stockuser --instance=anomaly-db --password=$DB_PASSWORD

# Get connection name (you'll need this)
gcloud sql instances describe anomaly-db --format="value(connectionName)"
# Output: your-project:us-central1:anomaly-db
```

### Step 3: Deploy Backend

```powershell
cd backend

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/anomaly-detection-2026/anomaly-backend:latest .

# Get your connection name from Step 2
$CONNECTION_NAME = "anomaly-detection-2026:us-central1:anomaly-db"
$DB_PASSWORD = "YourSecurePassword123!"

# Deploy to Cloud Run
gcloud run deploy anomaly-backend `
    --image gcr.io/anomaly-detection-2026/anomaly-backend:latest `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --add-cloudsql-instances $CONNECTION_NAME `
    --set-env-vars "DATABASE_URL=postgresql://stockuser:$DB_PASSWORD@/stock_db?host=/cloudsql/$CONNECTION_NAME,LOG_LEVEL=INFO,LOG_FORMAT=json" `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5 `
    --port 8000 `
    --timeout 300

# Get the backend URL
gcloud run services describe anomaly-backend --region=us-central1 --format="value(status.url)"
# Output: https://anomaly-backend-xxxxx-uc.a.run.app
```

### Step 4: Deploy Frontend

```powershell
cd ../frontend

# Set the backend URL from previous step
$BACKEND_URL = "https://anomaly-backend-xxxxx-uc.a.run.app"

# Update the Dockerfile to use build arg (already configured)
# Build and push
gcloud builds submit `
    --tag gcr.io/anomaly-detection-2026/anomaly-frontend:latest `
    --substitutions="_REACT_APP_API_URL=$BACKEND_URL" .

# Deploy to Cloud Run
gcloud run deploy anomaly-frontend `
    --image gcr.io/anomaly-detection-2026/anomaly-frontend:latest `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --memory 256Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2 `
    --port 80

# Get frontend URL
gcloud run services describe anomaly-frontend --region=us-central1 --format="value(status.url)"
# Output: https://anomaly-frontend-xxxxx-uc.a.run.app
```

### Step 5: Run Database Migrations

```powershell
# Connect to Cloud SQL via Cloud Run
gcloud run jobs create run-migrations `
    --image gcr.io/anomaly-detection-2026/anomaly-backend:latest `
    --region us-central1 `
    --add-cloudsql-instances $CONNECTION_NAME `
    --set-env-vars "DATABASE_URL=postgresql://stockuser:$DB_PASSWORD@/stock_db?host=/cloudsql/$CONNECTION_NAME" `
    --command "alembic" `
    --args "upgrade,head"

# Execute migration job
gcloud run jobs execute run-migrations --region us-central1 --wait
```

---

## 🆓 Free Alternative: Use External PostgreSQL

To avoid Cloud SQL costs (~$9/month), use a free PostgreSQL provider:

### Option A: Neon (Recommended)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Use it directly in Cloud Run:

```powershell
# Deploy with Neon database
gcloud run deploy anomaly-backend `
    --image gcr.io/anomaly-detection-2026/anomaly-backend:latest `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --set-env-vars "DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require,LOG_LEVEL=INFO" `
    --memory 1Gi `
    --min-instances 0 `
    --max-instances 5 `
    --port 8000
```

### Option B: Supabase

1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database → Connection string
4. Use it in Cloud Run deployment

---

## 🔧 Useful Commands

```powershell
# View logs
gcloud run logs read --service=anomaly-backend --region=us-central1 --limit=50

# View service status
gcloud run services describe anomaly-backend --region=us-central1

# Update environment variables
gcloud run services update anomaly-backend --region=us-central1 --set-env-vars "NEW_VAR=value"

# Scale instances
gcloud run services update anomaly-backend --region=us-central1 --min-instances=1

# Delete services (to stop billing)
gcloud run services delete anomaly-backend --region=us-central1
gcloud run services delete anomaly-frontend --region=us-central1

# Pause Cloud SQL (to save costs when not in use)
gcloud sql instances patch anomaly-db --activation-policy=NEVER

# Resume Cloud SQL
gcloud sql instances patch anomaly-db --activation-policy=ALWAYS
```

---

## 🔐 Security Best Practices

1. **Store secrets in Secret Manager**:

```powershell
# Create secret
echo -n "your-db-password" | gcloud secrets create db-password --data-file=-

# Use in Cloud Run
gcloud run services update anomaly-backend `
    --set-secrets="DATABASE_PASSWORD=db-password:latest"
```

2. **Restrict access** (if needed):

```powershell
# Remove public access
gcloud run services update anomaly-backend --no-allow-unauthenticated

# Add IAM user
gcloud run services add-iam-policy-binding anomaly-backend `
    --member="user:email@example.com" `
    --role="roles/run.invoker"
```

---

## 🔄 CI/CD with Cloud Build

The included `cloudbuild.yaml` enables automatic deployment on git push:

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click "Create Trigger"
3. Connect your GitHub repository
4. Set trigger to run on push to `main`
5. Set substitution variables:
   - `_REGION`: `us-central1`
   - `_DATABASE_URL`: Your connection string
   - `_CLOUD_SQL_CONNECTION`: Your Cloud SQL connection name
   - `_BACKEND_URL`: Backend service URL

---

## 📊 Monitoring

```powershell
# View metrics in console
# https://console.cloud.google.com/run

# Set up alerts
gcloud monitoring alert-policies create `
    --display-name="High Error Rate" `
    --condition="..."
```

---

## 🛠️ Troubleshooting

### Cold Start Latency

Cloud Run has cold starts when scaling from 0. To minimize:

```powershell
# Keep 1 instance warm (costs ~$5/month)
gcloud run services update anomaly-backend --min-instances=1
```

### Database Connection Issues

```powershell
# Check Cloud SQL is running
gcloud sql instances list

# Test connection from Cloud Shell
gcloud sql connect anomaly-db --user=stockuser
```

### Build Failures

```powershell
# View build logs
gcloud builds list
gcloud builds log BUILD_ID
```

---

## 📞 Support

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Pricing Calculator](https://cloud.google.com/products/calculator)
