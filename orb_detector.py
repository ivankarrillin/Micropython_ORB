class ORBDetector:
    try:
        import utime as time
    except ImportError:
        import time

    try:
        _seed = time.ticks_ms()
    except AttributeError:
        _seed = int(time.time() * 1000)

    PI = 3.141592653589793
    UMBRAL = 50

    def __init__(self):
        self.pattern = [(self.randint(-15, 15), self.randint(-15, 15),
                         self.randint(-15, 15), self.randint(-15, 15)) for _ in range(256)]

    @classmethod
    def random(cls):
        cls._seed = (cls._seed * 1103515245 + 12345) % (2**31)
        return cls._seed

    @classmethod
    def randint(cls, a, b):
        return a + cls.random() % (b - a + 1)

    @staticmethod
    def atan_series(z, terms=10):
        if abs(z) > 1:
            return (ORBDetector.PI / 2 if z > 0 else -ORBDetector.PI / 2) - ORBDetector.atan_series(1/z, terms)
        result = 0
        sign = 1
        for n in range(terms):
            term = (z ** (2 * n + 1)) / (2 * n + 1)
            result += sign * term
            sign *= -1
        return result

    @staticmethod
    def atan2_taylor(y, x, terms=10):
        if x > 0:
            return ORBDetector.atan_series(y / x, terms)
        elif x < 0 and y >= 0:
            return ORBDetector.atan_series(y / x, terms) + ORBDetector.PI
        elif x < 0 and y < 0:
            return ORBDetector.atan_series(y / x, terms) - ORBDetector.PI
        elif x == 0 and y > 0:
            return ORBDetector.PI / 2
        elif x == 0 and y < 0:
            return -ORBDetector.PI / 2
        else:
            return 0

    @staticmethod
    def sin(x):
        x = x % (2 * ORBDetector.PI)
        if x > ORBDetector.PI:
            x -= 2 * ORBDetector.PI
        elif x < -ORBDetector.PI:
            x += 2 * ORBDetector.PI
        return x - (x**3)/6 + (x**5)/120 - (x**7)/5040

    @staticmethod
    def cos(x):
        x = x % (2 * ORBDetector.PI)
        if x > ORBDetector.PI:
            x -= 2 * ORBDetector.PI
        elif x < -ORBDetector.PI:
            x += 2 * ORBDetector.PI
        x2 = x * x
        return 1 - x2/2 + x2*x2/24 - x2*x2*x2/720

    @staticmethod
    def radians(grado):
        return grado * ORBDetector.PI / 180

    @staticmethod
    def leer_matriz(archivo):
        with open(archivo, 'r') as f:
            contenido = f.read()
            matriz = eval(contenido)
        return matriz

    def detect_fast_corners(self, image, threshold=None):
        if threshold is None:
            threshold = self.UMBRAL

        keypoints = []
        circle_offsets = [(0,-3), (1,-3), (2,-2), (3,-1), (3,0), (3,1), (2,2), (1,3),
                          (0,3), (-1,3), (-2,2), (-3,1), (-3,0), (-3,-1), (-2,-2), (-1,-3)]
        for y in range(3, len(image)-3):
            for x in range(3, len(image[0])-3):
                pixel = image[y][x]
                brighter = darker = 0
                for i in [0, 4, 8, 12]:
                    dy, dx = circle_offsets[i]
                    if image[y+dy][x+dx] > pixel + threshold:
                        brighter += 1
                    elif image[y+dy][x+dx] < pixel - threshold:
                        darker += 1
                if brighter >= 3 or darker >= 3:
                    brighter = darker = 0
                    for dy, dx in circle_offsets:
                        if image[y+dy][x+dx] > pixel + threshold:
                            brighter += 1
                        elif image[y+dy][x+dx] < pixel - threshold:
                            darker += 1
                    if brighter >= 12 or darker >= 12:
                        keypoints.append({'pt': (y, x), 'angle': 0})
        return keypoints

    def compute_orientation(self, image, keypoint):
        y, x = keypoint['pt']
        m01 = m10 = 0
        for i in range(-15, 16):
            for j in range(-15, 16):
                yi = y + i
                xj = x + j
                if 0 <= yi < len(image) and 0 <= xj < len(image[0]):
                    intensity = image[yi][xj]
                    m01 += i * intensity
                    m10 += j * intensity
        angle = (self.atan2_taylor(m01, m10) * 180 / self.PI) % 360
        return angle

    def brief_descriptor(self, image, keypoint, pattern):
        y, x = keypoint['pt']
        angle_rad = self.radians(keypoint['angle'])
        descriptor = []
        for x1, y1, x2, y2 in pattern:
            x1_rot = x1 * self.cos(angle_rad) - y1 * self.sin(angle_rad)
            y1_rot = x1 * self.sin(angle_rad) + y1 * self.cos(angle_rad)
            x2_rot = x2 * self.cos(angle_rad) - y2 * self.sin(angle_rad)
            y2_rot = x2 * self.sin(angle_rad) + y2 * self.cos(angle_rad)
            val1 = image[int(y+y1_rot)][int(x+x1_rot)] if 0 <= int(y+y1_rot) < len(image) and 0 <= int(x+x1_rot) < len(image[0]) else 0
            val2 = image[int(y+y2_rot)][int(x+x2_rot)] if 0 <= int(y+y2_rot) < len(image) and 0 <= int(x+x2_rot) < len(image[0]) else 0
            descriptor.append(1 if val1 > val2 else 0)
        return descriptor

    def detectar_orb(self, archivo):
        matriz = self.leer_matriz(archivo)
        keypoints = self.detect_fast_corners(matriz)

        for kp in keypoints:
            kp['angle'] = self.compute_orientation(matriz, kp)
            kp['descriptor'] = self.brief_descriptor(matriz, kp, self.pattern)

        return keypoints
