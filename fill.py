"""
区域填充模块
实现种子填充和扫描线填充算法
"""
import pygame
import collections


class SeedFiller:
    """种子填充算法（四连通）"""
    
    @staticmethod
    def fill(surface, seed_x, seed_y, fill_color, boundary_color=None):
        """种子填充
        surface: 绘制表面
        seed_x, seed_y: 种子点坐标
        fill_color: 填充颜色
        boundary_color: 边界颜色，如果为None则填充到边界
        """
        width = surface.get_width()
        height = surface.get_height()
        
        # 获取种子点颜色
        seed_color = surface.get_at((int(seed_x), int(seed_y)))[:3]
        
        # 如果种子点已经是填充颜色，则返回
        if seed_color == fill_color:
            return
        
        # 使用队列实现
        queue = collections.deque([(int(seed_x), int(seed_y))])
        visited = set()
        
        while queue:
            x, y = queue.popleft()
            
            # 检查边界
            if x < 0 or x >= width or y < 0 or y >= height:
                continue
            
            # 检查是否已访问
            if (x, y) in visited:
                continue
            
            # 获取当前点颜色
            current_color = surface.get_at((x, y))[:3]
            
            # 检查是否需要填充
            if boundary_color is not None:
                # 如果遇到边界颜色，跳过
                if current_color == boundary_color:
                    continue
            else:
                # 如果颜色不是种子颜色，跳过
                if current_color != seed_color:
                    continue
            
            # 填充当前点
            surface.set_at((x, y), fill_color)
            visited.add((x, y))
            
            # 添加四邻域点
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            for nx, ny in neighbors:
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in visited:
                        neighbor_color = surface.get_at((nx, ny))[:3]
                        if boundary_color is not None:
                            if neighbor_color != boundary_color:
                                queue.append((nx, ny))
                        else:
                            if neighbor_color == seed_color:
                                queue.append((nx, ny))


class ScanlineFiller:
    """扫描线填充算法"""
    
    @staticmethod
    def fill_polygon(surface, vertices, fill_color):
        """扫描线填充多边形
        vertices: 多边形顶点列表 [(x1, y1), (x2, y2), ...]
        """
        if len(vertices) < 3:
            return
        
        # 找到y的最小值和最大值
        y_min = min(v[1] for v in vertices)
        y_max = max(v[1] for v in vertices)
        
        # 构建边表（ET）
        edges = []
        n = len(vertices)
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            
            if p1[1] != p2[1]:  # 忽略水平边
                if p1[1] < p2[1]:
                    y_min_edge = p1[1]
                    x_at_ymin = p1[0]
                    y_max_edge = p2[1]
                else:
                    y_min_edge = p2[1]
                    x_at_ymin = p2[0]
                    y_max_edge = p1[1]
                
                dx = (p2[0] - p1[0]) / (p2[1] - p1[1]) if p2[1] != p1[1] else 0
                edges.append({
                    'y_min': y_min_edge,
                    'y_max': y_max_edge,
                    'x': x_at_ymin,
                    'dx': dx
                })
        
        # 按y_min排序
        edges.sort(key=lambda e: e['y_min'])
        
        # 活动边表（AET）
        active_edges = []
        edge_index = 0
        
        # 逐条扫描线填充
        for y in range(int(y_min), int(y_max) + 1):
            # 将新的边加入活动边表
            while edge_index < len(edges) and edges[edge_index]['y_min'] == y:
                active_edges.append(edges[edge_index].copy())
                edge_index += 1
            
            # 移除y_max <= y的边
            active_edges = [e for e in active_edges if e['y_max'] > y]
            
            # 更新活动边表中边的x值
            for edge in active_edges:
                edge['x'] += edge['dx']
            
            # 按x值排序
            active_edges.sort(key=lambda e: e['x'])
            
            # 填充扫描线
            for i in range(0, len(active_edges), 2):
                if i + 1 < len(active_edges):
                    x_start = int(active_edges[i]['x'])
                    x_end = int(active_edges[i + 1]['x'])
                    pygame.draw.line(surface, fill_color, (x_start, y), (x_end, y))

