#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Azure Infrastructure Setup for ddukddak-recipe-server
# Usage: az login && bash infra/setup.sh
# =============================================================================

# ===== Configuration =====
RESOURCE_GROUP="rg-ddukddak"
LOCATION="koreacentral"

# PostgreSQL
PG_SERVER_NAME="pg-ddukddak"
PG_ADMIN_USER="ddukddakadmin"
PG_DB_NAME="ddukddak"
PG_SKU="Standard_B1ms"
PG_VERSION="16"

# Container Apps
CONTAINER_ENV_NAME="cae-ddukddak"
CONTAINER_APP_NAME="ca-ddukddak"

# GitHub (OIDC)
GITHUB_ORG="seongm1n"
GITHUB_REPO="ddukddak-recipe-server"
GITHUB_BRANCH="main"
SP_DISPLAY_NAME="sp-ddukddak-deploy"

# ===== Helper =====
log() { echo "===> $1"; }

# ===== Step 1: Resource Group =====
log "Creating Resource Group: $RESOURCE_GROUP ($LOCATION)"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

# ===== Step 2: PostgreSQL Flexible Server =====
read -rsp "Enter PostgreSQL admin password: " PG_ADMIN_PASSWORD
echo

log "Creating PostgreSQL Flexible Server: $PG_SERVER_NAME (B1ms, 12-month free)"
az postgres flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$PG_SERVER_NAME" \
  --location "$LOCATION" \
  --admin-user "$PG_ADMIN_USER" \
  --admin-password "$PG_ADMIN_PASSWORD" \
  --sku-name "$PG_SKU" \
  --tier "Burstable" \
  --version "$PG_VERSION" \
  --storage-size 32 \
  --public-access "0.0.0.0" \
  --output none 2>&1 || log "PostgreSQL Server already exists (skipping)"

log "Creating database: $PG_DB_NAME"
az postgres flexible-server db create \
  --resource-group "$RESOURCE_GROUP" \
  --server-name "$PG_SERVER_NAME" \
  --database-name "$PG_DB_NAME" \
  --output none 2>&1 || log "Database already exists (skipping)"

log "Ensuring firewall rule: AllowAllAzureServices"
az postgres flexible-server firewall-rule create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$PG_SERVER_NAME" \
  --rule-name "AllowAllAzureServices" \
  --start-ip-address "0.0.0.0" \
  --end-ip-address "0.0.0.0" \
  --output none 2>&1 || log "Firewall rule already exists (skipping)"

# ===== Step 3: Container Apps Environment =====
if az containerapp env show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_ENV_NAME" &>/dev/null; then
  log "Container Apps Environment already exists: $CONTAINER_ENV_NAME (skipping)"
else
  log "Creating Container Apps Environment: $CONTAINER_ENV_NAME"
  az containerapp env create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_ENV_NAME" \
    --location "$LOCATION" \
    --output none
fi

# ===== Step 4: Container App =====
log "Enter application secrets for Container App"

read -rsp "JWT_SECRET: " JWT_SECRET && echo
read -rsp "GEMINI_API_KEY: " GEMINI_API_KEY && echo
read -rsp "YOUTUBE_API_KEY: " YOUTUBE_API_KEY && echo
read -rp "GOOGLE_CLIENT_ID: " GOOGLE_CLIENT_ID
read -rp "KAKAO_CLIENT_ID: " KAKAO_CLIENT_ID

DATABASE_URL="postgresql+asyncpg://${PG_ADMIN_USER}:${PG_ADMIN_PASSWORD}@${PG_SERVER_NAME}.postgres.database.azure.com:5432/${PG_DB_NAME}?ssl=require"

