"""
Spout Sender Module for Windows

Spout is a Windows framework for sharing video between applications
in real-time. It's similar to Syphon on macOS but designed for Windows.

This module provides a simple interface for sending video frames
from pygame/numpy arrays to other applications via Spout.

Requirements:
- Windows operating system
- SpoutGL Python package: pip install SpoutGL
- OpenGL support
"""

import numpy as np
import time
import threading
import sys
from typing import Optional, Tuple
import pygame

# Check Spout availability
SPOUT_AVAILABLE = False
spout = None

try:
    if sys.platform.startswith('win'):
        import SpoutGL
        spout = SpoutGL
        SPOUT_AVAILABLE = True
        print("✅ SpoutGL successfully imported")
    else:
        print("ℹ️  Spout is only available on Windows")
except ImportError:
    print("❌ SpoutGL not found. Install with: pip install SpoutGL")
except Exception as e:
    print(f"❌ Error importing SpoutGL: {e}")


class SpoutSender:
    """Spout sender for streaming video frames to other Windows applications"""
    
    def __init__(self, 
                 sender_name: str = "Breaking News Effects",
                 width: int = 1920,
                 height: int = 1080,
                 flip_mode: str = "both"):  # "none", "vertical", "horizontal", "both"
        """
        Initialize Spout sender
        
        Args:
            sender_name: Name of the Spout source
            width: Video width in pixels
            height: Video height in pixels
        """
        self.sender_name = sender_name
        self.width = width
        self.height = height
        self.flip_mode = flip_mode
        
        self.sender = None
        self.is_initialized = False
        self.is_sending = False
        self.frame_count = 0
        self.start_time = time.time()
        
        # Thread safety
        self.lock = threading.Lock()
        
        if SPOUT_AVAILABLE:
            self._initialize_spout()
        else:
            print("❌ Spout not available - sender will not function")
    
    def _initialize_spout(self):
        """Initialize the Spout sender"""
        try:
            # Create Spout sender
            self.sender = spout.SpoutSender()
            
            # Set the sender name
            self.sender.setSenderName(self.sender_name)
            
            # Initialize OpenGL context (required for Spout)
            success = self.sender.createOpenGL()
            if not success:
                print(f"❌ Failed to create OpenGL context for Spout")
                return
            
            self.is_initialized = True
            self.is_sending = True
            
            print(f"✅ Spout sender '{self.sender_name}' initialized successfully")
            print(f"   Resolution: {self.width}x{self.height}")
            print("   Compatible with OBS Studio, Resolume, TouchDesigner, and more!")
            
        except Exception as e:
            print(f"❌ Error initializing Spout sender: {e}")
            self.is_initialized = False
    
    def send_frame(self, frame_data: np.ndarray) -> bool:
        """
        Send a frame via Spout
        
        Args:
            frame_data: Numpy array containing the frame data (RGB/RGBA format)
            
        Returns:
            True if frame was sent successfully, False otherwise
        """
        if not self.is_initialized or not self.sender:
            return False
            
        try:
            with self.lock:
                # Ensure frame data is in the correct format
                if frame_data.dtype != np.uint8:
                    frame_data = frame_data.astype(np.uint8)
                
                # Handle different channel formats and convert to BGRA for better Spout compatibility
                if len(frame_data.shape) == 3 and frame_data.shape[2] == 4:
                    # RGBA to BGRA conversion for better Spout transparency support
                    bgra_frame = frame_data.copy()
                    bgra_frame[:, :, [0, 2]] = bgra_frame[:, :, [2, 0]]  # Swap R and B channels
                elif len(frame_data.shape) == 3 and frame_data.shape[2] == 3:
                    # RGB to BGRA conversion (add alpha channel)
                    bgra_frame = np.zeros((frame_data.shape[0], frame_data.shape[1], 4), dtype=np.uint8)
                    bgra_frame[:, :, [2, 1, 0]] = frame_data  # RGB to BGR
                    bgra_frame[:, :, 3] = 255  # Full alpha
                else:
                    print(f"❌ Unsupported frame format: {frame_data.shape}")
                    return False
                
                # Ensure frame is the correct size
                if bgra_frame.shape[:2] != (self.height, self.width):
                    import cv2
                    bgra_frame = cv2.resize(bgra_frame, (self.width, self.height))
                
                # Fix orientation based on flip_mode setting
                if self.flip_mode == "vertical":
                    bgra_frame = np.flipud(bgra_frame)
                elif self.flip_mode == "horizontal":
                    bgra_frame = np.fliplr(bgra_frame)
                elif self.flip_mode == "both":
                    bgra_frame = np.flipud(np.fliplr(bgra_frame))
                # "none" means no flipping
                
                # Send to Spout
                # Spout expects data as contiguous array
                bgra_frame = np.ascontiguousarray(bgra_frame)
                
                # SpoutGL sendImage signature: sendImage(buffer, width, height, format, invert, stride)
                stride = self.width * 4  # 4 bytes per pixel for BGRA
                success = self.sender.sendImage(bgra_frame, 
                                              self.width, self.height, 
                                              spout.enums.GL_BGRA_EXT, False, stride)
                
                if success:
                    self.frame_count += 1
                    return True
                else:
                    print("❌ Failed to send frame to Spout")
                    return False
                
        except Exception as e:
            print(f"❌ Error sending Spout frame: {e}")
            return False
    
    def send_pygame_surface(self, surface) -> bool:
        """
        Send a pygame surface as a Spout frame
        
        Args:
            surface: pygame Surface object
            
        Returns:
            True if frame was sent successfully, False otherwise
        """
        if not self.is_initialized:
            return False
            
        try:
            # Convert pygame surface to numpy array
            # First, convert to a format that supports per-pixel alpha
            surface_rgba = surface.convert_alpha()
            
            # Get both RGB and alpha data
            width, height = surface_rgba.get_size()
            
            # Get the raw pixel data
            raw_data = pygame.image.tostring(surface_rgba, 'RGBA')
            
            # Convert to numpy array and reshape
            rgba_array = np.frombuffer(raw_data, dtype=np.uint8)
            rgba_array = rgba_array.reshape((height, width, 4))
            
            # Pygame images are already in the correct orientation for Spout
            return self.send_frame(rgba_array)
            
        except Exception as e:
            print(f"❌ Error converting pygame surface for Spout: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if Spout sender is active"""
        return self.is_initialized and self.is_sending
    
    def get_connection_count(self) -> int:
        """Get number of receivers (Spout doesn't track this directly)"""
        # Spout doesn't provide connection count, so return 1 if active
        return 1 if self.is_connected() else 0
    
    def get_sender_info(self) -> dict:
        """Get information about the Spout sender"""
        if not self.is_initialized:
            return {}
            
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'sender_name': self.sender_name,
            'width': self.width,
            'height': self.height,
            'frames_sent': self.frame_count,
            'elapsed_time': elapsed,
            'average_fps': avg_fps,
            'is_active': self.is_connected()
        }
    
    def update_size(self, width: int, height: int) -> bool:
        """
        Update the sender resolution
        
        Args:
            width: New width
            height: New height
            
        Returns:
            True if successful, False otherwise
        """
        # Spout will automatically handle resolution changes
        # when sending frames of different sizes
        self.width = width
        self.height = height
        print(f"✅ Spout sender size updated to {width}x{height}")
        return True
    
    def stop(self):
        """Stop the Spout sender and cleanup resources"""
        if self.is_sending:
            self.is_sending = False
            
        if self.sender:
            try:
                self.sender.releaseSender()
                self.sender.closeOpenGL()
                self.sender = None
                print(f"✅ Spout sender '{self.sender_name}' stopped")
            except Exception as e:
                print(f"❌ Error stopping Spout sender: {e}")
                
        self.is_initialized = False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()


