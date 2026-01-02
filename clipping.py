"""
二维图形裁剪模块
实现Cohen-Sutherland线段裁剪算法和Liang-Barsky算法
"""
import pygame


class ClippingWindow:
    """裁剪窗口类"""
    def __init__(self, x_min, y_min, x_max, y_max):
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
    
    def draw(self, surface, color=(255, 0, 0)):
        """绘制裁剪窗口"""
        pygame.draw.rect(surface, color, 
                        (self.x_min, self.y_min, 
                         self.x_max - self.x_min, 
                         self.y_max - self.y_min), 2)


class CohenSutherlandClipper:
    """Cohen-Sutherland线段裁剪算法"""
    INSIDE = 0  # 0000
    LEFT = 1   # 0001
    RIGHT = 2   # 0010
    BOTTOM = 4  # 0100
    TOP = 8     # 1000
    
    def __init__(self, window):
        self.window = window
    
    def compute_code(self, x, y):
        """计算点的区域码"""
        code = self.INSIDE
        if x < self.window.x_min:
            code |= self.LEFT
        elif x > self.window.x_max:
            code |= self.RIGHT
        if y < self.window.y_min:
            code |= self.BOTTOM
        elif y > self.window.y_max:
            code |= self.TOP
        return code
    
    def clip_line(self, x1, y1, x2, y2):
        """裁剪线段，返回裁剪后的线段端点，如果完全在窗口外返回None"""
        code1 = self.compute_code(x1, y1)
        code2 = self.compute_code(x2, y2)
        
        accept = False
        max_iterations = 10  # 防止无限循环
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            # 如果两个端点都在窗口内
            if code1 == 0 and code2 == 0:
                accept = True
                break
            # 如果两个端点都在窗口外的同一侧
            elif (code1 & code2) != 0:
                break
            else:
                # 选择在窗口外的端点
                code_out = code1 if code1 != 0 else code2
                
                # 找到交点（避免除零错误）
                if code_out & self.TOP:
                    if abs(y2 - y1) > 1e-10:  # 避免除零
                        x = x1 + (x2 - x1) * (self.window.y_max - y1) / (y2 - y1)
                        y = self.window.y_max
                    else:
                        break  # 水平线，无法与顶部相交
                elif code_out & self.BOTTOM:
                    if abs(y2 - y1) > 1e-10:  # 避免除零
                        x = x1 + (x2 - x1) * (self.window.y_min - y1) / (y2 - y1)
                        y = self.window.y_min
                    else:
                        break  # 水平线，无法与底部相交
                elif code_out & self.RIGHT:
                    if abs(x2 - x1) > 1e-10:  # 避免除零
                        y = y1 + (y2 - y1) * (self.window.x_max - x1) / (x2 - x1)
                        x = self.window.x_max
                    else:
                        break  # 垂直线，无法与右侧相交
                elif code_out & self.LEFT:
                    if abs(x2 - x1) > 1e-10:  # 避免除零
                        y = y1 + (y2 - y1) * (self.window.x_min - x1) / (x2 - x1)
                        x = self.window.x_min
                    else:
                        break  # 垂直线，无法与左侧相交
                
                # 替换窗口外的点
                if code_out == code1:
                    x1, y1 = x, y
                    code1 = self.compute_code(x1, y1)
                else:
                    x2, y2 = x, y
                    code2 = self.compute_code(x2, y2)
        
        if accept:
            return (x1, y1, x2, y2)
        return None


class LiangBarskyClipper:
    """Liang-Barsky线段裁剪算法"""
    def __init__(self, window):
        self.window = window
    
    def clip_line(self, x1, y1, x2, y2):
        """裁剪线段"""
        dx = x2 - x1
        dy = y2 - y1
        
        p = [-dx, dx, -dy, dy]
        q = [x1 - self.window.x_min, self.window.x_max - x1,
             y1 - self.window.y_min, self.window.y_max - y1]
        
        u1 = 0.0
        u2 = 1.0
        
        for i in range(4):
            if p[i] == 0:
                if q[i] < 0:
                    return None  # 线段平行于边界且在窗口外
            else:
                r = q[i] / p[i]
                if p[i] < 0:
                    u1 = max(u1, r)
                else:
                    u2 = min(u2, r)
        
        if u1 > u2:
            return None  # 线段完全在窗口外
        
        nx1 = x1 + u1 * dx
        ny1 = y1 + u1 * dy
        nx2 = x1 + u2 * dx
        ny2 = y1 + u2 * dy
        
        return (nx1, ny1, nx2, ny2)


