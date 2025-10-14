#!/bin/bash

# Build All Presentations Script
# Builds both Guest Finder and Topic Researcher presentations

set -e  # Exit on error

echo "🎨 Building All Presentations"
echo "=============================="
echo ""

# Build Guest Finder presentation
echo "🔍 Building Guest Finder Agent presentation..."
./scripts/build-presentations.sh docs/presentations/guest-finder/presentation.md
echo ""

# Build Topic Researcher presentation
echo "📊 Building Topic Researcher Agent presentation..."
./scripts/build-presentations.sh docs/presentations/topic-researcher/presentation.md
echo ""

echo "✨ All presentations built successfully!"
echo ""
echo "📦 Generated files:"
echo "   Guest Finder:"
echo "     - docs/presentations/guest-finder/presentation-final.html"
echo "     - docs/presentations/guest-finder/presentation-final.pdf"
echo ""
echo "   Topic Researcher:"
echo "     - docs/presentations/topic-researcher/presentation-final.html"
echo "     - docs/presentations/topic-researcher/presentation-final.pdf"
echo ""
echo "🚀 Open presentations:"
echo "   open docs/presentations/guest-finder/presentation-final.html"
echo "   open docs/presentations/topic-researcher/presentation-final.html"
