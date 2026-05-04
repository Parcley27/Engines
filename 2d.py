import pygame
import numpy as np
import time
import random
import math

from dataclasses import dataclass, field

width = int(1920 / 4)
height = int(1280 / 4)

cameraDepth = 3

fieldOfView = math.radians(70) # horizontal
focalLength = (width / 2) / math.tan(fieldOfView / 2)

screenDimensions = [width, height]

fps = 60

@dataclass
class Point:
    x: float
    y: float
    z: float

    def toPixel(self) -> np.ndarray:
        #scale = (-self.z - 5) / -5
        depth = self.z + cameraDepth
        pixelX = (self.x / depth) * focalLength + width / 2
        pixelY = (-self.y / depth) * focalLength + height / 2

        return np.array([pixelX, pixelY])

@dataclass
class Triangle:
    points: list[Point]
    originalPoints: list[Point] = field(default_factory = list)

    colour: tuple[int, int, int] = (0, 255, 255)

    def __post_init__(self):
        self.originalPoints = [Point(point.x, point.y, point.z) for point in self.points]
    
    def centerPoint(self) -> Point:
        centerX = sum(point.x for point in self.points) / len(self.points)
        centerY = sum(point.y for point in self.points) / len(self.points)
        centerZ = sum(point.z for point in self.points) / len(self.points)

        return Point(centerX, centerY, centerZ)

    def originalCenterPoint(self) -> Point:
        centerX = sum(point.x for point in self.originalPoints) / len(self.originalPoints)
        centerY = sum(point.y for point in self.originalPoints) / len(self.originalPoints)
        centerZ = sum(point.z for point in self.originalPoints) / len(self.originalPoints)

        return Point(centerX, centerY, centerZ)

    def translate(self, x, y, z):
        for point in self.points:
            point.x += x
            point.y += y
            point.z += z
    
    def translateFromOriginal(self, x, y, z):
        for i, point in enumerate(self.points):
            point.x = self.originalPoints[i].x + x
            point.y = self.originalPoints[i].y + y
            point.z = self.originalPoints[i].z + z
        
    def scale(self, factor):
        center = self.centerPoint()

        for point in self.points:
            point.x = center.x + (point.x - center.x) * factor
            point.y = center.y + (point.y - center.y) * factor
            point.z = center.z + (point.z - center.z) * factor
    
    def scaleFromOriginal(self, factor):
        center = self.originalCenterPoint()

        for i, point in enumerate(self.points):
            point.x = center.x + (self.originalPoints[i].x - center.x) * factor
            point.y = center.y + (self.originalPoints[i].y - center.y) * factor
            point.z = center.z + (self.originalPoints[i].z - center.z) * factor

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

    def asPixels(self) -> list[np.ndarray]:
        return [point.toPixel() for point in self.points]

def fan(points: list[np.ndarray]) -> list[Triangle]:
    triangles = []

    for i in range(1, len(points) - 1):
        trianglePoints = [Point(points[0].x, points[0].y), Point(points[i].x, points[i].y), Point(points[i+1].x, points[i+1].y)]
        triangles.append(Triangle(trianglePoints))
    
    return triangles

#def constructVector(pointA: np.ndarray, pointB: np.ndarray) -> np.ndarray:
    if len(pointA) != len(pointB): return np.array([0, 0], dtype = float)

    coordinates = []

    for i in range(len(pointA)):
        coordinates.append(pointB[i] - pointA[i])
    
    return np.array(coordinates, dtype = float)

def edgeFunction(pointA: np.ndarray, pointB: np.ndarray, testPoint: np.ndarray) -> float:
    lineAB = pointB - pointA
    lineAP = testPoint - pointA

    return lineAB[0] * lineAP[1] - lineAB[1] * lineAP[0]

def computeTriangleMask(triangle: Triangle, gridX: int, gridY: int) -> np.ndarray:
    edges = []

    trianglePoints = triangle.asPixels()

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
    trianglePoints = triangle.asPixels()
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

    screen = pygame.display.set_mode(screenDimensions)
    clock = pygame.time.Clock()
    
    isRunning = True
    frameCount = 0

    pointSets = [
        [Point(0.0, 0.0, 0.0),  Point(1.0, 0.0, 0.0),  Point(0.0, 1.0, 0.0)], 
        [Point(1.0, 1.0, 1.0), Point(0.0, 1.0, 1.0), Point(1.0, 0.0, 1.0)], 

    ]

    for pointSet in pointSets:
        for point in pointSet:
            point.x -= 0.5
            point.y -= 0.5

    """

    fanPoints = [
        Point(0.50, 0.25),
        Point(0.45, 0.26),
        Point(0.40, 0.27),
        Point(0.35, 0.30),
        Point(0.30, 0.35),
        Point(0.25, 0.50),
        Point(0.30, 0.65),
        Point(0.35, 0.70),
        Point(0.40, 0.73),
        Point(0.45, 0.74),
        Point(0.50, 0.75),
        Point(0.55, 0.74),
        Point(0.60, 0.73),
        Point(0.65, 0.70),
        Point(0.70, 0.65),
        Point(0.75, 0.50),
        Point(0.70, 0.35),
        Point(0.65, 0.30),
        Point(0.60, 0.27),
        Point(0.55, 0.26),
        #Point(0.7, 0.6)
        
    ]

    """

    triangles = [Triangle(pointSet) for pointSet in pointSets]
    #triangles = fan(fanPoints)

    for triangle in triangles:
        triangle.colour = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

    gridX, gridY = np.meshgrid(np.arange(width), np.arange(height), indexing="ij")

    frameBuffer = np.zeros((width, height, 3), dtype = np.uint8)

    while isRunning:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                isRunning = False

        frameCount += 1

        frameBuffer[:] = 0
        frameBuffer[:, :, 0] = (255 * (width  - gridX) / width).astype(np.uint8)
        frameBuffer[:, :, 2] = (255 * (height - gridY) / height).astype(np.uint8)

        for triangle in triangles:
            #triangle.translateFromOriginal(math.sin(frameCount * 0.05) * 0.2 , math.cos(frameCount * 0.05) * 0.2, 0)
            triangle.translate(math.sin(frameCount * 0.1) * 0.01 , math.cos(frameCount * 0.1) * 0.01, 0)
            #triangle.rotate(0.01)
            current = 1 + math.sin(frameCount * 0.05) * 0.4
            previous = 1 + math.sin((frameCount - 1) * 0.05) * 0.4
            triangle.scale(current / previous)
        
        sortedTriangles = sorted(triangles, key = lambda t: t.centerPoint().z, reverse = True)

        for triangle in sortedTriangles:
            mask = computeTriangleMask(triangle, gridX, gridY)
            frameBuffer[mask] = triangle.colour


        pygame.surfarray.blit_array(screen, frameBuffer)

        pygame.display.set_caption(f"""{clock.get_fps():.3f}/{fps} fps""")

        pygame.display.flip()

        clock.tick(fps)
    
    pygame.quit()

if __name__ == "__main__":
    main()