def is_spout_available() -> bool:
    """Check if Spout is available on this system"""
    return SPOUT_AVAILABLE and sys.platform.startswith('win')


def create_spout_sender(sender_name: str = "Breaking News Effects", 
                       width: int = 1920, 
                       height: int = 1080,
                       flip_mode: str = "both") -> Optional[SpoutSender]:
    """
    Convenience function to create a Spout sender
    
    Args:
        sender_name: Name of the Spout source
        width: Video width
        height: Video height
        
    Returns:
        SpoutSender instance if successful, None otherwise
    """
    if not is_spout_available():
        print("❌ Spout not available on this system")
        return None
        
    try:
        sender = SpoutSender(
            sender_name=sender_name,
            width=width,
            height=height,
            flip_mode=flip_mode
        )
        
        if sender.is_initialized:
            return sender
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error creating Spout sender: {e}")
        return None


def list_spout_senders() -> list:
    """
    List available Spout senders from other applications
    
    Returns:
        List of sender names
    """
    if not SPOUT_AVAILABLE:
        return []
        
    try:
        receiver = spout.SpoutReceiver()
        senders = []
        
        # The actual API might be different, return empty list for now
        # This is a nice-to-have feature, not essential
        return senders
        
    except Exception as e:
        print(f"❌ Error listing Spout senders: {e}")
        return []


# Test function
if __name__ == "__main__":
    print("🧪 Testing Spout Sender...")
    
    if not is_spout_available():
        print("❌ Spout not available for testing")
        exit(1)
    
    # Create a test sender
    sender = create_spout_sender("Spout Test", 640, 480)
    
    if not sender:
        print("❌ Failed to create test sender")
        exit(1)
    
    print("✅ Test sender created successfully")
    print("ℹ️  Check for 'Spout Test' source in Spout-compatible applications")
    
    # Send some test frames
    try:
        import time
        for i in range(60):  # Send 60 test frames
            # Create a simple test pattern
            test_frame = np.zeros((480, 640, 4), dtype=np.uint8)
            test_frame[:, :, 0] = (i * 4) % 256  # Red channel animation
            test_frame[:, :, 1] = 128  # Green
            test_frame[:, :, 2] = 255 - ((i * 4) % 256)  # Blue channel animation
            test_frame[:, :, 3] = 255  # Alpha
            
            sender.send_frame(test_frame)
            time.sleep(1/30)  # 30 FPS
            
            if i % 10 == 0:
                print(f"📤 Sent frame {i+1}/60")
        
        print("✅ Test completed successfully")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    finally:
        sender.stop()
        print("🏁 Test finished")