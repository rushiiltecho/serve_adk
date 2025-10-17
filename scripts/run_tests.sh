#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Vertex AI Agent Gateway Tests${NC}"
echo -e "${GREEN}================================${NC}\n"

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"
echo -e "${BLUE}PYTHONPATH: ${PYTHONPATH}${NC}\n"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel -q

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q pytest pytest-cov pytest-asyncio httpx python-dotenv

# Create necessary __init__.py files
echo -e "${YELLOW}Setting up package structure...${NC}"
touch app/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Check if app module can be imported
echo -e "\n${BLUE}Verifying app module...${NC}"
python3 -c "import sys; sys.path.insert(0, '.'); from app.config import Settings; print('✅ app module imports successfully')" 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Cannot import app module${NC}"
    echo -e "${YELLOW}Checking project structure...${NC}"
    ls -la app/
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -e "\n${BLUE}Loading environment variables...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}No .env file found, using test defaults${NC}"
    export GOOGLE_CLOUD_PROJECT="test-project"
    export GOOGLE_CLOUD_LOCATION="us-central1"
    export AGENTS='[{"agent_id":"test-123","name":"test_agent","display_name":"Test Agent","description":"Test","enabled":true}]'
    export ENVIRONMENT="test"
fi

# Create basic test if none exists
if [ ! -f "tests/unit/test_basic.py" ]; then
    echo -e "${YELLOW}Creating basic test file...${NC}"
    mkdir -p tests/unit
    cat > tests/unit/test_basic.py << 'EOF'
"""Basic sanity tests."""
import pytest
import os


def test_python_path():
    """Test that Python path is set correctly."""
    import sys
    assert '.' in sys.path or os.getcwd() in sys.path


def test_app_import():
    """Test that app module can be imported."""
    try:
        from app.config import Settings
        assert Settings is not None
    except ImportError as e:
        pytest.fail(f"Failed to import app module: {e}")


def test_environment_loaded():
    """Test that environment is loaded."""
    assert os.getenv('GOOGLE_CLOUD_PROJECT') is not None


def test_agents_config():
    """Test that AGENTS config is valid."""
    import json
    agents_str = os.getenv('AGENTS')
    assert agents_str is not None
    agents = json.loads(agents_str)
    assert isinstance(agents, list)
    assert len(agents) > 0


def test_settings_creation():
    """Test that Settings can be created."""
    from app.config import Settings
    
    # Create settings with test values
    settings = Settings(
        google_cloud_project="test-project",
        google_cloud_location="us-central1"
    )
    
    assert settings.google_cloud_project == "test-project"
    assert settings.google_cloud_location == "us-central1"
EOF
fi

# Run unit tests
echo -e "\n${BLUE}Running unit tests...${NC}"
PYTHONPATH="${PROJECT_ROOT}" pytest tests/unit/ -v --tb=short

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Unit tests passed${NC}"


# Run with coverage
echo -e "\n${BLUE}Running tests with coverage...${NC}"
PYTHONPATH="${PROJECT_ROOT}" pytest --cov=app --cov-report=html --cov-report=term-missing tests/unit/

# Display summary
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ All tests passed${NC}"
echo -e "Coverage report: ${YELLOW}htmlcov/index.html${NC}"
echo -e "\n${GREEN}Tests completed successfully!${NC}\n"