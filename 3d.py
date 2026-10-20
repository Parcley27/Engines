from __future__ import annotations

import pygame
import numpy as np
import time
import random
import math

from dataclasses import dataclass, field

width = int(1920 / 4)
height = int(1280 / 4)

cameraDepth = 5

fieldOfView = math.radians(70) # horizontal
focalLength = (width / 2) / math.tan(fieldOfView / 2)

screenDimensions = [width, height]

fps = 60

testSpeed = 0.1

colours = ["darkred", "red", "darkorange", "orange", "gold", "yellow", "darkgreen", "green", "darkblue", "blue", "purple", "violet"]
colourIndex = 0

@dataclass
class Quaternion:
    # vector part
    x: float = 0
    y: float = 0
    z: float = 0

    # scalar part
    w: float = 1

    @staticmethod
    def fromAxisAngle(axis: np.ndarray, angle: float) -> Quaternion:
        length = np.linalg.norm(axis)

        if length == 0:
            return Quaternion(0, 0, 0, 1)

        axisX, axisY, axisZ = axis

        s = math.sin(angle / 2) / length

        return (Quaternion(axisX * s, axisY * s, axisZ * s, math.cos(angle / 2)))

    def normalize(self) -> Quaternion:
        length = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

        return Quaternion(self.x / length, self.y / length, self.z / length, self.w / length)

    def multiply(self, other: Quaternion) -> Quaternion:
        x1, y1, z1, w1 = self.x, self.y, self.z, self.w
        x2, y2, z2, w2 = other.x, other.y, other.z, other.w
        
        return Quaternion(
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2

        )

    def toMatrix(self) -> np.ndarray:
        x, y, z, w = self.x, self.y, self.z, self.w

        return np.array([
            [1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w)],
            [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w)],
            [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y)],

        ], dtype = np.float32)

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
    
    def centrePoint(self) -> Point:
        centreX = sum(point.x for point in self.points) / len(self.points)
        centreY = sum(point.y for point in self.points) / len(self.points)
        centreZ = sum(point.z for point in self.points) / len(self.points)

        return Point(centreX, centreY, centreZ)

    def originalcentrePoint(self) -> Point:
        centreX = sum(point.x for point in self.originalPoints) / len(self.originalPoints)
        centreY = sum(point.y for point in self.originalPoints) / len(self.originalPoints)
        centreZ = sum(point.z for point in self.originalPoints) / len(self.originalPoints)

        return Point(centreX, centreY, centreZ)

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
        centre = self.centrePoint()

        for point in self.points:
            point.x = centre.x + (point.x - centre.x) * factor
            point.y = centre.y + (point.y - centre.y) * factor
            point.z = centre.z + (point.z - centre.z) * factor
    
    def scaleFromOriginal(self, factor):
        centre = self.originalcentrePoint()

        for i, point in enumerate(self.points):
            point.x = centre.x + (self.originalPoints[i].x - centre.x) * factor
            point.y = centre.y + (self.originalPoints[i].y - centre.y) * factor
            point.z = centre.z + (self.originalPoints[i].z - centre.z) * factor

    def rotate(self, rotation: Quaternion):
        rotationMatrix = rotation.toMatrix()

        centre = self.centrePoint()
        centreVector = np.array([centre.x, centre.y, centre.z], dtype = np.float32)

        for point in self.points:
            pointVector = np.array([point.x, point.y, point.z], dtype = np.float32)

            offsetFromcentre = pointVector - centreVector
            rotatedOffset = rotationMatrix @ offsetFromcentre

            rotatedPosition = centreVector + rotatedOffset

            point.x = rotatedPosition[0]
            point.y = rotatedPosition[1]
            point.z = rotatedPosition[2]
        
    def rotateFromOriginal(self, rotation: Quaternion):
        rotationMatrix = rotation.toMatrix()

        originalcentre = self.originalcentrePoint()
        originalcentreVector = np.array([originalcentre.x, originalcentre.y, originalcentre.z], dtype = np.float32)

        for pointIndex in range(len(self.points)):
            point = self.points[pointIndex]
            originalPoint = self.originalPoints[pointIndex]

            originalPointVector = np.array([originalPoint.x, originalPoint.y, originalPoint.z], dtype = np.float32)

            offsetFromcentre = originalPointVector - originalcentreVector
            rotatedOffset = rotationMatrix @ offsetFromcentre
            rotatedPosition = rotatedOffset + originalcentreVector

            point.x = float(rotatedPosition[0])
            point.y = float(rotatedPosition[1])
            point.z = float(rotatedPosition[2])

    def asPixels(self) -> list[np.ndarray]:
        return [point.toPixel() for point in self.points]

