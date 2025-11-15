#!/bin/bash
echo "Starting sanctions list update: $(date)"

# Create data directory
mkdir -p ../../data

# Download OFAC (example - adjust URL as needed)
echo "Downloading OFAC data..."
# curl -o ../../data/ofac_sdn.xml [OFAC_URL]

# Import (uncomment when you have real data)
# node sanctions-importer.js import-ofac ../../data/ofac_sdn.csv

echo "Update complete: $(date)"
