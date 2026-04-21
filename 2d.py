import pygame
import numpy as np
import time
import random

from dataclasses import dataclass

width = int(1920 / 5)
#width = 500
height = int(1080 / 5)
#height = 300

dimensions = [width, height]

fps = 60

def constructVector(pointA: np.ndarray, pointB: np.ndarray) -> np.ndarray:
    if len(pointA) != len(pointB): return np.array([0, 0], dtype = float)

    coordinates = []

    for i in range(len(pointA)):
        coordinates.append(pointB[i] - pointA[i])
    
    return np.array(coordinates, dtype = float)

def edgeFunction(pointA: np.ndarray, pointB: np.ndarray, testPoint: np.ndarray) -> float:
    lineAB = pointB - pointA
    lineAP = testPoint - pointA

    return lineAB[0] * lineAP[1] - lineAB[1] * lineAP[0]

def computeTriangleMask(triangle: list[np.ndarray], gridX: int, gridY: int):
    edges = []

    for i in range(3):
        pointA = triangle[i]
        pointB = triangle[(i + 1) % 3]

        edge = (pointB[0] - pointA[0]) * (gridY - pointA[1]) - (pointB[1] - pointA[1]) * (gridX - pointA[0])

        edges.append(edge)

    return (
        ((edges[0] >= 0) & (edges[1] >= 0) & (edges[2] >= 0)) |
        ((edges[0] <= 0) & (edges[1] <= 0) & (edges[2] <= 0))

    )

def isInTriangle(triangle: list[np.ndarray], testPoint: np.ndarray) -> bool:
    edges = []

    for i in range(3):
        pointA = triangle[i]
        pointB = triangle[(i + 1) % 3]

        edges.append(edgeFunction(pointA, pointB, testPoint))
    
    return all(edge >= 0 for edge in edges) or all(edge <= 0 for edge in edges)

@dataclass
class Point:
    x: float
    y: float

    def toPixel(self) -> np.ndarray:
        return np.array([self.x * width, self.y * height]) 

def main():
    print("Hello, Game Engine!")

    pygame.init()
    pygame.display.set_caption("2D Engine")
    screen = pygame.display.set_mode(dimensions)    
    clock = pygame.time.Clock()
    
    isRunning = True
    frameTimes = []

    pointSets = [
        [Point(0.1, 0.1), Point(0.3, 0.5), Point(0.4, 0.3)], 
        [Point(0.8, 0.7), Point(0.6, 0.5), Point(0.9, 0.4)],
        [Point(0.5, 0.6), Point(0.4, 0.5), Point(0.4, 0.8)]

    ]

    triangles = []
    for pointSet in pointSets:
        triangles.append(([point.toPixel() for point in pointSet]))
    
    xSide = np.arange(width, dtype = float)
    ySide = np.arange(height, dtype = float)

    gridX, gridY = np.meshgrid(xSide, ySide, indexing = "ij")

    frameBuffer = np.zeros((width, height, 3), dtype = np.uint8)

    while isRunning:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                isRunning = False

        startTime = time.perf_counter()

        #frameBuffer[:, :] = (255, 0, 255)
        frameBuffer[:, :, 0] = (255 * (width  - gridX) / width).astype(np.uint8)
        frameBuffer[:, :, 2] = (255 * (height - gridY) / height).astype(np.uint8)

        for triangle in triangles:
            mask = computeTriangleMask(triangle, gridX, gridY)

            frameBuffer[mask] = (200, 200, 200)

        pygame.surfarray.blit_array(screen, frameBuffer)

        pygame.display.set_caption(f"""{clock.get_fps():.3f}/{fps} fps""")

        pygame.display.flip()

        stopTime = time.perf_counter()
        timeDelta = stopTime - startTime

        frameTimes.append(timeDelta)
        averageTime = sum(frameTimes) / len(frameTimes)

        print(f"""Render time for frame {len(frameTimes)}: {(timeDelta * 1000):.3f}ms""")
        print(f"""Average frame time: {(averageTime * 1000):.3f}ms | Average FPS: {(1 / averageTime):.3f}""")

        clock.tick(fps)
        #time.sleep(5)

        #isRunning = False
    
    pygame.quit()

if __name__ == "__main__":
    main()