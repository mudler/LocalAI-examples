#!/bin/bash

# Jarvis Voice Assistant Run Script
# This script activates the virtual environment and starts Jarvis

# Change to the directory where this script is located
pushd "$(dirname "$0")" > /dev/null

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Jarvis Voice Assistant...${NC}"

# Check if virtual environment exists
if [ ! -d "jarvis-env" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}💡 Please run ./setup.sh first to set up the environment.${NC}"
    exit 1
fi

# Check if requirements are installed
if [ ! -f "jarvis-env/pyvenv.cfg" ]; then
    echo -e "${RED}❌ Virtual environment appears to be corrupted!${NC}"
    echo -e "${YELLOW}💡 Please run ./setup.sh again to recreate the environment.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source jarvis-env/bin/activate

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  WARNING: OPENAI_API_KEY environment variable is not set!${NC}"
    echo -e "${BLUE}💡 Please set your OpenAI API key:${NC}"
    echo -e "   ${YELLOW}export OPENAI_API_KEY='your-api-key-here'${NC}"
    echo ""
    echo -e "${BLUE}🔧 Or create a .env file:${NC}"
    echo -e "   ${YELLOW}echo 'OPENAI_API_KEY=your-api-key-here' > .env${NC}"
    echo ""
    echo -e "${BLUE}🎛️  Optional environment variables:${NC}"
    echo -e "   ${YELLOW}OPENAI_MODEL=gpt-4${NC} (default: gpt-3.5-turbo)"
    echo -e "   ${YELLOW}OPENAI_TTS_VOICE=nova${NC} (default: alloy)"
    echo -e "   ${YELLOW}OPENAI_TTS_MODEL=tts-1-hd${NC} (default: tts-1)"
    echo -e "   ${YELLOW}OPENAI_BASE_URL=https://api.openai.com/v1${NC}"
    echo -e "   ${YELLOW}BACKGROUND_AUDIO=false${NC} (default: true)"
    echo ""
    echo -e "${BLUE}🎤 Available TTS voices:${NC} ${YELLOW}alloy, echo, fable, onyx, nova, shimmer${NC}"
    echo ""
    echo -e "${RED}❌ Cannot start without API key. Exiting...${NC}"
    exit 1
fi

# Check if realtime.py exists
if [ ! -f "realtime.py" ]; then
    echo -e "${RED}❌ realtime.py not found!${NC}"
    echo -e "${YELLOW}💡 Please make sure you're in the correct directory.${NC}"
    exit 1
fi

# Show current configuration
echo -e "${GREEN}✅ Configuration:${NC}"
echo -e "   ${BLUE}📝 Chat Model:${NC} ${YELLOW}${OPENAI_MODEL:-gpt-3.5-turbo}${NC}"
echo -e "   ${BLUE}🎤 TTS Model:${NC} ${YELLOW}${OPENAI_TTS_MODEL:-tts-1}${NC}"
echo -e "   ${BLUE}🗣️ TTS Voice:${NC} ${YELLOW}${OPENAI_TTS_VOICE:-alloy}${NC}"
echo -e "   ${BLUE}🌐 Base URL:${NC} ${YELLOW}${OPENAI_BASE_URL:-https://api.openai.com/v1}${NC}"
echo ""

# Start Jarvis
echo -e "${GREEN}🎯 Starting Jarvis...${NC}"
echo -e "${BLUE}💡 Press Ctrl+C to stop${NC}"
echo ""

python realtime.py