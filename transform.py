"""
几何变换模块
实现平移、旋转、比例变换
"""
import math
import numpy as np


class Transform:
    """几何变换类"""
    
    @staticmethod
    def translate(points, tx, ty):
        """平移变换
        points: 点列表 [(x1, y1), (x2, y2), ...]
        返回变换后的点列表
        """
        result = []
        for x, y in points:
            result.append((x + tx, y + ty))
        return result
    
    @staticmethod
    def rotate(points, angle, center_x=0, center_y=0):
        """旋转变换
        points: 点列表
        angle: 旋转角度（弧度）
        center_x, center_y: 旋转中心
        """
        result = []
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        for x, y in points:
            # 平移到原点
            x -= center_x
            y -= center_y
            # 旋转
            new_x = x * cos_a - y * sin_a
            new_y = x * sin_a + y * cos_a
            # 平移回去
            new_x += center_x
            new_y += center_y
            result.append((new_x, new_y))
        return result
    
    @staticmethod
    def scale(points, sx, sy, center_x=0, center_y=0):
        """比例变换
        points: 点列表
        sx, sy: x和y方向的缩放因子
        center_x, center_y: 缩放中心
        """
        result = []
        for x, y in points:
            # 平移到原点
            x -= center_x
            y -= center_y
            # 缩放
            x *= sx
            y *= sy
            # 平移回去
            x += center_x
            y += center_y
            result.append((x, y))
        return result
    
    @staticmethod
    def matrix_transform(points, matrix):
        """使用变换矩阵进行变换
        matrix: 3x3变换矩阵
        """
        result = []
        for x, y in points:
            # 齐次坐标
            point = np.array([x, y, 1])
            transformed = matrix @ point
            result.append((transformed[0], transformed[1]))
        return result
    
    @staticmethod
    def get_translation_matrix(tx, ty):
        """获取平移矩阵"""
        return np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ])
    
    @staticmethod
    def get_rotation_matrix(angle, center_x=0, center_y=0):
        """获取旋转矩阵"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # 组合变换：平移(-cx, -cy) -> 旋转 -> 平移(cx, cy)
        T1 = Transform.get_translation_matrix(-center_x, -center_y)
        R = np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])
        T2 = Transform.get_translation_matrix(center_x, center_y)
        return T2 @ R @ T1
    
    @staticmethod
    def get_scale_matrix(sx, sy, center_x=0, center_y=0):
        """获取缩放矩阵"""
        T1 = Transform.get_translation_matrix(-center_x, -center_y)
        S = np.array([
            [sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]
        ])
        T2 = Transform.get_translation_matrix(center_x, center_y)
        return T2 @ S @ T1

