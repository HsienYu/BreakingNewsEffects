"""
Simple Video Streamer - NDI Alternative

This module provides a simple video streaming solution that can be used
when NDI is not available or difficult to set up. It uses HTTP streaming
or UDP streaming as alternatives.

This is particularly useful for:
1. Development and testing
2. Systems where NDI SDK is not available
3. Quick setup without complex dependencies
"""

import numpy as np
import cv2
import time
import threading
import socket
import struct
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
from typing import Optional, Tuple
import queue
import io
import base64


class UDPVideoStreamer:
    """Simple UDP-based video streamer"""
    
    def __init__(self, 
                 stream_name: str = "Breaking News Effects",
                 host: str = "127.0.0.1",
                 port: int = 8888,
                 width: int = 1920,
                 height: int = 1080,
                 fps: int = 30,
                 quality: int = 85):
        """
        Initialize UDP video streamer
        
        Args:
            stream_name: Name of the stream
            host: Host address to bind to
            port: UDP port to use
            width: Video width
            height: Video height
            fps: Frame rate
            quality: JPEG compression quality (1-100)
        """
        self.stream_name = stream_name
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        
        self.socket = None
        self.is_initialized = False
        self.is_sending = False
        self.frame_count = 0
        self.start_time = time.time()
        
        self.lock = threading.Lock()
        
        # Frame rate control
        self.frame_interval = 1.0 / fps
        self.last_frame_time = 0
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the UDP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Enable broadcasting if sending to broadcast address
            if self.host.endswith('.255'):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            self.is_initialized = True
            self.is_sending = True
            
            print(f"UDP Video Streamer '{self.stream_name}' initialized")
            print(f"  Address: {self.host}:{self.port}")
            print(f"  Resolution: {self.width}x{self.height}")
            print(f"  Frame rate: {self.fps} fps")
            print(f"  Quality: {self.quality}%")
            
        except Exception as e:
            print(f"Error initializing UDP streamer: {e}")
            self.is_initialized = False
    
    def send_frame(self, frame_data: np.ndarray) -> bool:
        """Send a frame via UDP"""
        if not self.is_initialized or not self.socket:
            return False
        
        try:
            with self.lock:
                # Frame rate limiting
                current_time = time.time()
                if current_time - self.last_frame_time < self.frame_interval:
                    return True
                
                # Convert frame to the correct format and size
                if len(frame_data.shape) == 3 and frame_data.shape[2] == 4:
                    # RGBA to RGB
                    rgb_frame = frame_data[:, :, :3]
                elif len(frame_data.shape) == 3 and frame_data.shape[2] == 3:
                    rgb_frame = frame_data
                else:
                    print(f"Unsupported frame format: {frame_data.shape}")
                    return False
                
                # Resize if needed
                if rgb_frame.shape[:2] != (self.height, self.width):
                    rgb_frame = cv2.resize(rgb_frame, (self.width, self.height))
                
                # Compress to JPEG
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
                success, jpeg_data = cv2.imencode('.jpg', rgb_frame, encode_params)
                
                if not success:
                    return False
                
                # Create packet with header
                packet_data = self._create_packet(jpeg_data.tobytes())
                
                # Send packet (split if too large)
                self._send_packet(packet_data)
                
                self.frame_count += 1
                self.last_frame_time = current_time
                
                return True
                
        except Exception as e:
            print(f"Error sending UDP frame: {e}")
            return False
    
    def _create_packet(self, jpeg_data: bytes) -> bytes:
        """Create a packet with header information"""
        header = struct.pack('!IIIIQ', 
                           0x4E444953,  # Magic number "NDIS" 
                           self.frame_count,
                           self.width,
                           self.height,
                           int(time.time() * 1000000))  # Timestamp in microseconds
        return header + jpeg_data
    
    def _send_packet(self, packet_data: bytes):
        """Send packet data, splitting if necessary"""
        max_packet_size = 65507  # Max UDP packet size
        
        if len(packet_data) <= max_packet_size:
            # Send in single packet
            self.socket.sendto(packet_data, (self.host, self.port))
        else:
            # Split into multiple packets
            chunk_size = max_packet_size - 16  # Reserve space for fragment header
            total_chunks = (len(packet_data) + chunk_size - 1) // chunk_size
            
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = min(start_idx + chunk_size, len(packet_data))
                chunk = packet_data[start_idx:end_idx]
                
                # Add fragment header
                fragment_header = struct.pack('!IIII', 
                                            0x46524147,  # Magic "FRAG"
                                            self.frame_count,
                                            i,  # Fragment number
                                            total_chunks)  # Total fragments
                
                fragment_packet = fragment_header + chunk
                self.socket.sendto(fragment_packet, (self.host, self.port))
    
    def send_pygame_surface(self, surface) -> bool:
        """Send a pygame surface as a frame"""
        try:
            # Convert pygame surface to numpy array
            rgb_array = np.array(surface.convert().get_view('3'), dtype=np.uint8)
            
            # pygame surfaces are in (width, height, channels) format
            # We need (height, width, channels) for OpenCV
            if len(rgb_array.shape) == 3:
                rgb_array = np.transpose(rgb_array, (1, 0, 2))
            
            return self.send_frame(rgb_array)
            
        except Exception as e:
            print(f"Error converting pygame surface: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if streamer is active"""
        return self.is_initialized and self.is_sending
    
    def get_connection_count(self) -> int:
        """Return 1 if active (UDP doesn't track connections)"""
        return 1 if self.is_connected() else 0
    
    def get_stats(self) -> dict:
        """Get streaming statistics"""
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'frames_sent': self.frame_count,
            'elapsed_time': elapsed,
            'average_fps': avg_fps,
            'target_fps': self.fps,
            'stream_name': self.stream_name,
            'address': f"{self.host}:{self.port}"
        }
    
    def stop(self):
        """Stop the streamer"""
        self.is_sending = False
        
        if self.socket:
            try:
                self.socket.close()
                self.socket = None
                print(f"UDP Video Streamer '{self.stream_name}' stopped")
            except Exception as e:
                print(f"Error stopping UDP streamer: {e}")
        
        self.is_initialized = False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()


