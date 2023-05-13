#!/bin/bash

# Check if a port number is provided
if [ -z "$1" ]
  then
    echo "Error: Port number not provided"
    exit 1
fi

# Get the PID of the process running on the port
PID=$(lsof -i :"${1}" | awk 'NR==2{print $2}')

# Check if a PID was found
if [ -z "$PID" ]
  then
    echo "Error: No process found running on port $1"
    exit 1
fi

# Kill the process
echo "Killing process $PID running on port $1"
kill -9 "$PID"

# ./killport.sh 8000