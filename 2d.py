import pygame
import numpy as np

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

    while isRunning:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                isRunning = False
            
        frameBuffer[:, :] = (255, 0, 255)

        pygame.surfarray.blit_array(screen, frameBuffer)

        pygame.display.set_caption(f"""{clock.get_fps():.3f}/{fps} fps""")

        pygame.display.flip()

        clock.tick(fps)
    
    pygame.quit()

if __name__ == "__main__":
    main()