import numpy as np
import sys
import os
import time
import pygame
import threading
import queue

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
    """A display for scrolling news headlines using pygame with Syphon output"""

    def __init__(self, width=1280, height=360, bg_color=(0, 0, 0, 0), text_color=(255, 255, 255)):
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

        # Set up text properties
        self.bg_color = bg_color
        self.text_color = text_color
        self.default_font = pygame.font.Font(None, 48)  # Default font size
        self.breaking_font = pygame.font.Font(
            None, 60)  # Cache breaking news font

        # Initialize a queue for news items
        self.news_queue = queue.Queue()
        self.current_news = None
        self.current_x_float = float(self.width)  # Use float for sub-pixel precision
        self.scroll_speed = 2.5  # Slightly slower but smoother scroll speed

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
        """Add a news item to the queue"""
        self.news_queue.put(text)

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

        # Clear the screen with transparent background
        self.screen.fill((0, 0, 0, 0))

        # Cache surfaces to improve performance - only recreate when window size changes
        current_size = (self.width, self.height)
        if self.last_window_size != current_size or self.cached_red_bar is None:
            # Create a red bar at the bottom of the screen (news channel style)
            bar_height = 40  # Height of the red bottom bar
            self.cached_red_bar = pygame.Surface(
                (self.width, bar_height), pygame.SRCALPHA)
            self.cached_red_bar.fill((200, 0, 0, 220))  # Semi-transparent red

            # Draw "BREAKING NEWS" text with a prominent style
            self.cached_breaking_text = self.breaking_font.render(
                "BREAKING NEWS", True, (255, 255, 0))  # Yellow text for better contrast

            # Create a background for the text
            padding = 15
            self.cached_text_bg = pygame.Surface((self.cached_breaking_text.get_width(
            ) + padding*2, self.cached_breaking_text.get_height() + padding), pygame.SRCALPHA)
            # Semi-transparent red background for the text
            self.cached_text_bg.fill((200, 0, 0, 200))

            self.last_window_size = current_size

        bar_height = 40
        red_bar = self.cached_red_bar
        breaking_text = self.cached_breaking_text
        text_bg = self.cached_text_bg
        padding = 15

        # Position the text in a more prominent position (top left)
        breaking_text_x = 20
        breaking_text_y = 20  # Position at the top of the screen

        # Blit the background first
        self.screen.blit(text_bg, (breaking_text_x - padding,
                         breaking_text_y - padding//2))

        # Draw the text on the screen
        self.screen.blit(breaking_text, (breaking_text_x, breaking_text_y))

        # Blit the red bar at the bottom of the screen
        bottom_y = self.height - bar_height
        self.screen.blit(red_bar, (0, bottom_y))

        # Process news items
        if self.current_news is None and not self.news_queue.empty():
            self.current_news = self.news_queue.get()
            self.current_x_float = float(self.width)  # Start off screen with float precision

        # Render the current news item with caching
        if self.current_news:
            # Check cache first
            if self.current_news in self.text_surface_cache:
                text_surface = self.text_surface_cache[self.current_news]
            else:
                # Render and cache the text surface
                text_surface = self.default_font.render(
                    self.current_news, True, self.text_color)

                # Manage cache size
                if len(self.text_surface_cache) >= self.max_cache_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self.text_surface_cache))
                    del self.text_surface_cache[oldest_key]

                self.text_surface_cache[self.current_news] = text_surface

            text_width = text_surface.get_width()

            # Place text in the red bar (vertically centered in the bar)
            y_pos = bottom_y + (bar_height - text_surface.get_height()) // 2

            # Draw the text using integer position from float calculation
            current_x_int = int(self.current_x_float)
            self.screen.blit(text_surface, (current_x_int, y_pos))

            # Scroll the text with sub-pixel precision
            # Adaptive speed: longer text scrolls slightly slower for readability
            adaptive_speed = self.scroll_speed
            if len(self.current_news) > 80:  # Long headlines
                adaptive_speed = self.scroll_speed * 0.8
            elif len(self.current_news) > 120:  # Very long headlines
                adaptive_speed = self.scroll_speed * 0.7
                
            self.current_x_float -= adaptive_speed

            # If text has scrolled completely off screen, reset
            if self.current_x_float < -text_width:
                self.current_news = None  # Ready for next news item

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

        # Clean up pygame
        pygame.quit()
