#!/usr/bin/env python3
"""
Spout Test Script for Breaking News Effects

This script tests the Spout sender functionality by creating a simple
test pattern and sending it over Spout. This is much easier to set up
than NDI on Windows!

To test:
1. Run this script
2. Open a Spout-compatible application like:
   - OBS Studio (with Spout2 plugin)
   - Resolume Arena/Avenue  
   - TouchDesigner
   - VLC Media Player (with Spout plugin)
   - Any Spout receiver application
3. Look for "Breaking News Effects - Spout Test" as an available Spout source
4. You should see a test pattern with moving elements

Requirements:
- Windows operating system
- SpoutGL package: pip install SpoutGL
- OpenGL support (most modern systems have this)
"""

import pygame
import numpy as np
import time
import sys
import os
from displays.spout_sender import create_spout_sender, is_spout_available, list_spout_senders

def create_test_pattern(width, height, frame_count):
    """Create an animated test pattern"""
    # Create pygame surface with alpha
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Animated background
    time_factor = frame_count * 0.05
    
    # Create gradient background
    for y in range(height):
        for x in range(width):
            # Create moving wave pattern
            wave = np.sin((x + y + time_factor * 50) * 0.01) * 127 + 128
            red = int(wave * 0.3)
            green = int(wave * 0.5) 
            blue = int(wave * 0.8)
            surface.set_at((x, y), (red, green, blue, 255))
    
    # Add text elements
    font_large = pygame.font.Font(None, 84)
    font_medium = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    
    # Main title
    title_text = font_large.render("🎯 SPOUT TEST", True, (255, 255, 255))
    title_shadow = font_large.render("🎯 SPOUT TEST", True, (0, 0, 0))
    
    # Add shadow effect
    title_rect = title_text.get_rect(center=(width // 2, height // 4))
    shadow_rect = title_rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    
    surface.blit(title_shadow, shadow_rect)
    surface.blit(title_text, title_rect)
    
    # Moving ticker text
    ticker_text = "Breaking News Effects • Spout for Windows • Real-time Video Sharing • "
    ticker_surface = font_medium.render(ticker_text, True, (255, 255, 0))
    ticker_width = ticker_surface.get_width()
    
    # Calculate moving position
    ticker_x = (frame_count * 2) % (width + ticker_width) - ticker_width
    ticker_y = height // 2
    
    # Draw ticker background
    ticker_bg = pygame.Surface((width, 60), pygame.SRCALPHA)
    ticker_bg.fill((255, 0, 0, 180))  # Semi-transparent red
    surface.blit(ticker_bg, (0, ticker_y - 10))
    
    # Draw ticker text
    surface.blit(ticker_surface, (ticker_x, ticker_y))
    
    # Frame counter and stats
    stats_text = font_small.render(f"Frame: {frame_count:05d} | Spout Streaming Active", 
                                  True, (0, 255, 255))
    surface.blit(stats_text, (20, height - 100))
    
    # Instructions
    instructions = [
        "Look for this source in Spout-compatible applications:",
        "• OBS Studio (with Spout2 plugin)",
        "• Resolume Arena/Avenue",
        "• TouchDesigner",
        "• VLC Media Player (with Spout plugin)"
    ]
    
    for i, instruction in enumerate(instructions):
        color = (255, 255, 255) if i == 0 else (200, 200, 200)
        inst_text = font_small.render(instruction, True, color)
        surface.blit(inst_text, (20, height - 70 + i * 25))
    
    # Animated elements
    # Bouncing circle
    circle_x = int(width * 0.8 + 100 * np.sin(time_factor))
    circle_y = int(height * 0.3 + 50 * np.cos(time_factor * 1.5))
    pygame.draw.circle(surface, (255, 100, 255), (circle_x, circle_y), 30)
    
    # Color bars
    bar_width = width // 8
    colors = [
        (255, 0, 0, 255),    # Red
        (255, 127, 0, 255),  # Orange
        (255, 255, 0, 255),  # Yellow
        (0, 255, 0, 255),    # Green
        (0, 255, 255, 255),  # Cyan
        (0, 0, 255, 255),    # Blue
        (127, 0, 255, 255),  # Purple
        (255, 255, 255, 255) # White
    ]
    
    bar_height = 40
    bar_y = height - 140
    
    for i, color in enumerate(colors):
        x = i * bar_width
        bar_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        bar_surface.fill(color)
        surface.blit(bar_surface, (x, bar_y))
    
    return surface

def main():
    """Main test function"""
    print("=" * 60)
    print("🎯 Breaking News Effects - Spout Test")
    print("=" * 60)
    
    # Check if Spout is available
    if not is_spout_available():
        print("❌ Spout is not available on this system")
        print("   Make sure you have:")
        print("   1. Windows operating system")
        print("   2. SpoutGL package installed: pip install SpoutGL")
        print("   3. OpenGL support (most systems have this)")
        sys.exit(1)
    
    print("✅ Spout is available")
    
    # List existing Spout senders
    try:
        existing_senders = list_spout_senders()
        if existing_senders:
            print(f"🔍 Found {len(existing_senders)} existing Spout senders:")
            for sender in existing_senders:
                print(f"   • {sender}")
        else:
            print("🔍 No existing Spout senders found")
    except Exception as e:
        print(f"⚠️  Could not list existing senders: {e}")
    
    # Initialize pygame
    pygame.init()
    pygame.font.init()
    
    # Test configuration
    test_width = 1280
    test_height = 720
    sender_name = "Breaking News Effects - Spout Test"
    
    print(f"\n📺 Creating Spout sender: '{sender_name}'")
    print(f"   Resolution: {test_width}x{test_height}")
    
    # Create Spout sender
    spout_sender = create_spout_sender(
        sender_name=sender_name,
        width=test_width,
        height=test_height
    )
    
    if not spout_sender:
        print("❌ Failed to create Spout sender")
        pygame.quit()
        sys.exit(1)
    
    print("✅ Spout sender created successfully")
    print(f"\n🚀 Starting test transmission...")
    print(f"   Source name: '{sender_name}'")
    print("   Look for this source in your Spout-compatible applications")
    print("   Press Ctrl+C or close window to stop")
    
    # Create a preview window
    preview_width = 640
    preview_height = 360
    screen = pygame.display.set_mode((preview_width, preview_height))
    pygame.display.set_caption("Spout Test - Preview (Close to stop)")
    
    clock = pygame.time.Clock()
    frame_count = 0
    start_time = time.time()
    last_stats_time = 0
    target_fps = 30
    
    try:
        running = True
        while running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        running = False
            
            # Create test pattern at full resolution
            test_surface = create_test_pattern(test_width, test_height, frame_count)
            
            # Send to Spout
            success = spout_sender.send_pygame_surface(test_surface)
            
            # Create preview (scaled down version)
            preview_surface = pygame.transform.scale(test_surface, 
                                                   (preview_width, preview_height))
            screen.blit(preview_surface, (0, 0))
            pygame.display.flip()
            
            frame_count += 1
            
            # Print stats every 5 seconds
            current_time = time.time()
            if current_time - last_stats_time > 5.0:
                elapsed = current_time - start_time
                actual_fps = frame_count / elapsed
                
                print(f"📊 Frame {frame_count:05d} | "
                      f"Actual FPS: {actual_fps:.1f}/{target_fps} | "
                      f"Spout: {'✅ OK' if success else '❌ Error'}")
                
                # Show sender info
                info = spout_sender.get_sender_info()
                if info:
                    print(f"   Average FPS: {info['average_fps']:.1f} | "
                          f"Total frames: {info['frames_sent']}")
                
                last_stats_time = current_time
            
            clock.tick(target_fps)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    finally:
        # Cleanup and show final stats
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        print(f"\n📈 Final Test Statistics:")
        print(f"   Total frames sent: {frame_count}")
        print(f"   Total time: {elapsed:.1f} seconds")
        print(f"   Average FPS: {avg_fps:.1f}")
        
        if spout_sender:
            info = spout_sender.get_sender_info()
            if info and info['is_active']:
                print(f"   Spout sender was active throughout test")
            
            spout_sender.stop()
            print("✅ Spout sender stopped")
        
        pygame.quit()
        print("✅ Test completed successfully")
        print("\n💡 Tips for using Spout:")
        print("   • Install OBS Studio and the Spout2 plugin for easy recording")
        print("   • Spout has very low latency compared to screen capture")
        print("   • Multiple applications can receive the same Spout source")
        print("   • Perfect for live streaming and real-time visual effects")

if __name__ == "__main__":
    main()