#!/usr/bin/env python3
"""
Spout Transparency Test Script

This script helps you verify that transparency is working correctly in your Spout setup.
It creates clear visual patterns to test alpha channel support.
"""

import pygame
import numpy as np
import time
from displays.spout_sender import create_spout_sender, is_spout_available

def create_transparency_test_pattern(width, height, frame_number):
    """Create a test pattern to verify transparency is working"""
    # Create pygame surface with alpha
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Clear to completely transparent
    surface.fill((0, 0, 0, 0))
    
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    
    # Create different transparency levels
    test_areas = [
        {"name": "100% OPAQUE", "alpha": 255, "color": (255, 0, 0), "pos": (50, 50)},
        {"name": "75% OPAQUE", "alpha": 192, "color": (0, 255, 0), "pos": (50, 150)},
        {"name": "50% OPAQUE", "alpha": 128, "color": (0, 0, 255), "pos": (50, 250)},
        {"name": "25% OPAQUE", "alpha": 64, "color": (255, 255, 0), "pos": (50, 350)},
        {"name": "0% TRANSPARENT", "alpha": 0, "color": (255, 0, 255), "pos": (50, 450)},
    ]
    
    for area in test_areas:
        # Create a rectangle with the specified transparency
        rect_surface = pygame.Surface((300, 60), pygame.SRCALPHA)
        color_with_alpha = (*area["color"], area["alpha"])
        rect_surface.fill(color_with_alpha)
        surface.blit(rect_surface, area["pos"])
        
        # Add text label (always opaque for readability)
        if area["alpha"] > 0:  # Only show text if not completely transparent
            text_color = (255, 255, 255) if sum(area["color"]) < 400 else (0, 0, 0)
            text = font_small.render(area["name"], True, text_color)
            text_pos = (area["pos"][0] + 10, area["pos"][1] + 20)
            surface.blit(text, text_pos)
    
    # Add instructions
    title = font_large.render("SPOUT TRANSPARENCY TEST", True, (255, 255, 255))
    surface.blit(title, (400, 50))
    
    instructions = [
        "In your Spout receiver (OBS, etc.):",
        "• 100% OPAQUE should be fully visible",
        "• Lower percentages should be see-through", 
        "• 0% TRANSPARENT should be invisible",
        "• Background should be transparent",
        f"Frame: {frame_number:04d}"
    ]
    
    for i, instruction in enumerate(instructions):
        color = (255, 255, 255) if i < 5 else (0, 255, 255)
        inst_text = font_small.render(instruction, True, color)
        surface.blit(inst_text, (400, 100 + i * 30))
    
    # Add animated moving indicator
    indicator_x = int(400 + 100 * np.sin(frame_number * 0.1))
    indicator_y = 350
    
    indicator_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
    indicator_surface.fill((255, 255, 255, 200))  # Semi-transparent white
    pygame.draw.circle(indicator_surface, (255, 0, 0, 255), (30, 30), 20)  # Red circle
    surface.blit(indicator_surface, (indicator_x, indicator_y))
    
    # Add moving indicator label
    indicator_text = font_small.render("MOVING INDICATOR", True, (255, 255, 255))
    surface.blit(indicator_text, (400, 420))
    
    return surface

def main():
    """Main test function"""
    print("🎯 Spout Transparency Test")
    print("=" * 50)
    
    if not is_spout_available():
        print("❌ Spout is not available")
        return
    
    # Initialize pygame
    pygame.init()
    pygame.font.init()
    
    print("This test will help you verify Spout transparency is working.")
    print("Open your Spout receiver (OBS, etc.) and look for:")
    print("• Different opacity levels")
    print("• Transparent background")
    print("• Animated moving indicator")
    print("")
    print("If transparency isn't working, you may need to:")
    print("• Check OBS Spout source settings")
    print("• Try different Spout receiver")
    print("• Verify graphics drivers support alpha")
    print("")
    
    input("Press Enter to start the transparency test...")
    
    # Create Spout sender
    sender = create_spout_sender(
        sender_name="Transparency Test",
        width=800,
        height=600,
        flip_mode="both"  # Use your preferred orientation
    )
    
    if not sender:
        print("❌ Failed to create Spout sender")
        return
    
    print("🚀 Running transparency test...")
    print("⏰ Test will run for 30 seconds")
    print("📺 Check your Spout receiver now!")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while time.time() - start_time < 30:  # Run for 30 seconds
            # Create test pattern
            test_surface = create_transparency_test_pattern(800, 600, frame_count)
            
            # Send via Spout
            success = sender.send_pygame_surface(test_surface)
            
            if not success:
                print("❌ Failed to send frame")
                break
            
            frame_count += 1
            
            # Show progress every 5 seconds
            elapsed = time.time() - start_time
            if frame_count % 150 == 0:  # Every 5 seconds at 30fps
                print(f"⏱️  Test progress: {elapsed:.1f}s / 30s (Frame {frame_count})")
            
            time.sleep(1/30)  # 30 FPS
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    finally:
        sender.stop()
        pygame.quit()
        
        print(f"\n✅ Transparency test completed!")
        print(f"📊 Total frames sent: {frame_count}")
        print("")
        print("🔍 Analysis:")
        print("If you saw different opacity levels → Transparency is working! ✅")
        print("If everything looked opaque → Transparency needs configuration ⚙️")
        print("")
        print("💡 OBS Studio Tips:")
        print("• Add Spout2 Capture source")
        print("• Right-click source → Filters → Color Correction")
        print("• Or check if 'Allow Transparency' is enabled in source properties")

if __name__ == "__main__":
    main()