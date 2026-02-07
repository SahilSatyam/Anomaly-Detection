# =============================================================================
# GCP Cloud Run Deployment Script (PowerShell)
# Stock Anomaly Detection System
# =============================================================================
# Usage: .\deploy.ps1 -ProjectId "your-project-id" -Region "us-central1"
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDatabase,
    
    [Parameter(Mandatory=$false)]
    [string]$ExternalDbUrl  # Use external DB like Neon/Supabase
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "📝 $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Step { param($step, $msg) Write-Host "`n🔨 Step $step`: $msg" -ForegroundColor Magenta }

# Configuration
$BACKEND_SERVICE = "anomaly-backend"
$FRONTEND_SERVICE = "anomaly-frontend"
$DB_INSTANCE = "anomaly-db"
$DB_NAME = "stock_db"
$DB_USER = "stockuser"

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "🚀 GCP Cloud Run Deployment" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "❌ gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    Write-Host "   Download: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Get project ID
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        $ProjectId = Read-Host "Enter your GCP Project ID"
    }
}

Write-Info "Project: $ProjectId"
Write-Info "Region: $Region"

# Authenticate
Write-Info "Checking authentication..."
try {
    $null = gcloud auth print-access-token 2>$null
} catch {
    Write-Warning "Not authenticated. Opening browser for login..."
    gcloud auth login
}

# Set project
gcloud config set project $ProjectId

# Enable APIs
Write-Step 1 "Enabling required APIs..."
$apis = @(
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "containerregistry.googleapis.com",
    "secretmanager.googleapis.com"
)
gcloud services enable $apis
Write-Success "APIs enabled"

# =============================================================================
# Database Setup
# =============================================================================
$DATABASE_URL = ""

if ($ExternalDbUrl) {
    Write-Info "Using external database: $ExternalDbUrl"
    $DATABASE_URL = $ExternalDbUrl
} elseif (-not $SkipDatabase) {
    Write-Step 2 "Setting up Cloud SQL PostgreSQL..."
    
    # Check if instance exists
    $existingInstance = gcloud sql instances list --filter="name=$DB_INSTANCE" --format="value(name)" 2>$null
    
    if (-not $existingInstance) {
        Write-Info "Creating Cloud SQL instance (this takes 5-10 minutes)..."
        
        # Generate random password
        $DB_PASSWORD = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 20 | ForEach-Object {[char]$_})
        
        # Create instance (db-f1-micro is the smallest/cheapest)
        gcloud sql instances create $DB_INSTANCE `
            --database-version=POSTGRES_15 `
            --tier=db-f1-micro `
            --region=$Region `
            --storage-size=10GB `
            --storage-type=HDD `
            --database-flags=max_connections=50
        
        # Create database
        gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE
        
        # Create user
        gcloud sql users create $DB_USER --instance=$DB_INSTANCE --password=$DB_PASSWORD
        
        # Store password in Secret Manager
        $DB_PASSWORD | gcloud secrets create anomaly-db-password --data-file=- --replication-policy="automatic"
        
        Write-Success "Cloud SQL instance created"
        Write-Warning "Database password stored in Secret Manager: anomaly-db-password"
    } else {
        Write-Info "Using existing Cloud SQL instance"
        $DB_PASSWORD = gcloud secrets versions access latest --secret="anomaly-db-password" 2>$null
    }
    
    # Get connection name
    $CONNECTION_NAME = gcloud sql instances describe $DB_INSTANCE --format="value(connectionName)"
    Write-Info "Connection Name: $CONNECTION_NAME"
    
    # Build DATABASE_URL for Cloud SQL socket
    $DATABASE_URL = "postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"
} else {
    Write-Warning "Skipping database setup. Make sure to set DATABASE_URL manually."
}

# =============================================================================
# Deploy Backend
# =============================================================================
Write-Step 3 "Building and deploying Backend..."

$backendPath = Join-Path $PSScriptRoot "..\..\backend"
Push-Location $backendPath

