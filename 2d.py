import pygame
import numpy as np
import time

width = int(1920 / 2)
#width = 500
height = int(1080 / 2)
#height = 300

dimensions = [width, height]

fps = 60

def main():
    print("Hello, Game Engine!")

    pygame.init()
    pygame.display.set_caption("2D Engine")

    screen = pygame.display.set_mode(dimensions)

    frameBuffer = np.zeros((width, height, 3), dtype = np.uint8)
    
    clock = pygame.time.Clock()
    
    isRunning = True

    frameCount = 0

    while isRunning:
        frameCount += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                isRunning = False

        startTime = time.perf_counter()

        #frameBuffer[:, :] = (255, 0, 255)
        for x in range(width):
            for y in range(height):
                frameBuffer[x, y] = (255 * (width - x) / width, 0, 255 * (height - y) / height)

        pygame.surfarray.blit_array(screen, frameBuffer)

        pygame.display.set_caption(f"""{clock.get_fps():.3f}/{fps} fps""")

        pygame.display.flip()

        stopTime = time.perf_counter()
        timeDelta = stopTime - startTime

        print(f"""Render time for frame {frameCount}: {timeDelta}s""")

        clock.tick(fps)
    
    pygame.quit()

if __name__ == "__main__":
    main()