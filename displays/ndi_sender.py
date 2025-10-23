import numpy as np
import cv2
import time
import threading
import os
import sys
import subprocess
from typing import Optional, Tuple

# Check NDI availability using different approaches
NDI_AVAILABLE = False
ndi = None
NDI_METHOD = None

# Try different NDI approaches
try:
    # Method 1: Try ndi-python package (if available)
    import ndi
    NDI_AVAILABLE = True
    NDI_METHOD = "ndi-python"
    print("NDI Python bindings successfully imported")
except ImportError:
    try:
        # Method 2: Try PyNDI (alternative package)
        import PyNDI as ndi
        NDI_AVAILABLE = True
        NDI_METHOD = "PyNDI"
        print("PyNDI successfully imported")
    except ImportError:
        # Method 3: Check for NDI SDK installation and use ctypes/FFmpeg approach
        if sys.platform.startswith('win'):
            ndi_paths = [
                os.path.join(os.environ.get('NDI_SDK_DIR', ''), 'Bin', 'x64'),
                r'C:\Program Files\NDI\NDI 5 SDK\Bin\x64',
                r'C:\Program Files\NDI\NDI SDK\Bin\x64',
                r'C:\Program Files (x86)\NDI\NDI 5 SDK\Bin\x64',
                r'C:\Program Files (x86)\NDI\NDI SDK\Bin\x64'
            ]
            
            for path in ndi_paths:
                if os.path.exists(os.path.join(path, 'Processing.NDI.Lib.x64.dll')):
                    NDI_AVAILABLE = True
                    NDI_METHOD = "ffmpeg-ndi"
                    print(f"NDI SDK found at: {path}")
                    print("Will use FFmpeg-based NDI streaming")
                    break
        
        if not NDI_AVAILABLE:
            print("NDI not available. Install options:")
            print("1. Install ndi-python: pip install ndi-python")
            print("2. Install PyNDI: pip install PyNDI")
            print("3. Install NDI SDK from https://ndi.video/")
except Exception as e:
    print(f"Error checking NDI availability: {e}")


