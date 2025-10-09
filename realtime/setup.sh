#!/bin/bash

# Jarvis Voice Assistant Setup Script
# This script sets up the environment for the Jarvis voice assistant

set -e  # Exit on any error
SUDO=
echo "🚀 Setting up Jarvis Voice Assistant..."

# Detect package manager and install system dependencies
if command -v zypper &> /dev/null; then
    echo "📦 Installing system dependencies with zypper..."
    $SUDO zypper in -y portaudio-devel python3-devel gcc libgthread-2_0-0
elif command -v dnf &> /dev/null; then
    echo "📦 Installing system dependencies with dnf..."
    $SUDO dnf install -y portaudio-devel python3-devel python3-pip
elif command -v apt &> /dev/null; then
    echo "📦 Installing system dependencies with apt..."
    $SUDO apt update
    $SUDO apt install -y portaudio19-dev python3-dev python3-pip python3-venv
elif command -v yum &> /dev/null; then
    echo "📦 Installing system dependencies with yum..."
    $SUDO yum install -y portaudio-devel python3-devel python3-pip
elif command -v pacman &> /dev/null; then
    echo "📦 Installing system dependencies with pacman..."
    $SUDO pacman -S --noconfirm portaudio python python-pip
else
    echo "⚠️  Unknown package manager. Please install portaudio-devel and python3-devel manually."
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv jarvis-env

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source jarvis-env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

echo "🔧 Installing PyTorch..."
pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "⚠️  WARNING: OPENAI_API_KEY environment variable is not set!"
    echo "💡 To use Jarvis, you need to set your OpenAI API key:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "🔧 You can also create a .env file with:"
    echo "   echo 'OPENAI_API_KEY=your-api-key-here' > .env"
    echo ""
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🎯 To start Jarvis:"
echo "   1. Set your API key: export OPENAI_API_KEY='your-key'"
echo "   2. Run Jarvis: bash run.sh"
echo ""
echo "🎛️  Optional environment variables:"
echo "   OPENAI_MODEL=gpt-4 (default: gpt-3.5-turbo)"
echo "   OPENAI_TTS_VOICE=nova (default: alloy)"
echo "   OPENAI_TTS_MODEL=tts-1-hd (default: tts-1)"
echo "   OPENAI_BASE_URL=https://api.openai.com/v1"
echo ""
echo ""