if az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" &>/dev/null; then
  log "Container App already exists: $CONTAINER_APP_NAME — updating secrets and env vars"
  az containerapp secret set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_APP_NAME" \
    --secrets \
      "database-url=$DATABASE_URL" \
      "jwt-secret=$JWT_SECRET" \
      "gemini-api-key=$GEMINI_API_KEY" \
      "youtube-api-key=$YOUTUBE_API_KEY" \
    --output none

  az containerapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_APP_NAME" \
    --set-env-vars \
      "DATABASE_URL=secretref:database-url" \
      "JWT_SECRET=secretref:jwt-secret" \
      "GEMINI_API_KEY=secretref:gemini-api-key" \
      "YOUTUBE_API_KEY=secretref:youtube-api-key" \
      "APPLE_CLIENT_ID=com.ddukddak.recipe" \
      "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
      "KAKAO_CLIENT_ID=$KAKAO_CLIENT_ID" \
      "DEBUG=false" \
      "ACCESS_TOKEN_EXPIRE_MINUTES=60" \
      "REFRESH_TOKEN_EXPIRE_DAYS=30" \
    --output none
else
  log "Creating Container App: $CONTAINER_APP_NAME"
  az containerapp create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_APP_NAME" \
    --environment "$CONTAINER_ENV_NAME" \
    --image "mcr.microsoft.com/k8se/quickstart:latest" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 1 \
    --cpu 0.25 \
    --memory 0.5Gi \
    --secrets \
      "database-url=$DATABASE_URL" \
      "jwt-secret=$JWT_SECRET" \
      "gemini-api-key=$GEMINI_API_KEY" \
      "youtube-api-key=$YOUTUBE_API_KEY" \
    --env-vars \
      "DATABASE_URL=secretref:database-url" \
      "JWT_SECRET=secretref:jwt-secret" \
      "GEMINI_API_KEY=secretref:gemini-api-key" \
      "YOUTUBE_API_KEY=secretref:youtube-api-key" \
      "APPLE_CLIENT_ID=com.ddukddak.recipe" \
      "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
      "KAKAO_CLIENT_ID=$KAKAO_CLIENT_ID" \
      "DEBUG=false" \
      "ACCESS_TOKEN_EXPIRE_MINUTES=60" \
      "REFRESH_TOKEN_EXPIRE_DAYS=30" \
    --output none
fi

# ===== Step 5: Service Principal + OIDC =====
EXISTING_APP_ID=$(az ad app list --display-name "$SP_DISPLAY_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)

if [ -n "$EXISTING_APP_ID" ]; then
  log "Service Principal already exists: $SP_DISPLAY_NAME (skipping)"
  APP_ID="$EXISTING_APP_ID"
else
  log "Creating Service Principal for GitHub Actions OIDC"

  APP_ID=$(az ad app create \
    --display-name "$SP_DISPLAY_NAME" \
    --query appId -o tsv)

  az ad sp create --id "$APP_ID" --output none

  SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)
  SUBSCRIPTION_ID=$(az account show --query id -o tsv)

  az role assignment create \
    --assignee-object-id "$SP_OBJECT_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "Contributor" \
    --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    --output none

  log "Creating Federated Credential for branch: $GITHUB_BRANCH"
  az ad app federated-credential create \
    --id "$APP_ID" \
    --parameters '{
      "name": "github-actions-deploy",
      "issuer": "https://token.actions.githubusercontent.com",
      "subject": "repo:'"$GITHUB_ORG"'/'"$GITHUB_REPO"':ref:refs/heads/'"$GITHUB_BRANCH"'",
      "description": "GitHub Actions OIDC for '"$GITHUB_BRANCH"' branch deployment",
      "audiences": ["api://AzureADTokenExchange"]
    }' \
    --output none
fi

# ===== Step 6: Print GitHub Secrets =====
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
APP_URL=$(az containerapp show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_APP_NAME" \
  --query properties.configuration.ingress.fqdn -o tsv 2>/dev/null || echo "N/A")

echo ""
echo "============================================="
echo " Setup Complete!"
echo "============================================="
echo ""
echo "Container App URL: https://$APP_URL"
echo ""
echo "Add these as GitHub Repository Secrets:"
echo "  AZURE_CLIENT_ID=$APP_ID"
echo "  AZURE_TENANT_ID=$TENANT_ID"
echo "  AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
echo ""
echo "============================================="
