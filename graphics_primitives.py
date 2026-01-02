"""
二维图形生成模块
实现点、直线、曲线、圆、字符的生成
"""
import pygame
import math
import os


class Point:
    """点类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def draw(self, surface, color=(0, 0, 0), size=1):
        """绘制点"""
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


class Line:
    """直线类 - 使用Bresenham算法"""
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    
    def draw(self, surface, color=(0, 0, 0)):
        """使用Bresenham算法绘制直线"""
        x1, y1 = int(self.x1), int(self.y1)
        x2, y2 = int(self.x2), int(self.y2)
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            surface.set_at((x, y), color)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy


class Circle:
    """圆类 - 使用中点圆算法"""
    def __init__(self, center_x, center_y, radius, clip_angles=None):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.clip_angles = clip_angles  # 裁剪角度列表，用于绘制圆弧
    
    def draw(self, surface, color=(0, 0, 0), clip_window=None):
        """使用中点圆算法绘制圆或圆弧"""
        import math
        
        x = 0
        y = int(self.radius)
        d = 1 - int(self.radius)
        
        cx = int(self.center_x)
        cy = int(self.center_y)
        
        def is_point_in_clip_region(px, py):
            """检查点是否在裁剪区域内"""
            # 如果有裁剪窗口，检查点是否在窗口内
            if clip_window:
                return (clip_window.x_min <= px <= clip_window.x_max and
                       clip_window.y_min <= py <= clip_window.y_max)
            return True
        
        def draw_circle_points(x, y, cx, cy):
            """绘制圆的8个对称点"""
            points = [
                (cx + x, cy + y), (cx - x, cy + y),
                (cx + x, cy - y), (cx - x, cy - y),
                (cx + y, cy + x), (cx - y, cy + x),
                (cx + y, cy - x), (cx - y, cy - x)
            ]
            for px, py in points:
                if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                    if is_point_in_clip_region(px, py):
                        surface.set_at((px, py), color)
        
        draw_circle_points(x, y, cx, cy)
        
        while x < y:
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
            draw_circle_points(x, y, cx, cy)


class BezierCurve:
    """贝塞尔曲线类"""
    def __init__(self, control_points):
        self.control_points = control_points  # 控制点列表
    
    def draw(self, surface, color=(0, 0, 0), segments=50, clip_window=None):
        """绘制贝塞尔曲线（优化：减少segments提高性能，支持裁剪）"""
        n = len(self.control_points) - 1
        
        def comb(n, k):
            """计算组合数 C(n, k)"""
            if k > n or k < 0:
                return 0
            if k == 0 or k == n:
                return 1
            result = 1
            for i in range(min(k, n - k)):
                result = result * (n - i) // (i + 1)
            return result
        
        def bezier_point(t):
            """计算贝塞尔曲线上的点"""
            result_x = 0
            result_y = 0
            for i, point in enumerate(self.control_points):
                # 伯恩斯坦基函数
                bernstein = comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
                result_x += point[0] * bernstein
                result_y += point[1] * bernstein
            return (result_x, result_y)
        
        def is_point_in_window(x, y, window):
            """检查点是否在裁剪窗口内"""
            if window is None:
                return True
            return (window.x_min <= x <= window.x_max and 
                   window.y_min <= y <= window.y_max)
        
        prev_point = bezier_point(0)
        prev_in_window = is_point_in_window(prev_point[0], prev_point[1], clip_window)
        
        for i in range(1, segments + 1):
            t = i / segments
            curr_point = bezier_point(t)
            curr_in_window = is_point_in_window(curr_point[0], curr_point[1], clip_window)
            
            # 如果当前点在窗口内，或者前一个点在窗口内，绘制线段
            if curr_in_window or prev_in_window:
                # 如果两个点都在窗口内，直接绘制
                if curr_in_window and prev_in_window:
                    pygame.draw.line(surface, color, prev_point, curr_point, 1)
                else:
                    # 需要裁剪线段，只绘制窗口内的部分
                    # 简化处理：如果至少有一个点在窗口内，就绘制
                    # 更精确的方法需要计算线段与窗口边界的交点
                    if curr_in_window or prev_in_window:
                        # 裁剪线段端点
                        clipped_prev = prev_point
                        clipped_curr = curr_point
                        
                        # 如果前一个点在窗口外，找到它与窗口的交点
                        if not prev_in_window:
                            clipped_prev = self._clip_point_to_window(prev_point, curr_point, clip_window)
                        
                        # 如果当前点在窗口外，找到它与窗口的交点
                        if not curr_in_window:
                            clipped_curr = self._clip_point_to_window(curr_point, prev_point, clip_window)
                        
                        if clipped_prev and clipped_curr:
                            pygame.draw.line(surface, color, clipped_prev, clipped_curr, 1)
            
            prev_point = curr_point
            prev_in_window = curr_in_window
    
    def _clip_point_to_window(self, point_out, point_in, window):
        """将窗口外的点裁剪到窗口边界上"""
        if window is None:
            return point_out
        
        x, y = point_out
        x_in, y_in = point_in
        
        # 计算从窗口外点到窗口内点的方向
        dx = x_in - x
        dy = y_in - y
        
        # 找到与窗口边界的交点
        intersections = []
        
        # 检查与左边界 (x = x_min) 的交点
        if dx != 0:
            t = (window.x_min - x) / dx
            if 0 <= t <= 1:
                y_intersect = y + t * dy
                if window.y_min <= y_intersect <= window.y_max:
                    intersections.append((window.x_min, y_intersect))
        
        # 检查与右边界 (x = x_max) 的交点
        if dx != 0:
            t = (window.x_max - x) / dx
            if 0 <= t <= 1:
                y_intersect = y + t * dy
                if window.y_min <= y_intersect <= window.y_max:
                    intersections.append((window.x_max, y_intersect))
        
        # 检查与上边界 (y = y_min) 的交点
        if dy != 0:
            t = (window.y_min - y) / dy
            if 0 <= t <= 1:
                x_intersect = x + t * dx
                if window.x_min <= x_intersect <= window.x_max:
                    intersections.append((x_intersect, window.y_min))
        
        # 检查与下边界 (y = y_max) 的交点
        if dy != 0:
            t = (window.y_max - y) / dy
            if 0 <= t <= 1:
                x_intersect = x + t * dx
                if window.x_min <= x_intersect <= window.x_max:
                    intersections.append((x_intersect, window.y_max))
        
        # 返回最近的交点
        if intersections:
            # 返回距离窗口外点最近的交点
            min_dist = float('inf')
            closest = None
            for inter in intersections:
                dist = ((inter[0] - x) ** 2 + (inter[1] - y) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    closest = inter
            return closest
        
        return None


class Text:
    """文本类"""
    def __init__(self, text, x, y, font_size=24):
        self.text = text
        self.x = x
        self.y = y
        self.font_size = font_size
    
    def draw(self, surface, color=(0, 0, 0)):
        """绘制文本"""
        # 使用支持中文的字体
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/msyh.ttc",   # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
            None  # 如果找不到，使用默认字体
        ]
        
        font = None
        for font_path in font_paths:
            try:
                if font_path and os.path.exists(font_path):
                    font = pygame.font.Font(font_path, self.font_size)
                    break
            except:
                continue
        
        if font is None:
            font = pygame.font.Font(None, self.font_size)
        
        text_surface = font.render(self.text, True, color)
        surface.blit(text_surface, (int(self.x), int(self.y)))

