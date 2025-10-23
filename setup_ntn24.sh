#!/bin/bash
# Setup script for NTN24 scraper

echo "🚀 Setting up NTN24 News Scraper..."
echo ""

# Install required dependencies
echo "📦 Installing dependencies..."
pip3 install requests beautifulsoup4

# Check if installation was successful
if python3 -c "import requests; import bs4" 2>/dev/null; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "Usage:"
echo "  # Basic scraping (fast)"
echo "  python3 ntn24_scraper.py"
echo ""
echo "  # Full offline mode (downloads everything)"
echo "  python3 ntn24_scraper.py --offline"
echo ""
echo "  # List cached news"
echo "  python3 ntn24_scraper.py --list"
echo ""
echo "For more information, see NTN24_OFFLINE_GUIDE.md"
