#!/bin/bash

# Function to install AWS CLI on Linux
install_aws_cli_linux() {
    echo "Installing AWS CLI on Linux..."
    # Add installation commands for Linux here
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not found. Installing..."
        sudo apt-get update
        sudo apt-get install awscli
    else
        echo "AWS CLI already installed."
    fi
}

# Function to install AWS CLI on macOS
install_aws_cli_macos() {
    echo "Installing AWS CLI on macOS..."
    # Add installation commands for macOS here
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not found. Installing..."
        brew install awscli
    else
        echo "AWS CLI already installed."
    fi
}

# Function to install AWS CLI on Windows
install_aws_cli_windows() {
    echo "Installing AWS CLI on Windows..."
    # Check if AWS CLI is already installed
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not found. Installing..."
        choco install awscli
    else
        echo "AWS CLI already installed."
    fi
}


# Check if data folder exists, if not create it
if [ ! -d "./data" ]; then
    echo "Creating data folder..."
    mkdir ./data
else
    echo "Data folder already exists."
fi

# Detect the operating system and call the appropriate installation function
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    install_aws_cli_linux
elif [[ "$OSTYPE" == "darwin"* ]]; then
    install_aws_cli_macos
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    install_aws_cli_windows
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi
# 從 .env 文件中加載環境變量
set -o allexport
source .env
set -o allexport


# Use AWS CLI to configure the initial settings
echo "Configuring AWS CLI..."
aws configure --profile init-conf set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure --profile init-conf set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure --profile init-conf set region "$AWS_DEFAULT_REGION"
aws configure --profile init-conf set output "$AWS_OUTPUT_FORMAT"

aws s3 cp --recursive s3://ai-s3-disk/datasets/StocksData/ ./data