def safeInt(value, default = 0) -> int:
    try:
        return int(value)
    
    except (ValueError, TypeError):
        return default

def safeFloat(value, default = 0.0) -> float:
    try:
        return float(value)
    
    except (ValueError, TypeError):
        return default

def loadModel(filePath: str) -> list[Triangle]:
    print("Loading model: " + filePath)

    points = []

    triangles = []
    
    with open(filePath, "r") as file:
        for line in file:
            if line.startswith("v "): # vertices
                lineData = line.split()
                
                x = float(lineData[1])
                y = float(lineData[2])
                z = float(lineData[3])

                points.append(Point(x, y, z))
            
            elif line.startswith("f "):
                faceData = line.split()
                facePointData = []

                faceVertexData = []
                for segment in faceData:
                    segmentData = segment.split("/")

                    for i in range(len(segmentData) - 2):
                        faceVertexData.append(safeInt(segmentData[i]))
                
                for vertex in faceVertexData:
                    facePointData.append(points[vertex - 1])

                triangles.extend(fan(facePointData))

    print(f"Loaded {len(triangles)} triangles")
    
    return triangles

def fan(points: list[Point]) -> list[Triangle]:
    triangles = []

    for i in range(1, len(points) - 1):
        trianglePoints = [Point(points[0].x, points[0].y, points[0].z), Point(points[i].x, points[i].y, points[i].z), Point(points[i + 1].x, points[i + 1].y, points[i + 1].z)]
        triangles.append(Triangle(trianglePoints))
    
    return triangles

#def constructVector(pointA: np.ndarray, pointB: np.ndarray) -> np.ndarray:
    if len(pointA) != len(pointB): return np.array([0, 0], dtype = float)

    coordinates = []

    for i in range(len(pointA)):
        coordinates.append(pointB[i] - pointA[i])
    
    return np.array(coordinates, dtype = float)

# cross product sign: positive if testPoint is to the right of line AB, negative if to the left (inside)
# magnitude: 2 * area of triangle pointA pointB testPoint
def edgeFunction(pointA: np.ndarray, pointB: np.ndarray, testPoint: np.ndarray) -> float:
    lineAB = pointB - pointA
    lineAP = testPoint - pointA

    return lineAB[0] * lineAP[1] - lineAB[1] * lineAP[0]

