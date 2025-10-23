#!/usr/bin/env python3
"""
Spout Orientation Test Script

This script helps you find the correct orientation setting for your Spout setup.
It will test different flip modes to help you determine which one gives the correct orientation.
"""

import pygame
import numpy as np
import time
from displays.spout_sender import create_spout_sender, is_spout_available

def create_orientation_test_pattern(width, height, mode_name):
    """Create a test pattern with clear orientation markers and mode name"""
    # Create pygame surface
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((50, 50, 50, 255))  # Dark gray background
    
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 24)
    
    # Mode name in center
    mode_text = font_large.render(f"MODE: {mode_name.upper()}", True, (255, 255, 255))
    mode_rect = mode_text.get_rect(center=(width // 2, height // 2))
    surface.blit(mode_text, mode_rect)
    
    # Corner markers with text
    # TOP-LEFT (should be top-left in correct orientation)
    pygame.draw.rect(surface, (255, 0, 0, 255), (0, 0, 120, 60))  # Red
    tl_text = font_small.render("TOP-LEFT", True, (255, 255, 255))
    surface.blit(tl_text, (5, 20))
    
    # TOP-RIGHT (should be top-right in correct orientation)  
    pygame.draw.rect(surface, (0, 255, 0, 255), (width-120, 0, 120, 60))  # Green
    tr_text = font_small.render("TOP-RIGHT", True, (0, 0, 0))
    surface.blit(tr_text, (width-115, 20))
    
    # BOTTOM-LEFT (should be bottom-left in correct orientation)
    pygame.draw.rect(surface, (0, 0, 255, 255), (0, height-60, 120, 60))  # Blue
    bl_text = font_small.render("BOTTOM-LEFT", True, (255, 255, 255))
    surface.blit(bl_text, (5, height-40))
    
    # BOTTOM-RIGHT (should be bottom-right in correct orientation)
    pygame.draw.rect(surface, (255, 255, 0, 255), (width-120, height-60, 120, 60))  # Yellow
    br_text = font_small.render("BOTTOM-RIGHT", True, (0, 0, 0))
    surface.blit(br_text, (width-115, height-40))
    
    # Arrow pointing right (should point right in correct orientation)
    arrow_y = height // 2 + 60
    arrow_points = [
        (width//2 - 40, arrow_y - 10),
        (width//2 + 20, arrow_y),
        (width//2 - 40, arrow_y + 10)
    ]
    pygame.draw.polygon(surface, (255, 0, 255), arrow_points)  # Magenta arrow
    
    arrow_text = font_small.render("ARROW POINTS RIGHT →", True, (255, 255, 255))
    arrow_text_rect = arrow_text.get_rect(center=(width // 2, arrow_y + 25))
    surface.blit(arrow_text, arrow_text_rect)
    
    return surface

def test_flip_mode(mode_name, flip_mode, duration=5):
    """Test a specific flip mode"""
    print(f"\n🧪 Testing flip mode: {mode_name} (flip_mode='{flip_mode}')")
    print("=" * 50)
    
    sender = create_spout_sender(
        sender_name=f"Orientation Test - {mode_name}",
        width=800,
        height=600,
        flip_mode=flip_mode
    )
    
    if not sender:
        print(f"❌ Failed to create sender for {mode_name}")
        return
    
    # Create test pattern
    test_surface = create_orientation_test_pattern(800, 600, mode_name)
    
    # Convert pygame surface to numpy array for direct sending
    raw_data = pygame.image.tostring(test_surface, 'RGBA')
    rgba_array = np.frombuffer(raw_data, dtype=np.uint8)
    rgba_array = rgba_array.reshape((600, 800, 4))
    
    print(f"📺 Sending test pattern for {duration} seconds...")
    print("   Look at your Spout receiver and check if:")
    print("   ✅ Corner labels are in correct positions")
    print("   ✅ Arrow points to the RIGHT")
    print("   ✅ Text is readable (not mirrored)")
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < duration:
        success = sender.send_frame(rgba_array)
        if not success:
            print("❌ Failed to send frame")
            break
        
        frame_count += 1
        time.sleep(1/30)  # 30 FPS
    
    sender.stop()
    print(f"✅ Test completed ({frame_count} frames sent)")
    
    # Pause between tests
    if duration > 0:
        print("⏸️  Pausing 2 seconds before next test...")
        time.sleep(2)

def main():
    """Main test function"""
    print("🎯 Spout Orientation Test")
    print("=" * 50)
    
    if not is_spout_available():
        print("❌ Spout is not available")
        return
    
    # Initialize pygame
    pygame.init()
    pygame.font.init()
    
    print("This script will test different orientation modes.")
    print("Watch your Spout receiver (OBS, etc.) and note which mode looks correct.")
    print("")
    print("For CORRECT orientation, you should see:")
    print("🔴 RED 'TOP-LEFT' in the top-left corner")
    print("🟢 GREEN 'TOP-RIGHT' in the top-right corner") 
    print("🔵 BLUE 'BOTTOM-LEFT' in the bottom-left corner")
    print("🟡 YELLOW 'BOTTOM-RIGHT' in the bottom-right corner")
    print("➡️ Magenta arrow pointing RIGHT")
    print("📝 All text readable (not mirrored)")
    print("")
    
    input("Press Enter to start testing...")
    
    # Test all flip modes
    modes_to_test = [
        ("No Flip", "none"),
        ("Vertical Flip", "vertical"), 
        ("Horizontal Flip", "horizontal"),
        ("Both Flips", "both")
    ]
    
    for mode_name, flip_mode in modes_to_test:
        test_flip_mode(mode_name, flip_mode, duration=7)
    
    print("\n🏁 All tests completed!")
    print("=" * 50)
    print("Which mode looked correct in your Spout receiver?")
    print("You can configure this in your Breaking News application.")
    print("")
    print("To use the correct setting:")
    print("1. Note which flip mode worked")
    print("2. Update your config or code to use that flip_mode")
    print("3. Available options: 'none', 'vertical', 'horizontal', 'both'")
    
    pygame.quit()

if __name__ == "__main__":
    main()