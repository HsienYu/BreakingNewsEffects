#!/usr/bin/env python3
"""
Test script for hybrid UI (scrollable list + scrolling text)
"""

import time
import pygame
from displays.scrolling_display import ScrollingNewsDisplay

def main():
    print("Testing Hybrid UI: Scrollable List + Scrolling Text")
    print("=" * 60)
    print("\nFeatures:")
    print("  • Scrollable news list (mixed/random order)")
    print("  • Auto-scrolling text at bottom")
    print("  • Small font (28px)")
    print("  • Thin bottom bar (25px)")
    print("\nControls:")
    print("  • Mouse wheel or Up/Down arrows - Scroll the list")
    print("  • ESC - Exit")
    print("\n" + "=" * 60)
    
    # Create display
    display = ScrollingNewsDisplay(
        width=1280,
        height=720,
        transparent_bg=False,
        green_screen=False
    )
    
    # Add some test news
    test_news = [
        "BBC NEWS: Global markets reach record highs",
        "NTN24: Political tensions rise in Latin America",
        "REUTERS: Technology sector shows strong growth",
        "CNN: Weather update - sunny skies expected",
        "AL JAZEERA: International summit begins today",
        "BBC NEWS: Sports update - Championship results",
        "NTN24: Economic report shows positive trends",
        "REUTERS: Breaking - Major announcement expected",
        "CNN: Entertainment news - New film releases",
        "AL JAZEERA: Analysis of current global events"
    ]
    
    print("\nAdding test news items...")
    for i, news in enumerate(test_news):
        display.show_news(news)
        print(f"  [{i+1}/{len(test_news)}] {news[:50]}...")
        time.sleep(0.5)  # Add gradually for demonstration
    
    print("\n✓ All news items added!")
    print("\nDisplay is now running...")
    print("  • List shows items in MIXED ORDER")
    print("  • Bottom bar scrolls through all items")
    print("  • Try scrolling with mouse wheel or arrow keys!")
    print("\nPress ESC to exit\n")
    
    # Main loop
    clock = pygame.time.Clock()
    try:
        while display.is_running():
            display.update()
            clock.tick(60)  # 60 FPS
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        display.close()
        print("✓ Display closed")

if __name__ == "__main__":
    main()
