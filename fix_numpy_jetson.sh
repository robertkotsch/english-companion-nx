#!/bin/bash
# fix_numpy_jetson.sh - Fix numpy dependency conflicts on Jetson Orin NX
# Run this script on the Jetson after experiencing numpy downgrade issues

set -e  # Exit on error

echo "=== Numpy Dependency Fix for Jetson Orin NX ==="
echo "This script will fix numpy 1.22.0 downgrade issue"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "conversation_prototype.py" ]; then
    echo -e "${RED}Error: Run this script from english-companion-nx directory${NC}"
    exit 1
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: .venv not found. Create it first with:${NC}"
    echo "python3 -m venv .venv --system-site-packages"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking current state...${NC}"
source .venv/bin/activate

# Check current numpy version
NUMPY_VERSION=$(python -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "not installed")
echo "Current numpy version: $NUMPY_VERSION"

if [ "$NUMPY_VERSION" = "1.22.0" ]; then
    echo -e "${RED}Confirmed: numpy is downgraded to 1.22.0${NC}"
elif [ "$NUMPY_VERSION" != "not installed" ]; then
    echo -e "${GREEN}Numpy version looks OK: $NUMPY_VERSION${NC}"
    echo "Checking for dependency conflicts..."
    pip check || echo -e "${YELLOW}Some conflicts found, continuing...${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Analyzing dependency tree...${NC}"
echo "Installing pipdeptree for analysis..."
pip install -q pipdeptree

echo ""
echo "What depends on numpy:"
pipdeptree -r -p numpy 2>/dev/null || echo "pipdeptree failed, continuing..."

echo ""
echo -e "${YELLOW}Step 3: Upgrading numpy...${NC}"
echo "Forcing numpy upgrade to >=1.24.1..."
pip install --upgrade --force-reinstall 'numpy>=1.24.1,<2.0.0'

# Verify upgrade
NEW_NUMPY_VERSION=$(python -c "import numpy; print(numpy.__version__)" 2>/dev/null)
echo "New numpy version: $NEW_NUMPY_VERSION"

if [[ "$NEW_NUMPY_VERSION" < "1.24.0" ]]; then
    echo -e "${RED}Error: numpy upgrade failed, still at $NEW_NUMPY_VERSION${NC}"
    echo ""
    echo "Trying alternative approach: reinstall dependencies in order..."

    echo ""
    echo -e "${YELLOW}Step 4: Reinstalling in correct order...${NC}"

    # Install numpy first
    pip install --force-reinstall 'numpy>=1.24.1,<2.0.0'

    # Install TTS (has heavy dependencies)
    echo "Reinstalling TTS..."
    pip install --force-reinstall TTS>=0.21.0

    # Install Whisper
    echo "Reinstalling openai-whisper..."
    pip install --force-reinstall openai-whisper>=20231117

    # Install remaining requirements
    echo "Reinstalling other requirements..."
    pip install -r requirements-jetson.txt

    # Check again
    FINAL_NUMPY_VERSION=$(python -c "import numpy; print(numpy.__version__)" 2>/dev/null)
    echo "Final numpy version: $FINAL_NUMPY_VERSION"
fi

echo ""
echo -e "${YELLOW}Step 5: Verifying installation...${NC}"

# Check all dependencies
echo "Running pip check..."
if pip check; then
    echo -e "${GREEN}✓ All dependencies satisfied!${NC}"
else
    echo -e "${RED}⚠ Some dependency conflicts remain${NC}"
    echo "See output above for details"
fi

echo ""
echo "Testing critical imports..."

# Test numpy
if python -c "import numpy; print('numpy version:', numpy.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ numpy OK${NC}"
else
    echo -e "${RED}✗ numpy import failed${NC}"
fi

# Test Whisper
if python -c "import whisper; print('whisper OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ whisper OK${NC}"
else
    echo -e "${RED}✗ whisper import failed${NC}"
fi

# Test TTS
if python -c "from TTS.api import TTS; print('TTS OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ TTS OK${NC}"
else
    echo -e "${RED}✗ TTS import failed${NC}"
fi

# Test PyTorch
if python -c "import torch; print('PyTorch CUDA available:', torch.cuda.is_available())" 2>/dev/null; then
    echo -e "${GREEN}✓ PyTorch OK${NC}"
else
    echo -e "${RED}✗ PyTorch import failed${NC}"
fi

echo ""
echo -e "${YELLOW}Step 6: Summary${NC}"
echo "---"
python -c "import numpy; print('numpy:', numpy.__version__)"
python -c "import whisper; print('whisper: installed')" 2>/dev/null || echo "whisper: FAILED"
python -c "from TTS.api import TTS; print('TTS: installed')" 2>/dev/null || echo "TTS: FAILED"
python -c "import torch; print('torch:', torch.__version__, '| CUDA:', torch.cuda.is_available())"
echo "---"

echo ""
FINAL_NUMPY=$(python -c "import numpy; print(numpy.__version__)" 2>/dev/null)
if [[ "$FINAL_NUMPY" < "1.24.0" ]]; then
    echo -e "${RED}⚠ FIX FAILED: numpy is still $FINAL_NUMPY${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Read TROUBLESHOOTING_NUMPY.md for advanced solutions"
    echo "2. Consider switching to faster-whisper (see Strategy 3)"
    echo "3. Or recreate venv from scratch (see Strategy 4)"
    exit 1
else
    echo -e "${GREEN}✓ SUCCESS: numpy is $FINAL_NUMPY${NC}"
    echo ""
    echo "You can now test the prototype:"
    echo "  python conversation_prototype.py"
    echo ""
    echo "If you still see errors, check:"
    echo "  pip check"
    exit 0
fi