class NDISender:
    """NDI sender for streaming video frames over the network"""
    
    def __init__(self, 
                 sender_name: str = "Breaking News Effects",
                 width: int = 1920,
                 height: int = 1080,
                 frame_rate: Tuple[int, int] = (30, 1),  # 30/1 = 30fps
                 enable_audio: bool = False):
        """
        Initialize NDI sender
        
        Args:
            sender_name: Name of the NDI source
            width: Video width in pixels
            height: Video height in pixels  
            frame_rate: Frame rate as (numerator, denominator) tuple
            enable_audio: Whether to enable audio support
        """
        self.sender_name = sender_name
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.enable_audio = enable_audio
        
        self.sender = None
        self.is_initialized = False
        self.is_sending = False
        self.last_frame_time = 0
        self.frame_interval = frame_rate[1] / frame_rate[0]  # Time between frames in seconds
        self.ffmpeg_process = None  # For FFmpeg-based NDI
        
        # Thread safety
        self.lock = threading.Lock()
        
        if NDI_AVAILABLE:
            if NDI_METHOD in ["ndi-python", "PyNDI"]:
                self._initialize_ndi_direct()
            elif NDI_METHOD == "ffmpeg-ndi":
                self._initialize_ndi_ffmpeg()
        else:
            print("NDI not available - sender will not function")
    
    def _initialize_ndi_direct(self):
        """Initialize the NDI sender using direct NDI libraries"""
        try:
            # Initialize NDI
            if not ndi.initialize():
                print("Failed to initialize NDI")
                return
                
            # Create NDI send settings
            send_settings = ndi.SendCreate()
            send_settings.ndi_name = self.sender_name.encode('utf-8')
            
            # Create the sender
            self.sender = ndi.send_create(send_settings)
            if not self.sender:
                print("Failed to create NDI sender")
                return
                
            self.is_initialized = True
            self.is_sending = True
            print(f"NDI sender '{self.sender_name}' initialized successfully ({NDI_METHOD})")
            print(f"  Resolution: {self.width}x{self.height}")
            print(f"  Frame rate: {self.frame_rate[0]}/{self.frame_rate[1]} fps")
            
        except Exception as e:
            print(f"Error initializing NDI sender: {e}")
            self.is_initialized = False
    
    def _initialize_ndi_ffmpeg(self):
        """Initialize NDI sender using FFmpeg with NDI output"""
        try:
            # Check if FFmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                print("FFmpeg not found. Please install FFmpeg with NDI support")
                return
            
            print(f"Initializing FFmpeg-based NDI sender '{self.sender_name}'")
            print(f"  Resolution: {self.width}x{self.height}")
            print(f"  Frame rate: {self.frame_rate[0]}/{self.frame_rate[1]} fps")
            print("  Note: This method requires FFmpeg with NDI support")
            
            # We'll create the FFmpeg process when we start sending frames
            self.is_initialized = True
            self.is_sending = True
            
        except Exception as e:
            print(f"Error initializing FFmpeg NDI sender: {e}")
            self.is_initialized = False
    
    def send_frame(self, frame_data: np.ndarray) -> bool:
        """
        Send a frame over NDI
        
        Args:
            frame_data: Numpy array containing the frame data (RGBA format expected)
            
        Returns:
            True if frame was sent successfully, False otherwise
        """
        if not self.is_initialized:
            return False
            
        try:
            with self.lock:
                # Check frame rate limiting
                current_time = time.time()
                if current_time - self.last_frame_time < self.frame_interval:
                    return True  # Skip frame to maintain target frame rate
                
                if NDI_METHOD in ["ndi-python", "PyNDI"]:
                    success = self._send_frame_direct(frame_data)
                elif NDI_METHOD == "ffmpeg-ndi":
                    success = self._send_frame_ffmpeg(frame_data)
                else:
                    success = False
                
                if success:
                    self.last_frame_time = current_time
                
                return success
                
        except Exception as e:
            print(f"Error sending NDI frame: {e}")
            return False
    
    def _send_frame_direct(self, frame_data: np.ndarray) -> bool:
        """Send frame using direct NDI libraries"""
        if not self.sender:
            return False
            
        try:
            # Ensure frame data is in the correct format
            if frame_data.dtype != np.uint8:
                frame_data = frame_data.astype(np.uint8)
            
            # Convert RGBA to BGRA (NDI prefers BGRA format)
            if len(frame_data.shape) == 3 and frame_data.shape[2] == 4:
                # RGBA to BGRA conversion
                bgra_frame = frame_data.copy()
                bgra_frame[:, :, [0, 2]] = bgra_frame[:, :, [2, 0]]  # Swap R and B channels
            elif len(frame_data.shape) == 3 and frame_data.shape[2] == 3:
                # RGB to BGRA conversion
                bgra_frame = np.zeros((frame_data.shape[0], frame_data.shape[1], 4), dtype=np.uint8)
                bgra_frame[:, :, [2, 1, 0]] = frame_data  # RGB to BGR
                bgra_frame[:, :, 3] = 255  # Full alpha
            else:
                print(f"Unsupported frame format: {frame_data.shape}")
                return False
            
            # Ensure frame is the correct size
            if bgra_frame.shape[:2] != (self.height, self.width):
                bgra_frame = cv2.resize(bgra_frame, (self.width, self.height))
            
            # Create NDI video frame
            video_frame = ndi.VideoFrameV2()
            video_frame.data = bgra_frame
            video_frame.line_stride_in_bytes = self.width * 4  # 4 bytes per pixel (BGRA)
            video_frame.xres = self.width
            video_frame.yres = self.height
            video_frame.frame_rate_N = self.frame_rate[0]
            video_frame.frame_rate_D = self.frame_rate[1]
            video_frame.picture_aspect_ratio = self.width / self.height
            video_frame.frame_format_type = ndi.FRAME_FORMAT_TYPE_PROGRESSIVE
            video_frame.fourcc = ndi.FOURCC_VIDEO_TYPE_BGRX  # BGRA format
            
            # Send the frame
            ndi.send_send_video_v2(self.sender, video_frame)
            return True
            
        except Exception as e:
            print(f"Error in direct NDI send: {e}")
            return False
    
    def _send_frame_ffmpeg(self, frame_data: np.ndarray) -> bool:
        """Send frame using FFmpeg with NDI output"""
        try:
            # Create FFmpeg process if not already created
            if self.ffmpeg_process is None:
                self._start_ffmpeg_process()
                
            if self.ffmpeg_process is None:
                return False
            
            # Ensure frame data is in the correct format
            if frame_data.dtype != np.uint8:
                frame_data = frame_data.astype(np.uint8)
            
            # Convert to RGB if needed and ensure correct size
            if len(frame_data.shape) == 3 and frame_data.shape[2] == 4:
                # RGBA to RGB conversion (drop alpha)
                rgb_frame = frame_data[:, :, :3]
            elif len(frame_data.shape) == 3 and frame_data.shape[2] == 3:
                rgb_frame = frame_data
            else:
                print(f"Unsupported frame format for FFmpeg: {frame_data.shape}")
                return False
            
            # Ensure frame is the correct size
            if rgb_frame.shape[:2] != (self.height, self.width):
                rgb_frame = cv2.resize(rgb_frame, (self.width, self.height))
            
            # Write frame to FFmpeg process
            self.ffmpeg_process.stdin.write(rgb_frame.tobytes())
            self.ffmpeg_process.stdin.flush()
            
            return True
            
        except Exception as e:
            print(f"Error in FFmpeg NDI send: {e}")
            # If there's an error, try to restart the process
            self._stop_ffmpeg_process()
            return False
    
    def _start_ffmpeg_process(self):
        """Start the FFmpeg process for NDI streaming"""
        try:
            cmd = [
                'ffmpeg',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', f'{self.width}x{self.height}',
                '-r', str(self.frame_rate[0]),
                '-i', '-',  # Read from stdin
                '-f', 'libndi_newtek',
                '-pix_fmt', 'uyvy422',
                '-ndi_name', self.sender_name,
                '-'
            ]
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            print(f"FFmpeg NDI process started for '{self.sender_name}'")
            
        except Exception as e:
            print(f"Error starting FFmpeg process: {e}")
            self.ffmpeg_process = None
    
    def _stop_ffmpeg_process(self):
        """Stop the FFmpeg process"""
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except Exception as e:
                print(f"Error stopping FFmpeg process: {e}")
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass
            finally:
                self.ffmpeg_process = None
    
    def send_pygame_surface(self, surface) -> bool:
        """
        Send a pygame surface as an NDI frame
        
        Args:
            surface: pygame Surface object
            
        Returns:
            True if frame was sent successfully, False otherwise
        """
        if not self.is_initialized:
            return False
            
        try:
            # Get pixel data from pygame surface
            # pygame uses RGB format by default
            rgb_array = np.array(surface.convert().get_view('3'), dtype=np.uint8)
            
            # pygame surfaces are in (width, height, channels) format
            # We need (height, width, channels) for OpenCV/NDI
            if len(rgb_array.shape) == 3:
                rgb_array = np.transpose(rgb_array, (1, 0, 2))
            
            # Handle alpha channel if present
            try:
                alpha_array = np.array(surface.get_view('A'), dtype=np.uint8)
                alpha_array = np.transpose(alpha_array, (1, 0))
                
                # Create RGBA array
                rgba_array = np.zeros((rgb_array.shape[0], rgb_array.shape[1], 4), dtype=np.uint8)
                rgba_array[:, :, :3] = rgb_array
                rgba_array[:, :, 3] = alpha_array
                
                return self.send_frame(rgba_array)
                
            except ValueError:
                # No alpha channel, create one
                rgba_array = np.zeros((rgb_array.shape[0], rgb_array.shape[1], 4), dtype=np.uint8)
                rgba_array[:, :, :3] = rgb_array
                rgba_array[:, :, 3] = 255  # Full opacity
                
                return self.send_frame(rgba_array)
                
        except Exception as e:
            print(f"Error converting pygame surface for NDI: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if NDI sender is connected and has receivers"""
        if not self.is_initialized:
            return False
            
        try:
            if NDI_METHOD in ["ndi-python", "PyNDI"] and self.sender:
                # Check for connections using direct NDI
                connection_count = ndi.send_get_no_connections(self.sender, timeout_in_ms=0)
                return connection_count > 0
            elif NDI_METHOD == "ffmpeg-ndi":
                # For FFmpeg, we can't easily check connections, so assume connected if process is running
                return self.ffmpeg_process is not None and self.ffmpeg_process.poll() is None
            else:
                return False
        except Exception as e:
            print(f"Error checking NDI connections: {e}")
            return False
    
    def get_connection_count(self) -> int:
        """Get the number of active NDI receivers connected to this sender"""
        if not self.is_initialized:
            return 0
            
        try:
            if NDI_METHOD in ["ndi-python", "PyNDI"] and self.sender:
                return ndi.send_get_no_connections(self.sender, timeout_in_ms=0)
            elif NDI_METHOD == "ffmpeg-ndi":
                # For FFmpeg, we can't get exact connection count, so return 1 if process is running
                return 1 if (self.ffmpeg_process is not None and self.ffmpeg_process.poll() is None) else 0
            else:
                return 0
        except Exception as e:
            print(f"Error getting NDI connection count: {e}")
            return 0
    
    def stop(self):
        """Stop the NDI sender and cleanup resources"""
        if self.is_sending:
            self.is_sending = False
            
        try:
            if NDI_METHOD in ["ndi-python", "PyNDI"] and self.sender:
                ndi.send_destroy(self.sender)
                self.sender = None
                print(f"NDI sender '{self.sender_name}' stopped")
            elif NDI_METHOD == "ffmpeg-ndi":
                self._stop_ffmpeg_process()
                print(f"FFmpeg NDI sender '{self.sender_name}' stopped")
        except Exception as e:
            print(f"Error stopping NDI sender: {e}")
        
        if NDI_AVAILABLE and NDI_METHOD in ["ndi-python", "PyNDI"]:
            try:
                ndi.destroy()
            except Exception as e:
                print(f"Error destroying NDI: {e}")
                
        self.is_initialized = False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()


def is_ndi_available() -> bool:
    """Check if NDI is available on this system"""
    return NDI_AVAILABLE


def create_ndi_sender(sender_name: str = "Breaking News Effects", 
                     width: int = 1920, 
                     height: int = 1080,
                     fps: int = 30) -> Optional[NDISender]:
    """
    Convenience function to create an NDI sender
    
    Args:
        sender_name: Name of the NDI source
        width: Video width
        height: Video height
        fps: Frame rate in frames per second
        
    Returns:
        NDISender instance if successful, None otherwise
    """
    if not NDI_AVAILABLE:
        print("NDI not available")
        return None
        
    try:
        sender = NDISender(
            sender_name=sender_name,
            width=width,
            height=height,
            frame_rate=(fps, 1)
        )
        
        if sender.is_initialized:
            return sender
        else:
            return None
            
    except Exception as e:
        print(f"Error creating NDI sender: {e}")
        return None