import time
import numpy as np
import syphon
from syphon.utils.numpy import copy_image_to_mtl_texture
from syphon.utils.raw import create_mtl_texture


def run_syphon_test():
    # Create a server with a meaningful name
    server = syphon.server.SyphonMetalServer(name="Syphon Test")
    print(f"Created Syphon server: {server.name}")

    # Create texture with the server's device
    width, height = 512, 512
    texture = create_mtl_texture(server.device, width, height)
    print(f"Created texture: {width}x{height}")

    # Create a simple animation with a moving rectangle
    texture_data = np.zeros((height, width, 4), dtype=np.uint8)
    texture_data[:, :, 3] = 255  # Set alpha channel to fully opaque

    position = 0
    try:
        print("Starting publishing loop (press Ctrl+C to stop)...")
        while True:
            # Clear the texture data
            texture_data[:, :, :3] = 0

            # Draw a moving red rectangle
            rect_size = 100
            rect_pos = position % (width - rect_size)
            texture_data[height//2-rect_size//2:height//2+rect_size//2,
                         rect_pos:rect_pos+rect_size, 0] = 255  # Red

            # Copy texture data to texture and publish frame
            copy_image_to_mtl_texture(texture_data, texture)
            server.publish_frame_texture(texture)

            position += 5
            time.sleep(1/30)  # 30 FPS
    except KeyboardInterrupt:
        print("\nStopping Syphon server...")
    finally:
        server.stop()
        print("Syphon server stopped")


if __name__ == "__main__":
    run_syphon_test()
