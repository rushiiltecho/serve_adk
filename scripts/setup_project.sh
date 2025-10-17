#!/bin/bash

echo "Setting up project structure..."

# Create all necessary directories
mkdir -p app/api/v1 app/core app/models app/services app/utils
mkdir -p tests/unit tests/integration

# Create all __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Create pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
EOF

echo "✅ Project structure created successfully!"
echo ""
echo "Run these commands:"
echo "  1. chmod +x setup_project.sh run_tests.sh"
echo "  2. ./setup_project.sh"
echo "  3. ./run_tests.sh"