class HTTPVideoStreamer:
    """Simple HTTP-based video streamer (MJPEG stream)"""
    
    def __init__(self, 
                 stream_name: str = "Breaking News Effects",
                 port: int = 8080,
                 width: int = 1920,
                 height: int = 1080,
                 fps: int = 30,
                 quality: int = 85):
        """
        Initialize HTTP video streamer
        
        Args:
            stream_name: Name of the stream
            port: HTTP port to use
            width: Video width
            height: Video height
            fps: Frame rate
            quality: JPEG compression quality (1-100)
        """
        self.stream_name = stream_name
        self.port = port
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        
        self.frame_queue = queue.Queue(maxsize=10)
        self.server = None
        self.server_thread = None
        self.is_initialized = False
        self.is_sending = False
        
        self.frame_count = 0
        self.start_time = time.time()
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the HTTP server"""
        try:
            class StreamHandler(BaseHTTPRequestHandler):
                def __init__(self, streamer, *args, **kwargs):
                    self.streamer = streamer
                    super().__init__(*args, **kwargs)
                
                def do_GET(self):
                    if self.path == '/stream.mjpg':
                        self.send_mjpeg_stream()
                    elif self.path == '/':
                        self.send_index_page()
                    else:
                        self.send_error(404)
                
                def send_mjpeg_stream(self):
                    self.send_response(200)
                    self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    
                    try:
                        while self.streamer.is_sending:
                            try:
                                frame_data = self.streamer.frame_queue.get(timeout=1.0)
                                
                                self.wfile.write(b'\\r\\n--frame\\r\\n')
                                self.wfile.write(b'Content-Type: image/jpeg\\r\\n')
                                self.wfile.write(f'Content-Length: {len(frame_data)}\\r\\n\\r\\n'.encode())
                                self.wfile.write(frame_data)
                                self.wfile.write(b'\\r\\n')
                                
                            except queue.Empty:
                                continue
                            except Exception as e:
                                print(f"Error in MJPEG stream: {e}")
                                break
                    except Exception as e:
                        print(f"Stream connection error: {e}")
                
                def send_index_page(self):
                    html = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>{self.streamer.stream_name}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            img {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
                        </style>
                    </head>
                    <body>
                        <h1>{self.streamer.stream_name}</h1>
                        <p>Resolution: {self.streamer.width}x{self.streamer.height}</p>
                        <p>Frame rate: {self.streamer.fps} fps</p>
                        <img src="/stream.mjpg" alt="Video Stream">
                        <p><a href="/stream.mjpg">Direct MJPEG stream link</a></p>
                    </body>
                    </html>
                    '''
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(html.encode())
                
                def log_message(self, format, *args):
                    # Suppress HTTP server logs
                    pass
            
            # Create handler with reference to this streamer
            def handler_factory(*args, **kwargs):
                return StreamHandler(self, *args, **kwargs)
            
            self.server = HTTPServer(('0.0.0.0', self.port), handler_factory)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.is_initialized = True
            self.is_sending = True
            
            print(f"HTTP Video Streamer '{self.stream_name}' initialized")
            print(f"  URL: http://localhost:{self.port}/")
            print(f"  MJPEG stream: http://localhost:{self.port}/stream.mjpg")
            print(f"  Resolution: {self.width}x{self.height}")
            print(f"  Frame rate: {self.fps} fps")
            
        except Exception as e:
            print(f"Error initializing HTTP streamer: {e}")
            self.is_initialized = False
    
    def send_frame(self, frame_data: np.ndarray) -> bool:
        """Send a frame via HTTP"""
        if not self.is_initialized:
            return False
        
        try:
            # Convert frame to the correct format and size
            if len(frame_data.shape) == 3 and frame_data.shape[2] == 4:
                # RGBA to RGB
                rgb_frame = frame_data[:, :, :3]
            elif len(frame_data.shape) == 3 and frame_data.shape[2] == 3:
                rgb_frame = frame_data
            else:
                print(f"Unsupported frame format: {frame_data.shape}")
                return False
            
            # Resize if needed
            if rgb_frame.shape[:2] != (self.height, self.width):
                rgb_frame = cv2.resize(rgb_frame, (self.width, self.height))
            
            # Compress to JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
            success, jpeg_data = cv2.imencode('.jpg', rgb_frame, encode_params)
            
            if not success:
                return False
            
            # Add to queue (drop oldest frame if queue is full)
            try:
                self.frame_queue.put_nowait(jpeg_data.tobytes())
            except queue.Full:
                # Remove oldest frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(jpeg_data.tobytes())
                except queue.Empty:
                    pass
            
            self.frame_count += 1
            return True
            
        except Exception as e:
            print(f"Error sending HTTP frame: {e}")
            return False
    
    def send_pygame_surface(self, surface) -> bool:
        """Send a pygame surface as a frame"""
        try:
            # Convert pygame surface to numpy array
            rgb_array = np.array(surface.convert().get_view('3'), dtype=np.uint8)
            
            # pygame surfaces are in (width, height, channels) format
            # We need (height, width, channels) for OpenCV
            if len(rgb_array.shape) == 3:
                rgb_array = np.transpose(rgb_array, (1, 0, 2))
            
            return self.send_frame(rgb_array)
            
        except Exception as e:
            print(f"Error converting pygame surface: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if streamer is active"""
        return self.is_initialized and self.is_sending
    
    def get_connection_count(self) -> int:
        """Return approximate number of connected clients"""
        # For HTTP, we can't easily track connections, so return 1 if active
        return 1 if self.is_connected() else 0
    
    def stop(self):
        """Stop the streamer"""
        self.is_sending = False
        
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                
                if self.server_thread:
                    self.server_thread.join(timeout=2.0)
                
                print(f"HTTP Video Streamer '{self.stream_name}' stopped")
            except Exception as e:
                print(f"Error stopping HTTP streamer: {e}")
        
        self.is_initialized = False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()


def create_simple_streamer(stream_name: str = "Breaking News Effects",
                          method: str = "http",
                          port: int = None,
                          width: int = 1920,
                          height: int = 1080,
                          fps: int = 30) -> Optional[object]:
    """
    Create a simple video streamer
    
    Args:
        stream_name: Name of the stream
        method: "http" or "udp"
        port: Port to use (default: 8080 for HTTP, 8888 for UDP)
        width: Video width
        height: Video height
        fps: Frame rate
        
    Returns:
        Streamer instance if successful, None otherwise
    """
    try:
        if method.lower() == "http":
            if port is None:
                port = 8080
            return HTTPVideoStreamer(stream_name, port, width, height, fps)
        elif method.lower() == "udp":
            if port is None:
                port = 8888
            return UDPVideoStreamer(stream_name, "127.0.0.1", port, width, height, fps)
        else:
            print(f"Unknown streaming method: {method}")
            return None
            
    except Exception as e:
        print(f"Error creating streamer: {e}")
        return None