try {
    # Build image
    Write-Info "Building Docker image..."
    gcloud builds submit --tag "gcr.io/$ProjectId/${BACKEND_SERVICE}:latest" .
    
    # Deploy to Cloud Run
    Write-Info "Deploying to Cloud Run..."
    
    $deployArgs = @(
        "run", "deploy", $BACKEND_SERVICE,
        "--image", "gcr.io/$ProjectId/${BACKEND_SERVICE}:latest",
        "--region", $Region,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--memory", "1Gi",
        "--cpu", "1",
        "--min-instances", "0",
        "--max-instances", "5",
        "--port", "8000",
        "--timeout", "300",
        "--set-env-vars", "LOG_LEVEL=INFO,LOG_FORMAT=json"
    )
    
    if ($DATABASE_URL) {
        $deployArgs += "--set-env-vars"
        $deployArgs += "DATABASE_URL=$DATABASE_URL"
    }
    
    if ($CONNECTION_NAME -and -not $ExternalDbUrl) {
        $deployArgs += "--add-cloudsql-instances"
        $deployArgs += $CONNECTION_NAME
    }
    
    & gcloud $deployArgs
    
    # Get backend URL
    $BACKEND_URL = gcloud run services describe $BACKEND_SERVICE --region=$Region --format="value(status.url)"
    Write-Success "Backend deployed: $BACKEND_URL"
    
} finally {
    Pop-Location
}

# =============================================================================
# Deploy Frontend
# =============================================================================
Write-Step 4 "Building and deploying Frontend..."

$frontendPath = Join-Path $PSScriptRoot "..\..\frontend"
Push-Location $frontendPath

try {
    # Build image with backend URL
    Write-Info "Building Docker image with REACT_APP_API_URL=$BACKEND_URL"
    gcloud builds submit `
        --tag "gcr.io/$ProjectId/${FRONTEND_SERVICE}:latest" `
        --substitutions="_REACT_APP_API_URL=$BACKEND_URL" .
    
    # Deploy to Cloud Run
    Write-Info "Deploying to Cloud Run..."
    gcloud run deploy $FRONTEND_SERVICE `
        --image "gcr.io/$ProjectId/${FRONTEND_SERVICE}:latest" `
        --region $Region `
        --platform managed `
        --allow-unauthenticated `
        --memory 256Mi `
        --cpu 1 `
        --min-instances 0 `
        --max-instances 2 `
        --port 80
    
    # Get frontend URL
    $FRONTEND_URL = gcloud run services describe $FRONTEND_SERVICE --region=$Region --format="value(status.url)"
    Write-Success "Frontend deployed: $FRONTEND_URL"
    
} finally {
    Pop-Location
}

# =============================================================================
# Update CORS
# =============================================================================
Write-Step 5 "Updating CORS settings..."
gcloud run services update $BACKEND_SERVICE `
    --region $Region `
    --update-env-vars "CORS_ORIGINS=$FRONTEND_URL"
Write-Success "CORS updated"

# =============================================================================
# Run Migrations
# =============================================================================
Write-Step 6 "Running database migrations..."
try {
    gcloud run jobs create run-migrations `
        --image "gcr.io/$ProjectId/${BACKEND_SERVICE}:latest" `
        --region $Region `
        --set-env-vars "DATABASE_URL=$DATABASE_URL" `
        --command "alembic" `
        --args "upgrade,head" `
        --max-retries 1 2>$null
} catch {
    Write-Info "Migration job already exists, executing..."
}

gcloud run jobs execute run-migrations --region $Region --wait
Write-Success "Migrations complete"

# =============================================================================
# Summary
# =============================================================================
Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Service URLs:" -ForegroundColor Cyan
Write-Host "   Frontend:  $FRONTEND_URL" -ForegroundColor White
Write-Host "   Backend:   $BACKEND_URL" -ForegroundColor White
Write-Host "   API Docs:  $BACKEND_URL/docs" -ForegroundColor White
Write-Host ""
if (-not $ExternalDbUrl -and -not $SkipDatabase) {
    Write-Host "🗄️ Database:" -ForegroundColor Cyan
    Write-Host "   Instance:  $DB_INSTANCE" -ForegroundColor White
    Write-Host "   Database:  $DB_NAME" -ForegroundColor White
}
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Visit $FRONTEND_URL to access your app"
Write-Host "   2. Check $BACKEND_URL/api/health for backend status"
Write-Host "   3. View logs: gcloud run logs read --service=$BACKEND_SERVICE --region=$Region"
Write-Host ""
Write-Host "💰 Cost Saving Tips:" -ForegroundColor Yellow
Write-Host "   - Cloud Run scales to zero when idle (free!)"
Write-Host "   - Pause Cloud SQL when not in use:"
Write-Host "     gcloud sql instances patch $DB_INSTANCE --activation-policy=NEVER"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
