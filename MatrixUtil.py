import numpy as np

def RotateX(matrix, angle):
    """Rotate matrix 'angle' degrees around X axis"""
    rotationMatrix = np.identity(4)
    theta = np.radians(angle)
    cos, sin = np.cos(theta), np.sin(theta)
    rotationMatrix[1][1] = cos
    rotationMatrix[2][2] = cos
    rotationMatrix[1][2] = -sin
    rotationMatrix[2][1] = sin
    return np.dot(matrix, rotationMatrix)

def RotateY(matrix, angle):
    """Rotate matrix 'angle' degrees around Y axis"""
    rotationMatrix = np.identity(4)
    theta = np.radians(angle)
    cos, sin = np.cos(theta), np.sin(theta)
    rotationMatrix[0][0] = cos
    rotationMatrix[2][2] = cos
    rotationMatrix[0][2] = sin
    rotationMatrix[2][0] = -sin
    return np.dot(matrix, rotationMatrix)

def RotateZ(matrix, angle):
    """Rotate matrix 'angle' degrees around Z axis"""
    rotationMatrix = np.identity(4)
    theta = np.radians(angle)
    cos, sin = np.cos(theta), np.sin(theta)
    rotationMatrix[0][0] = cos
    rotationMatrix[1][1] = cos
    rotationMatrix[0][1] = -sin
    rotationMatrix[1][0] = sin
    return np.dot(matrix, rotationMatrix)

def Translate(matrix, p):
    """Translate matrix"""
    translationMatrix = np.identity(4)
    translationMatrix[0][3] = p[0]
    translationMatrix[1][3] = p[1]
    translationMatrix[2][3] = p[2]
    return np.dot(matrix, translationMatrix)

def GetMatrixOrigin(matrix):
    """Return the matrix origin"""
    return [matrix[0][3], matrix[1][3], matrix[2][3]]

def TransformPoint(pointInA, matrixAToB):
    """Transform point coordinates in space A to point coordinates in space B"""
    return np.dot(matrixAToB, tuple(pointInA) + (1,))[:3]

def TransformVector(vectorInA, matrixAToB):
    """Transform vector coordinates in space A to vector coordinates in space B"""
    return np.dot(matrixAToB, tuple(vectorInA) + (0,))[:3]

def BuildTransformMatrix(O, X, Y):
    """Build the transform matrix from the reference space defined
        by 3 points.
        O : origin
        X : point in X dir
        Y : point around Y dir (will be orthogonalized to X, using Z)
    """
    # x = normalized(OX)
    # z = normal to plane (cross(x, OY))
    # y = cross(z, x)
    x = np.subtract(X, O)
    x = np.multiply(1.0/np.linalg.norm(x), x)
    y = np.subtract(Y, O)
    z = np.cross(x, y)
    z = np.multiply(1.0/np.linalg.norm(z), z)
    y = np.cross(z, x)

    transformMatrix = np.identity(4)
    transformMatrix[0][0] = x[0]
    transformMatrix[1][0] = x[1]
    transformMatrix[2][0] = x[2]

    transformMatrix[0][1] = y[0]
    transformMatrix[1][1] = y[1]
    transformMatrix[2][1] = y[2]

    transformMatrix[0][2] = z[0]
    transformMatrix[1][2] = z[1]
    transformMatrix[2][2] = z[2]

    transformMatrix[0][3] = O[0]
    transformMatrix[1][3] = O[1]
    transformMatrix[2][3] = O[2]

    return transformMatrix


if __name__ == '__main__':
    # Tests
    m = np.identity(4)
    np.set_printoptions(suppress=True, precision=2)

    angle = 90
    m1 = RotateX(m, angle)
    print("90 RotateX")
    print(m1)
    m1 = RotateY(m, angle)
    print("90 RotateY")
    print(m1)
    m1 = RotateZ(m, angle)
    print("90 RotateZ")
    print(m1)
    m1 = Translate(m1, (2, 3, 4))
    print("Translate 2 3 4")
    print(m1)
    p = GetMatrixOrigin(m1)
    print("origin")
    print(p)
    print(m1[:3,[3]])
    print("TransformPoint (1, 1, 0) with m1=")
    print(m1)
    p = TransformPoint((1, 1, 0), m1)
    print(p)
    print("TransformVector (1, 1, 0) with m1=")
    print(m1)
    v = TransformVector((1, 1, 0), m1)
    print(v)

    o = [0, 0, 0]
    x = [0, 1, 0]
    y = [0, 0, 1]
    m = BuildTransformMatrix(o, x, y)
    print("BuildTransformMatrix ", o, ", ", x, ", ", y)
    print(m)