class CircleClipper:
    """圆裁剪类"""
    def __init__(self, window):
        self.window = window
    
    def clip_circle(self, cx, cy, radius):
        """裁剪圆，返回裁剪后的圆弧段
        返回: 圆弧段列表 [(start_angle, end_angle), ...] 或 None（完全在窗口外）
        """
        import math
        
        # 检查圆是否与窗口相交
        closest_x = max(self.window.x_min, min(cx, self.window.x_max))
        closest_y = max(self.window.y_min, min(cy, self.window.y_max))
        dx = cx - closest_x
        dy = cy - closest_y
        distance_squared = dx * dx + dy * dy
        
        if distance_squared > radius * radius:
            return None  # 圆完全在窗口外
        
        # 计算圆与窗口边界的交点
        arcs = []
        
        # 检查圆与四条边的交点
        intersections = []
        
        # 上边 (y = y_min)
        if abs(cy - self.window.y_min) <= radius:
            discriminant = radius * radius - (cy - self.window.y_min) ** 2
            if discriminant >= 0:
                sqrt_d = math.sqrt(discriminant)
                x1 = cx - sqrt_d
                x2 = cx + sqrt_d
                if self.window.x_min <= x1 <= self.window.x_max:
                    angle = math.atan2(self.window.y_min - cy, x1 - cx)
                    intersections.append(('top', angle, (x1, self.window.y_min)))
                if self.window.x_min <= x2 <= self.window.x_max:
                    angle = math.atan2(self.window.y_min - cy, x2 - cx)
                    intersections.append(('top', angle, (x2, self.window.y_min)))
        
        # 下边 (y = y_max)
        if abs(cy - self.window.y_max) <= radius:
            discriminant = radius * radius - (cy - self.window.y_max) ** 2
            if discriminant >= 0:
                sqrt_d = math.sqrt(discriminant)
                x1 = cx - sqrt_d
                x2 = cx + sqrt_d
                if self.window.x_min <= x1 <= self.window.x_max:
                    angle = math.atan2(self.window.y_max - cy, x1 - cx)
                    intersections.append(('bottom', angle, (x1, self.window.y_max)))
                if self.window.x_min <= x2 <= self.window.x_max:
                    angle = math.atan2(self.window.y_max - cy, x2 - cx)
                    intersections.append(('bottom', angle, (x2, self.window.y_max)))
        
        # 左边 (x = x_min)
        if abs(cx - self.window.x_min) <= radius:
            discriminant = radius * radius - (cx - self.window.x_min) ** 2
            if discriminant >= 0:
                sqrt_d = math.sqrt(discriminant)
                y1 = cy - sqrt_d
                y2 = cy + sqrt_d
                if self.window.y_min <= y1 <= self.window.y_max:
                    angle = math.atan2(y1 - cy, self.window.x_min - cx)
                    intersections.append(('left', angle, (self.window.x_min, y1)))
                if self.window.y_min <= y2 <= self.window.y_max:
                    angle = math.atan2(y2 - cy, self.window.x_min - cx)
                    intersections.append(('left', angle, (self.window.x_min, y2)))
        
        # 右边 (x = x_max)
        if abs(cx - self.window.x_max) <= radius:
            discriminant = radius * radius - (cx - self.window.x_max) ** 2
            if discriminant >= 0:
                sqrt_d = math.sqrt(discriminant)
                y1 = cy - sqrt_d
                y2 = cy + sqrt_d
                if self.window.y_min <= y1 <= self.window.y_max:
                    angle = math.atan2(y1 - cy, self.window.x_max - cx)
                    intersections.append(('right', angle, (self.window.x_max, y1)))
                if self.window.y_min <= y2 <= self.window.y_max:
                    angle = math.atan2(y2 - cy, self.window.x_max - cx)
                    intersections.append(('right', angle, (self.window.x_max, y2)))
        
        # 如果圆完全在窗口内
        if (self.window.x_min <= cx - radius and cx + radius <= self.window.x_max and
            self.window.y_min <= cy - radius and cy + radius <= self.window.y_max):
            return 'full'  # 完整圆
        
        # 如果有交点，返回交点信息用于绘制圆弧
        if intersections:
            # 简化：返回交点角度列表
            angles = [item[1] for item in intersections]
            return angles
        
        # 如果圆心在窗口内但圆部分在窗口外
        if (self.window.x_min <= cx <= self.window.x_max and
            self.window.y_min <= cy <= self.window.y_max):
            return 'partial'  # 部分圆
        
        return None
    
    def is_circle_inside_window(self, cx, cy, radius):
        """判断圆是否完全在窗口内"""
        return (cx - radius >= self.window.x_min and 
                cx + radius <= self.window.x_max and
                cy - radius >= self.window.y_min and 
                cy + radius <= self.window.y_max)

