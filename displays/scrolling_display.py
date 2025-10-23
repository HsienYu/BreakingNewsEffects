import numpy as np
import sys
import os
import time
import pygame
import threading
import queue
from .ndi_sender import NDISender, is_ndi_available
from .simple_streamer import create_simple_streamer
from .spout_sender import SpoutSender, is_spout_available

# Properly import Syphon for macOS
SYPHON_AVAILABLE = False
try:
    # Check if we're on macOS
    if sys.platform == 'darwin':
        try:
            import syphon
            print("Successfully imported syphon module")
            SYPHON_AVAILABLE = True
        except ImportError:
            print("syphon module not found. Install with: pip install syphon-python")
except Exception as e:
    print(f"Error initializing Syphon: {e}")


class ScrollingNewsDisplay:
    """A display for scrolling news headlines using pygame with Syphon and NDI output"""

    def __init__(self, width=1280, height=360, bg_color=(0, 0, 0, 0), text_color=(255, 255, 255),
                 ndi_config=None, transparent_bg=True, green_screen=False):
        # Initialize pygame in the main thread
        pygame.init()

        # Set up the resizable window with transparency
        self.width = width
        self.height = height
        # Use RESIZABLE flag and SRCALPHA for transparent background
        self.screen = pygame.display.set_mode(
            (width, height), pygame.RESIZABLE | pygame.SRCALPHA)
        pygame.display.set_caption("Breaking News")

        # Ensure we're using a display mode that supports alpha
        pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

        # Set up Syphon with full HD resolution
        self.syphon_width = 3840
        self.syphon_height = 1080
        self.syphon_server = None
        self.syphon_texture = None
        self.syphon_is_metal = False

        # Use the global SYPHON_AVAILABLE variable
        global SYPHON_AVAILABLE
        if SYPHON_AVAILABLE:
            try:
                import numpy as np
                # Only import Metal utils if we use Metal
                self.syphon_surface = pygame.Surface(
                    (self.syphon_width, self.syphon_height), pygame.SRCALPHA, 32)
                if hasattr(syphon.server, 'SyphonMetalServer'):
                    from syphon.utils.numpy import copy_image_to_mtl_texture
                    from syphon.utils.raw import create_mtl_texture
                    self.syphon_server = syphon.server.SyphonMetalServer(
                        name="Breaking News")
                    # Create texture with the server's device
                    self.syphon_texture = create_mtl_texture(
                        self.syphon_server.device,
                        self.syphon_width,
                        self.syphon_height)
                    self.syphon_is_metal = True
                    self.copy_to_texture = copy_image_to_mtl_texture
                else:
                    import OpenGL.GL as gl
                    from syphon.utils.gl import copy_surface_to_texture
                    import ctypes

                    self.syphon_server = syphon.server.SyphonServer(
                        name="Breaking News")
                    self.syphon_texture = gl.glGenTextures(1)
                    self.copy_to_texture = copy_surface_to_texture

                    # Enable blending for transparency in OpenGL
                    gl.glEnable(gl.GL_BLEND)
                    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

                print("Syphon server initialized")
            except Exception as e:
                print(f"Error setting up Syphon: {e}")
                SYPHON_AVAILABLE = False

        # Set up video streaming (Spout > NDI > Simple Streamer)
        self.spout_sender = None
        self.spout_enabled = False
        self.ndi_sender = None
        self.ndi_enabled = False
        self.simple_streamer = None
        self.streaming_enabled = False
        
        if ndi_config is None:
            ndi_config = {}
        
        # Default NDI/streaming configuration
        streaming_defaults = {
            'enabled': True,
            'sender_name': 'Breaking News Effects',
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'fallback_method': 'http',  # 'http' or 'udp' for simple streaming
            'fallback_port': 8080
        }
        
        # Merge user config with defaults
        streaming_settings = {**streaming_defaults, **ndi_config}
        
        if streaming_settings.get('enabled', True):
            # Try Spout first (best for Windows)
            if is_spout_available():
                try:
                    self.spout_sender = SpoutSender(
                        sender_name=streaming_settings['sender_name'],
                        width=streaming_settings['width'],
                        height=streaming_settings['height'],
                        flip_mode=streaming_settings.get('spout_flip_mode', 'both')
                    )
                    
                    if self.spout_sender.is_initialized:
                        self.spout_enabled = True
                        self.streaming_enabled = True
                        print(f"🎯 Spout sender enabled: {streaming_settings['sender_name']}")
                        print("   Compatible with OBS Studio, Resolume, TouchDesigner, etc.")
                    else:
                        self.spout_sender = None
                        print("❌ Spout sender failed to initialize")
                        
                except Exception as e:
                    print(f"❌ Error setting up Spout sender: {e}")
                    self.spout_sender = None
            
            # If Spout failed, try NDI as backup
            if not self.spout_enabled and is_ndi_available():
                try:
                    print("🔄 Spout not available, trying NDI...")
                    self.ndi_sender = NDISender(
                        sender_name=streaming_settings['sender_name'],
                        width=streaming_settings['width'],
                        height=streaming_settings['height'],
                        frame_rate=(streaming_settings['fps'], 1)
                    )
                    
                    if self.ndi_sender.is_initialized:
                        self.ndi_enabled = True
                        self.streaming_enabled = True
                        print(f"✅ NDI sender enabled: {streaming_settings['sender_name']}")
                    else:
                        self.ndi_sender = None
                        print("❌ NDI sender failed to initialize")
                        
                except Exception as e:
                    print(f"❌ Error setting up NDI sender: {e}")
                    self.ndi_sender = None
            
            # If both Spout and NDI failed, try simple streamer as fallback
            if not self.spout_enabled and not self.ndi_enabled:
                try:
                    print("🔄 Spout and NDI not available, trying simple streamer fallback...")
                    self.simple_streamer = create_simple_streamer(
                        stream_name=streaming_settings['sender_name'],
                        method=streaming_settings.get('fallback_method', 'http'),
                        port=streaming_settings.get('fallback_port', 8080),
                        width=streaming_settings['width'],
                        height=streaming_settings['height'],
                        fps=streaming_settings['fps']
                    )
                    
                    if self.simple_streamer and self.simple_streamer.is_initialized:
                        self.streaming_enabled = True
                        method = streaming_settings.get('fallback_method', 'http')
                        port = streaming_settings.get('fallback_port', 8080)
                        if method == 'http':
                            print(f"✅ HTTP streamer enabled at http://localhost:{port}/")
                        else:
                            print(f"✅ UDP streamer enabled on port {port}")
                    else:
                        self.simple_streamer = None
                        print("❌ Simple streamer failed to initialize")
                        
                except Exception as e:
                    print(f"❌ Error setting up simple streamer: {e}")
                    self.simple_streamer = None

        # Set up text properties
        self.bg_color = bg_color
        self.text_color = text_color
        self.transparent_bg = transparent_bg
        self.green_screen = green_screen
        self.default_font = pygame.font.Font(None, 28)  # Smaller font (was 48)
        self.breaking_font = pygame.font.Font(
            None, 60)  # Cache breaking news font (not used anymore)

        # Initialize scrolling text (bottom bar only)
        self.scrolling_queue = []  # Queue for bottom scrolling text
        self.current_news = None
        self.current_x_float = float(self.width)  # Use float for sub-pixel precision
        self.scroll_speed = 2.5  # Scroll speed for scrolling text
        self.current_scrolling_index = 0  # Track which news item is scrolling

        # For thread safety
        self.running = True
        self.lock = threading.Lock()

        # Performance optimizations - cache surfaces
        self.cached_breaking_text = None
        self.cached_text_bg = None
        self.cached_red_bar = None
        self.last_window_size = (width, height)

        # Text surface caching for scrolling news
        self.text_surface_cache = {}
        self.max_cache_size = 20  # Limit cache size

        # Frame rate control for smooth scrolling
        self.target_fps = 60  # Keep 60 FPS for smooth text scrolling
        self.syphon_update_counter = 0
        self.syphon_update_interval = 4  # Update Syphon every 4 frames (15 FPS) to maintain performance

    def show_news(self, text):
        """Add a news item to the scrolling queue"""
        if text not in self.scrolling_queue:  # Avoid duplicates
            self.scrolling_queue.append(text)

    def update(self):
        """Update the display - should be called in the main loop"""
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), pygame.RESIZABLE | pygame.SRCALPHA)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

        # Clear the screen with appropriate background
        if self.green_screen:
            self.screen.fill((0, 255, 0, 255))  # Pure green for chroma key
        elif self.transparent_bg:
            self.screen.fill((0, 0, 0, 0))  # Transparent
        else:
            self.screen.fill((0, 0, 0, 255))  # Black background

        # Cache surfaces to improve performance - only recreate when window size changes
        current_size = (self.width, self.height)
        bar_height = 25  # Thinner bar (was 40)
        
        if self.last_window_size != current_size or self.cached_red_bar is None:
            # Create a thinner red bar at the bottom of the screen
            self.cached_red_bar = pygame.Surface(
                (self.width, bar_height), pygame.SRCALPHA)
            self.cached_red_bar.fill((200, 0, 0, 220))  # Semi-transparent red

            self.last_window_size = current_size

        red_bar = self.cached_red_bar

        # Draw the red bar at the bottom based on mode
        bottom_y = self.height - bar_height
        if self.green_screen:
            # For green screen: use opaque red bar (will be visible against green)
            self.screen.blit(red_bar, (0, bottom_y))
        elif self.transparent_bg:
            # Make red bar very transparent for overlay use
            transparent_bar = pygame.Surface((self.width, bar_height), pygame.SRCALPHA)
            transparent_bar.fill((200, 0, 0, 100))  # Very transparent red (100/255 = ~40% opacity)
            self.screen.blit(transparent_bar, (0, bottom_y))
        else:
            # Use original semi-transparent red bar
            self.screen.blit(red_bar, (0, bottom_y))

        # Render scrolling text in bottom bar
        if self.scrolling_queue:
            # Get next item to scroll if current is done
            if self.current_news is None:
                if self.current_scrolling_index < len(self.scrolling_queue):
                    self.current_news = self.scrolling_queue[self.current_scrolling_index]
                    self.current_x_float = float(self.width)
                else:
                    # Restart from beginning
                    self.current_scrolling_index = 0
                    self.current_news = self.scrolling_queue[0]
                    self.current_x_float = float(self.width)
            
            # Render scrolling text
            if self.current_news:
                if self.current_news in self.text_surface_cache:
                    text_surface = self.text_surface_cache[self.current_news]
                else:
                    text_surface = self.default_font.render(
                        self.current_news, True, self.text_color)
                    
                    if len(self.text_surface_cache) >= self.max_cache_size:
                        oldest_key = next(iter(self.text_surface_cache))
                        del self.text_surface_cache[oldest_key]
                    
                    self.text_surface_cache[self.current_news] = text_surface
                
                text_width = text_surface.get_width()
                
                # Position in the bottom bar (vertically centered)
                y_pos = bottom_y + (bar_height - text_surface.get_height()) // 2
                
                # Draw the scrolling text
                current_x_int = int(self.current_x_float)
                self.screen.blit(text_surface, (current_x_int, y_pos))
                
                # Scroll with adaptive speed
                adaptive_speed = self.scroll_speed
                if len(self.current_news) > 80:
                    adaptive_speed = self.scroll_speed * 0.8
                elif len(self.current_news) > 120:
                    adaptive_speed = self.scroll_speed * 0.7
                
                self.current_x_float -= adaptive_speed
                
                # If scrolled completely off screen, move to next item
                if self.current_x_float < -text_width:
                    self.current_news = None
                    self.current_scrolling_index += 1
                    if self.current_scrolling_index >= len(self.scrolling_queue):
                        self.current_scrolling_index = 0  # Loop back

        # Update the display
        pygame.display.update()

        # Optimize Syphon updates - only send every few frames to reduce CPU usage
        self.syphon_update_counter += 1
        should_update_syphon = self.syphon_update_counter >= self.syphon_update_interval

        if should_update_syphon:
            self.syphon_update_counter = 0

        # If Syphon is available, send the frame (but less frequently)
        if SYPHON_AVAILABLE and self.syphon_server and should_update_syphon:
            try:
                # Clear the Syphon surface with transparent background first
                self.syphon_surface.fill((0, 0, 0, 0))

                # Scale the pygame surface to Syphon dimensions
                pygame.transform.scale(
                    self.screen,
                    (self.syphon_width, self.syphon_height),
                    self.syphon_surface
                )

                # Send to Syphon
                if self.syphon_is_metal:
                    # Get both RGB and alpha data from the surface
                    rgb_array = pygame.surfarray.pixels3d(self.syphon_surface)
                    alpha_array = pygame.surfarray.pixels_alpha(
                        self.syphon_surface)

                    # Create a 4-channel RGBA array with proper shape (height, width, 4)
                    rgba_array = np.zeros(
                        (self.syphon_height, self.syphon_width, 4), dtype=np.uint8)

                    # Transpose the RGB array and flip it vertically to fix orientation
                    rgb_array_t = np.transpose(rgb_array, (1, 0, 2))
                    rgb_array_t = np.flip(
                        rgb_array_t, axis=0)  # Flip vertically

                    # Transpose and flip the alpha array to match the RGB transformation
                    alpha_array_t = np.transpose(alpha_array, (1, 0))
                    alpha_array_t = np.flip(
                        alpha_array_t, axis=0)  # Flip vertically

                    # Copy the RGB values
                    rgba_array[:, :, 0:3] = rgb_array_t
                    # Copy the alpha values - preserve transparency
                    rgba_array[:, :, 3] = alpha_array_t

                    # Ensure truly transparent pixels (alpha = 0) have zero RGB values
                    transparent_mask = alpha_array_t == 0
                    # Set all channels to 0 for transparent pixels
                    rgba_array[transparent_mask, :] = 0

                    # Send to Syphon
                    self.copy_to_texture(rgba_array, self.syphon_texture)
                    self.syphon_server.publish_frame_texture(
                        self.syphon_texture)
                else:
                    # For OpenGL backend - the OpenGL module should already be imported in the initialization
                    self.copy_to_texture(
                        self.syphon_surface,
                        self.syphon_texture
                    )
                    self.syphon_server.publish_frame(self.syphon_texture)
            except Exception as e:
                print(f"Error publishing to Syphon: {e}")
        
        # Send frame to streaming service if enabled
        if self.streaming_enabled:
            try:
                if self.spout_enabled and self.spout_sender:
                    # Send Spout frames every update for smooth motion
                    self.spout_sender.send_pygame_surface(self.screen)
                elif self.ndi_enabled and self.ndi_sender and should_update_syphon:
                    # NDI can be less frequent (heavier processing)
                    self.ndi_sender.send_pygame_surface(self.screen)
                elif self.simple_streamer and should_update_syphon:
                    # HTTP/UDP can be less frequent
                    self.simple_streamer.send_pygame_surface(self.screen)
            except Exception as e:
                print(f"Error sending streaming frame: {e}")

    def is_running(self):
        """Check if the display is still running"""
        return self.running

    def close(self):
        """Clean up resources"""
        self.running = False

        # Clean up Syphon
        if SYPHON_AVAILABLE and self.syphon_server:
            try:
                self.syphon_server.stop()
            except Exception as e:
                print(f"Error stopping Syphon server: {e}")
        
        # Clean up streaming services
        if self.spout_enabled and self.spout_sender:
            try:
                self.spout_sender.stop()
            except Exception as e:
                print(f"Error stopping Spout sender: {e}")
        
        if self.ndi_enabled and self.ndi_sender:
            try:
                self.ndi_sender.stop()
            except Exception as e:
                print(f"Error stopping NDI sender: {e}")
        
        if self.simple_streamer:
            try:
                self.simple_streamer.stop()
            except Exception as e:
                print(f"Error stopping simple streamer: {e}")

        # Clean up pygame
        pygame.quit()
