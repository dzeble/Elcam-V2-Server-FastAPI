#!/bin/bash
set -e

# Get project name argument
PROJECT_NAME=$1

if [ -z "$PROJECT_NAME" ]; then
    read -p "Enter project name: " PROJECT_NAME
fi

# Decide target directory
if [ "$PROJECT_NAME" = "." ]; then
    TARGET_DIR="."
else
    TARGET_DIR="./$PROJECT_NAME"
    mkdir -p "$TARGET_DIR"
fi

cd "$TARGET_DIR"

echo "📁 Creating FastAPI project structure in: $(pwd)"

# Top-level files
touch .env .gitignore README.md pyproject.toml pytest.ini

# Docker
mkdir -p docker
touch docker/Dockerfile docker/docker-compose.yml

# Alembic
mkdir -p alembic/versions
touch alembic/env.py

# Scripts
mkdir -p scripts
touch scripts/__init__.py scripts/new_service.py

# App
mkdir -p app/core app/db app/services app/services/users app/services/auth
touch app/__init__.py
touch app/main.py
touch app/core/{__init__.py,env.py,config.py,logging.py,security.py}
touch app/db/{__init__.py,base.py,session.py}

# Example services
touch app/services/__init__.py
for svc in users auth; do
  touch app/services/$svc/__init__.py
  touch app/services/$svc/{models.py,schemas.py,service.py,routers.py}
done

# Tests
mkdir -p tests/services
touch tests/conftest.py tests/test_meta_services.py
touch tests/services/test_users.py tests/services/test_auth.py

echo "✅ FastAPI enterprise template skeleton created in $(pwd)"