def rasterizeTriangle(triangle: Triangle, gridX: np.ndarray, gridY: np.ndarray) -> tuple[tuple[slice, slice], np.ndarray, np.ndarray] | None:
    if any(point.z + cameraDepth <= 0 for point in triangle.points):
        return None

    edges = []

    trianglePoints = triangle.asPixels()

    pointXs = [trianglePoint[0] for trianglePoint in trianglePoints]
    pointYs = [trianglePoint[1] for trianglePoint in trianglePoints]

    minX = int(max(min(pointXs), 0))
    maxX = int(min(max(pointXs), width - 1))
    minY = int(max(min(pointYs), 0))
    maxY = int(min(max(pointYs), height - 1))

    if minX > maxX or minY > maxY:
        return None

    region = (slice(minX, maxX + 1), slice(minY, maxY + 1))

    regionX = gridX[region]
    regionY = gridY[region]

    for i in range(3):
        pointA = trianglePoints[i]
        pointB = trianglePoints[(i + 1) % 3]

        edge = (pointB[0] - pointA[0]) * (regionY - pointA[1]) - (pointB[1] - pointA[1]) * (regionX - pointA[0])

        edges.append(edge)

    area = edgeFunction(trianglePoints[0], trianglePoints[1], trianglePoints[2])

    # head one ie no visable width
    if area == 0:
        return None

    vertex0Proximity = edges[1] / area
    vertex1Proximity = edges[2] / area
    vertex2Proximity = edges[0] / area

    mask = (vertex0Proximity >= 0) & (vertex1Proximity >= 0) & (vertex2Proximity >= 0)

    inverseDepth = (
        vertex0Proximity / (triangle.points[0].z + cameraDepth) +
        vertex1Proximity / (triangle.points[1].z + cameraDepth) +
        vertex2Proximity / (triangle.points[2].z + cameraDepth)

    )

    depth = np.full(mask.shape, np.inf, dtype = np.float32)
    np.divide(1, inverseDepth, out = depth, where = mask)

    return region, mask, depth

def computeTriangleMask(triangle: Triangle, gridX: np.ndarray, gridY: np.ndarray) -> np.ndarray:
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
    global colourIndex
    print("Hello, 3D Game Engine!")

    pygame.init()
    pygame.display.set_caption("3D Engine")

    screen = pygame.display.set_mode(screenDimensions)
    clock = pygame.time.Clock()
    
    isRunning = True
    frameCount = 0

    triangles = loadModel("cube.obj")

    for triangle in triangles:
        colour = tuple(pygame.Color(colours[colourIndex]))
        colourIndex = (colourIndex + 1) % len(colours)

        triangle.colour = (colour[0], colour[1], colour[2])

        triangle.translate(-4, 0, 0)

    gridX, gridY = np.meshgrid(np.arange(width, dtype = np.float32), np.arange(height, dtype = np.float32), indexing="ij")
    
    frameBuffer = np.zeros((width, height, 3), dtype = np.uint8)
    depthBuffer = np.zeros((width, height), dtype = np.float32)

    while isRunning:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                isRunning = False

        frameCount += 1

        translateConstant = math.sin(frameCount * 0.1 * testSpeed) * 0.4 * testSpeed

        frameBuffer[:] = 0
        depthBuffer[:] = np.inf

        # background
        frameBuffer[:, :, 0] = (255 * (width  - gridX) / width).astype(np.uint8)
        frameBuffer[:, :, 2] = (255 * (height - gridY) / height).astype(np.uint8)

        # move stuff
        for triangle in triangles: 
            triangle.translate(translateConstant, 0, 0)
            triangle.rotate(Quaternion.fromAxisAngle(np.array([1, 1, 1]), 0.006))

        # render stuff
        for triangle in triangles:
            coverage = rasterizeTriangle(triangle, gridX, gridY)

            if coverage is not None:
                region, mask, depth = coverage

                frameView = frameBuffer[region]
                depthView = depthBuffer[region]

                visiblePixels = mask & (depth < depthView)

                frameView[visiblePixels] = triangle.colour
                depthView[visiblePixels] = depth[visiblePixels]

            #triangle.translateFromOriginal(math.sin(frameCount * 0.05) * 0.2 , math.cos(frameCount * 0.05) * 0.2, 0)
            #triangle.translate(math.sin(frameCount * 0.1) * 0.01 , math.cos(frameCount * 0.1) * 0.01, 0)
            #triangle.rotate(0.01)
            #current = 1 + math.sin(frameCount * 0.05) * 0.4
            #previous = 1 + math.sin((frameCount - 1) * 0.05) * 0.4
            #triangle.scaleFromOriginal(0.8)
            #triangle.scale(current / previous)

        pygame.surfarray.blit_array(screen, frameBuffer)

        pygame.display.set_caption(f"""{clock.get_fps():.3f}/{fps} fps""")

        pygame.display.flip()

        clock.tick(fps)
    
    pygame.quit()

if __name__ == "__main__":
    main()