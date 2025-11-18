#!/bin/bash
set -e

echo "=========================================="
echo "🚀 Deploying ComplianceAI Fixes"
echo "=========================================="

# Set environment variable
export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es'

# Import PEP data
echo -e "\n📥 Importing PEP data..."
python3 import_pep_to_supabase.py

# Backup old backend
echo -e "\n💾 Backing up old backend..."
cp flask_backend.py flask_backend.py.backup

echo -e "\n✅ PEP data imported!"
echo "Now update flask_backend.py with the corrected code from the artifact"
echo "Then restart your backend server"
