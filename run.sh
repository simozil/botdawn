#!/bin/bash

# Check if the script is running as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root."
    echo "Please try switching to the root user using the 'sudo -i' command, and then run this script again."
    exit 1
fi

# Check and install Node.js and npm
function install_nodejs_and_npm() {
    if command -v node > /dev/null 2>&1; then
        echo "Node.js is already installed"
    else
        echo "Node.js is not installed, installing now..."
        curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi

    if command -v npm > /dev/null 2>&1; then
        echo "npm is already installed"
    else
        echo "npm is not installed, installing now..."
        sudo apt-get install -y npm
    fi
}

# Check and install PM2
function install_pm2() {
    if command -v pm2 > /dev/null 2>&1; then
        echo "PM2 is already installed"
    else
        echo "PM2 is not installed, installing now..."
        npm install pm2@latest -g
    fi
}

# Node installation function
function install_node() {
    install_nodejs_and_npm
    install_pm2

    pip3 install pillow
    pip3 install ddddocr
    pip3 install requests
    pip3 install loguru

    # Get username
    read -r -p "Please enter email: " DAWNUSERNAME
    export DAWNUSERNAME=$DAWNUSERNAME

    # Get password
    read -r -p "Please enter password: " DAWNPASSWORD
    export DAWNPASSWORD=$DAWNPASSWORD

    echo $DAWNUSERNAME:$DAWNPASSWORD > password.txt

    wget -O dawn.py https://raw.githubusercontent.com/b1n4he/DawnAuto/main/dawn.py
    # Update and install necessary software
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl iptables build-essential git wget jq make gcc nano tmux htop nvme-cli pkg-config libssl-dev libleveldb-dev tar clang bsdmainutils ncdu unzip libleveldb-dev lz4 snapd

    pm2 start dawn.py
}

# Main menu
function main_menu() {
    while true; do
        clear
        cat << EOF
_________________________
< Dawn Auto Script (for foreign VPS), from Twitter user Baboon@oxbaboon >
< Free and open-source, if someone charges you, go after them 🤌 >
-------------------------
        \   ^__^
        \  (oo)\_______
            (__)\       )\/\/
                ||----w |
                ||     ||
EOF
        echo "To exit the script, press ctrl+c on your keyboard."
        echo "Please select an action to perform:"
        echo "1. Install Node"
        read -p "Enter your choice: " OPTION

        case $OPTION in
        1) install_node ;;
        *) echo "Invalid option." ;;
        esac
        echo "Press any key to return to the main menu..."
        read -n 1
    done
}

# Display main menu
main_menu
