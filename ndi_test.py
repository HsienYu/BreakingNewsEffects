#!/usr/bin/env python3
"""
NDI Test Script for Breaking News Effects

This script tests the NDI sender functionality by creating a simple
test pattern and sending it over NDI. Use this to verify that NDI
is working correctly before running the main application.

To test:
1. Run this script
2. Open an NDI receiver application (like OBS Studio with NDI plugin, 
   NDI Studio Monitor, or any NDI-compatible software)
3. Look for "Breaking News Effects - Test" as an available NDI source
4. You should see a test pattern with moving text

Requirements:
- NDI SDK installed on your system
- ndi-python package installed (pip install ndi-python)
"""

import pygame
import time
import sys
import os
from displays.ndi_sender import create_ndi_sender, is_ndi_available

def create_test_pattern(width, height, frame_count):
    """Create a test pattern with animated elements"""
    # Create pygame surface
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Background gradient
    for y in range(height):
        color_intensity = int(255 * (y / height))
        color = (color_intensity // 4, color_intensity // 2, color_intensity)
        pygame.draw.line(surface, color, (0, y), (width, y))
    
    # Moving elements
    font_large = pygame.font.Font(None, 72)
    font_small = pygame.font.Font(None, 36)
    
    # Title text (static)
    title_text = font_large.render("NDI Test Pattern", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(width // 2, height // 4))
    surface.blit(title_text, title_rect)
    
    # Moving text
    moving_x = (frame_count * 3) % (width + 300) - 300
    moving_text = font_small.render("Breaking News Effects - NDI Streaming Test", True, (255, 255, 0))
    surface.blit(moving_text, (moving_x, height // 2))
    
    # Frame counter
    frame_text = font_small.render(f"Frame: {frame_count:05d}", True, (0, 255, 0))
    surface.blit(frame_text, (20, height - 40))
    
    # Connection indicator (placeholder for now)
    status_text = font_small.render("NDI Status: Sending", True, (0, 255, 255))
    surface.blit(status_text, (width - 200, height - 40))
    
    # Color bars at the bottom
    bar_width = width // 8
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
              (255, 0, 255), (0, 255, 255), (255, 255, 255), (128, 128, 128)]
    
    for i, color in enumerate(colors):
        x = i * bar_width
        pygame.draw.rect(surface, color, (x, height - 80, bar_width, 40))
    
    return surface

def main():
    """Main test function"""
    print("=" * 50)
    print("Breaking News Effects - NDI Test")
    print("=" * 50)
    
    # Check if NDI is available
    if not is_ndi_available():
        print("❌ NDI is not available on this system")
        print("   Make sure you have:")
        print("   1. NDI SDK installed")
        print("   2. ndi-python package installed (pip install ndi-python)")
        sys.exit(1)
    
    print("✅ NDI is available")
    
    # Initialize pygame
    pygame.init()
    pygame.font.init()
    
    # Test configuration
    test_width = 1920
    test_height = 1080
    test_fps = 30
    sender_name = "Breaking News Effects - Test"
    
    print(f"📺 Creating NDI sender: '{sender_name}'")
    print(f"   Resolution: {test_width}x{test_height}")
    print(f"   Frame rate: {test_fps} fps")
    
    # Create NDI sender
    ndi_sender = create_ndi_sender(
        sender_name=sender_name,
        width=test_width,
        height=test_height,
        fps=test_fps
    )
    
    if not ndi_sender:
        print("❌ Failed to create NDI sender")
        pygame.quit()
        sys.exit(1)
    
    print("✅ NDI sender created successfully")
    print("\n🔄 Starting test transmission...")
    print("   Look for the NDI source in your receiver application")
    print("   Press Ctrl+C to stop")
    
    # Create a small preview window
    preview_width = 320
    preview_height = 180
    screen = pygame.display.set_mode((preview_width, preview_height))
    pygame.display.set_caption("NDI Test - Preview")
    
    clock = pygame.time.Clock()
    frame_count = 0
    start_time = time.time()
    last_connection_check = 0
    
    try:
        while True:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        break
            
            # Create test pattern
            test_surface = create_test_pattern(test_width, test_height, frame_count)
            
            # Send to NDI
            success = ndi_sender.send_pygame_surface(test_surface)
            
            # Create preview (scaled down version)
            preview_surface = pygame.transform.scale(test_surface, (preview_width, preview_height))
            screen.blit(preview_surface, (0, 0))
            pygame.display.flip()
            
            # Check connections periodically
            current_time = time.time()
            if current_time - last_connection_check > 2.0:  # Check every 2 seconds
                connection_count = ndi_sender.get_connection_count()
                if connection_count > 0:
                    print(f"📡 NDI connections: {connection_count}")
                else:
                    print("🔍 No NDI receivers connected")
                last_connection_check = current_time
            
            frame_count += 1
            
            # Print stats every 100 frames
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed
                print(f"📊 Frame {frame_count:05d} | "
                      f"Actual FPS: {actual_fps:.1f} | "
                      f"NDI Status: {'✅ OK' if success else '❌ Error'}")
            
            clock.tick(test_fps)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    
    finally:
        # Cleanup
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        print(f"\n📈 Test Statistics:")
        print(f"   Total frames sent: {frame_count}")
        print(f"   Total time: {elapsed:.1f} seconds")
        print(f"   Average FPS: {avg_fps:.1f}")
        
        if ndi_sender:
            final_connections = ndi_sender.get_connection_count()
            print(f"   Final connections: {final_connections}")
            ndi_sender.stop()
            print("✅ NDI sender stopped")
        
        pygame.quit()
        print("✅ Test completed")

if __name__ == "__main__":
    main()