import pygame
import numpy as np
import time
import random
import math

from dataclasses import dataclass, field

width = int(1920 / 4)
#width = 500
height = int(1280 / 4)
#height = 300

dimensions = [width, height]

fps = 60

@dataclass
class Point:
    x: float
    y: float

    def toPixel(self) -> np.ndarray:
        return np.array([self.x * height, height - self.y * height])

@dataclass
class Triangle:
    points: list[Point]
    originalPoints: list[Point] = field(default_factory = list)

    def __post_init__(self):
        self.originalPoints = [Point(point.x, point.y) for point in self.points]
    
    def centerPoint(self) -> Point:
        centerX = sum(point.x for point in self.points) / len(self.points)
        centerY = sum(point.y for point in self.points) / len(self.points)

        return Point(centerX, centerY)

    def originalCenterPoint(self) -> Point:
        centerX = sum(point.x for point in self.originalPoints) / len(self.originalPoints)
        centerY = sum(point.y for point in self.originalPoints) / len(self.originalPoints)

        return Point(centerX, centerY)

    def translate(self, x, y):
        for point in self.points:
            point.x += x
            point.y += y
    
    def translateFromOriginal(self, x, y):
        for i, point in enumerate(self.points):
            point.x = self.originalPoints[i].x + x
            point.y = self.originalPoints[i].y + y
        
    def scale(self, factor):
        for point in self.points:
            point.x *= factor
            point.y *= factor
    
    def scaleFromOriginal(self, factor):
        for i, point in enumerate(self.points):
            point.x = self.originalPoints[i].x * factor
            point.y = self.originalPoints[i].y * factor

    def rotate(self, angle):
        cosAngle = math.cos(angle)
        sinAngle = math.sin(angle)

        center = self.originalCenterPoint()

        for point in self.points:
            newX = point.x * cosAngle - point.y * sinAngle + center.x * (1 - cosAngle) + center.y * sinAngle
            newY = point.x * sinAngle + point.y * cosAngle + center.y * (1 - cosAngle) - center.x * sinAngle

            point.x = newX
            point.y = newY
        
    def rotateFromOriginal(self, angle):
        cosAngle = math.cos(angle)
        sinAngle = math.sin(angle)

        center = self.originalCenterPoint()

        for i, point in enumerate(self.points):
            originalPoint = self.originalPoints[i]

            newX = originalPoint.x * cosAngle - originalPoint.y * sinAngle + center.x * (1 - cosAngle) + center.y * sinAngle
            newY = originalPoint.x * sinAngle + originalPoint.y * cosAngle + center.y * (1 - cosAngle) - center.x * sinAngle

            point.x = newX
            point.y = newY

    def getPoints(self) -> list[np.ndarray]:
        return [point.toPixel() for point in self.points]

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

def computeTriangleMask(triangle: Triangle, gridX: int, gridY: int):
    edges = []

    trianglePoints = triangle.getPoints()

    for i in range(3):
        pointA = trianglePoints[i]
        pointB = trianglePoints[(i + 1) % 3]

        edge = (pointB[0] - pointA[0]) * (gridY - pointA[1]) - (pointB[1] - pointA[1]) * (gridX - pointA[0])

        edges.append(edge)

    return (
        ((edges[0] >= 0) & (edges[1] >= 0) & (edges[2] >= 0)) |
        ((edges[0] <= 0) & (edges[1] <= 0) & (edges[2] <= 0))

    )

def isInTriangle(triangle: Triangle, testPoint: np.ndarray) -> bool:
    trianglePoints = triangle.getPoints()
    edges = []

    for i in range(3):
        pointA = trianglePoints[i]
        pointB = trianglePoints[(i + 1) % 3]

        edges.append(edgeFunction(pointA, pointB, testPoint))
    
    return all(edge >= 0 for edge in edges) or all(edge <= 0 for edge in edges)

def main():
    print("Hello, Game Engine!")

    pygame.init()
    pygame.display.set_caption("2D Engine")
    screen = pygame.display.set_mode(dimensions)    
    clock = pygame.time.Clock()
    
    isRunning = True
    frameCount = 0
    #frameTimes = []

    pointSets = [
        [Point(0.1, 0.1), Point(0.5, 0.1), Point(0.1, 0.5)], 
        [Point(0.8, 0.7), Point(0.6, 0.5), Point(1.2, 0.4)],
        [Point(0.5, 0.6), Point(0.4, 0.5), Point(0.4, 0.8)]

    ]

    triangles = [Triangle(pointSet) for pointSet in pointSets]
    
    #xSide = np.arange(width, dtype = float)
    #ySide = np.arange(height, dtype = float)

    #xSide = np.arange(width, dtype = np.uint16)
    #ySide = np.arange(height, dtype = np.uint16)

    #gridX, gridY = np.meshgrid(xSide, ySide, indexing = "ij")

    gridX, gridY = np.meshgrid(np.arange(width), np.arange(height), indexing="ij")

    frameBuffer = np.zeros((width, height, 3), dtype = np.uint8)

    while isRunning:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                isRunning = False

        #startTime = time.perf_counter()

        frameCount += 1

        #frameBuffer[:, :] = (255, 0, 255)
        frameBuffer[:] = 0
        frameBuffer[:, :, 0] = (255 * (width  - gridX) / width).astype(np.uint8)
        frameBuffer[:, :, 2] = (255 * (height - gridY) / height).astype(np.uint8)

        for triangle in triangles:
            #triangle.translateFromOriginal(0.1 + math.sin(frameCount * 0.1) * 0.1 , 0.1 + math.cos(frameCount * 0.1) * 0.1)
            #triangle.rotateFromOriginal(frameCount * 0.01)
            triangle.rotate(0.01)
            mask = computeTriangleMask(triangle, gridX, gridY)

            frameBuffer[mask] = (200, 200, 200)

        pygame.surfarray.blit_array(screen, frameBuffer)

        pygame.display.set_caption(f"""{clock.get_fps():.3f}/{fps} fps""")

        pygame.display.flip()

        #stopTime = time.perf_counter()
        #timeDelta = stopTime - startTime

        #frameTimes.append(timeDelta)
        #averageTime = sum(frameTimes) / len(frameTimes)

        #print(f"""Render time for frame {len(frameTimes)}: {(timeDelta * 1000):.3f}ms""")
        #print(f"""Average frame time: {(averageTime * 1000):.3f}ms | Average FPS: {(1 / averageTime):.3f}""")

        clock.tick(fps)
        #time.sleep(5)

        #isRunning = False
    
    pygame.quit()

if __name__ == "__main__":
    main()