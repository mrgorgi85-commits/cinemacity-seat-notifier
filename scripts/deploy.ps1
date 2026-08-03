# Azure Infrastructure Deployment Script (PowerShell)
# Target Resource Group: rg-imaxon-prague
# Target Region: westeurope
# Pricing Tier: Consumption (Y1 Free Tier Plan)

$ResourceGroup  = "rg-imaxon-prague"
$Location       = "westeurope"
$RandomSuffix   = (Get-Random -Minimum 1000 -Maximum 9999)
$StorageAccount = "stimaxonprd$RandomSuffix"
$FunctionApp    = "func-imaxon-prague-$RandomSuffix"
$RatioThreshold = "0.016"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Deploying IMAX 70mm Ticket Monitor to Azure Functions" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Create Resource Group
Write-Host "Creating Resource Group '$ResourceGroup' in '$Location'..." -ForegroundColor Yellow
az group create `
    --name $ResourceGroup `
    --location $Location

# 2. Create Storage Account
Write-Host "Creating Storage Account '$StorageAccount'..." -ForegroundColor Yellow
az storage account create `
    --name $StorageAccount `
    --location $Location `
    --resource-group $ResourceGroup `
    --sku Standard_LRS

# 3. Create Function App (Linux Consumption Plan, Python 3.11)
Write-Host "Creating Function App '$FunctionApp'..." -ForegroundColor Yellow
az functionapp create `
    --name $FunctionApp `
    --storage-account $StorageAccount `
    --consumption-plan-location $Location `
    --resource-group $ResourceGroup `
    --os-type Linux `
    --runtime python `
    --runtime-version 3.11 `
    --functions-version 4

# 4. Configure Application Settings
Write-Host "Configuring Application Settings..." -ForegroundColor Yellow
az functionapp config appsettings set `
    --name $FunctionApp `
    --resource-group $ResourceGroup `
    --settings `
        "MONITOR_SCHEDULE=0 */1 * * * *" `
        "CINEMA_ID=1052" `
        "MOVIE_NAME=The Odyssey" `
        "AUDITORIUM_NAME=IMAX" `
        "TARGET_DATES=[\"2026-08-08\", \"2026-08-09\"]" `
        "ALLOWED_SHOWTIMES={\"2026-08-08\": [\"16:40\", \"20:30\"], \"2026-08-09\": [\"09:00\", \"12:50\", \"16:40\"]}" `
        "MOVIE_PAGE_URL=https://www.cinemacity.cz/films/odyssea/7268s2r#/buy-tickets-by-cinema?in-cinema={cinema_id}&at-date={date_str}" `
        "RATIO_THRESHOLD=$RatioThreshold" `
        "TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN" `
        "TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID"

Write-Host "=====================================================" -ForegroundColor Green

Write-Host "Infrastructure setup complete!" -ForegroundColor Green
Write-Host "Function App Name: $FunctionApp" -ForegroundColor Green
Write-Host "Resource Group:    $ResourceGroup" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To publish function code run:" -ForegroundColor White
Write-Host "   Compress-Archive -Path function_app.py, host.json, requirements.txt -DestinationPath app.zip -Force" -ForegroundColor Yellow
Write-Host "   az functionapp deployment source config-zip -g $ResourceGroup -n $FunctionApp --src ./app.zip" -ForegroundColor Yellow
