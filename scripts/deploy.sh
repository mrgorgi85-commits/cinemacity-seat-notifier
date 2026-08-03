#!/usr/bin/env bash
# Azure Infrastructure Deployment Script (Bash)
# Target Resource Group: rg-imaxon-prague
# Target Region: westeurope
# Pricing Tier: Consumption (Y1 Free Tier Plan)

set -e

RESOURCE_GROUP="rg-imaxon-prague"
LOCATION="westeurope"
RANDOM_SUFFIX=$((1000 + RANDOM % 9000))
STORAGE_ACCOUNT="stimaxonprd${RANDOM_SUFFIX}"
FUNCTION_APP="func-imaxon-prague-${RANDOM_SUFFIX}"
RATIO_THRESHOLD="0.016"

echo -e "\033[0;36m=====================================================\033[0m"
echo -e "\033[0;36mDeploying IMAX 70mm Ticket Monitor to Azure Functions\033[0m"
echo -e "\033[0;36m=====================================================\033[0m"

# 1. Create Resource Group
echo -e "\033[0;33mCreating Resource Group '${RESOURCE_GROUP}' in '${LOCATION}'...\033[0m"
az group create \
    --name "${RESOURCE_GROUP}" \
    --location "${LOCATION}"

# 2. Create Storage Account
echo -e "\033[0;33mCreating Storage Account '${STORAGE_ACCOUNT}'...\033[0m"
az storage account create \
    --name "${STORAGE_ACCOUNT}" \
    --location "${LOCATION}" \
    --resource-group "${RESOURCE_GROUP}" \
    --sku Standard_LRS

# 3. Create Function App (Linux Consumption Plan, Python 3.11)
echo -e "\033[0;33mCreating Function App '${FUNCTION_APP}'...\033[0m"
az functionapp create \
    --name "${FUNCTION_APP}" \
    --storage-account "${STORAGE_ACCOUNT}" \
    --consumption-plan-location "${LOCATION}" \
    --resource-group "${RESOURCE_GROUP}" \
    --os-type Linux \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4

# 4. Configure Application Settings
echo -e "\033[0;33mConfiguring Application Settings...\033[0m"
az functionapp config appsettings set \
    --name "${FUNCTION_APP}" \
    --resource-group "${RESOURCE_GROUP}" \
    --settings \
        "MONITOR_SCHEDULE=0 */1 * * * *" \
        "CINEMA_ID=1052" \
        "MOVIE_NAME=The Odyssey" \
        "AUDITORIUM_NAME=IMAX" \
        "TARGET_DATES=[\"2026-08-08\", \"2026-08-09\"]" \
        "ALLOWED_SHOWTIMES={\"2026-08-08\": [\"16:40\", \"20:30\"], \"2026-08-09\": [\"09:00\", \"12:50\", \"16:40\"]}" \
        "MOVIE_PAGE_URL=https://www.cinemacity.cz/films/odyssea/7268s2r#/buy-tickets-by-cinema?in-cinema={cinema_id}&at-date={date_str}" \
        "RATIO_THRESHOLD=${RATIO_THRESHOLD}" \
        "TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN" \
        "TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID"

echo -e "\033[0;32m=====================================================\033[0m"

echo -e "\033[0;32mInfrastructure setup complete!\033[0m"
echo -e "\033[0;32mFunction App Name: ${FUNCTION_APP}\033[0m"
echo -e "\033[0;32mResource Group:    ${RESOURCE_GROUP}\033[0m"
echo -e "\033[0;32m=====================================================\033[0m"
echo ""
echo "To publish function code run:"
echo "   zip -r app.zip function_app.py host.json requirements.txt"
echo -e "   \033[0;33maz functionapp deployment source config-zip -g ${RESOURCE_GROUP} -n ${FUNCTION_APP} --src ./app.zip\033[0m"
