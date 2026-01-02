"""
图形系统核心模块
整合所有功能模块
"""
import pygame
import uuid
from graphics_primitives import Point, Line, Circle, BezierCurve, Text
from clipping import ClippingWindow, CohenSutherlandClipper, CircleClipper
from transform import Transform
from fill import SeedFiller, ScanlineFiller
from command_system import CommandManager, CommandType, DrawPointCommand, \
    DrawLineCommand, DrawCircleCommand, DrawCurveCommand, DrawTextCommand, \
    ClipCommand, TransformCommand, FillCommand, DeleteCommand, ClearCommand


class GraphicsSystem:
    """图形系统主类"""
    
    def __init__(self, canvas_width=800, canvas_height=600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.canvas = pygame.Surface((canvas_width, canvas_height))
        self.canvas.fill((255, 255, 255))  # 白色背景
        
        self.objects = {}  # 存储所有图形对象 {id: {'type': ..., 'data': ...}}
        self.clipping_window = None
        self.command_manager = CommandManager()
        
        # 用于撤销的状态保存
        self.object_states_backup = {}
    
    def add_point(self, x, y, color=(0, 0, 0), size=1):
        """添加点"""
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'point',
            'data': {
                'x': x, 'y': y, 'color': color, 'size': size
            }
        }
        self._redraw()
        return obj_id
    
    def add_line(self, x1, y1, x2, y2, color=(0, 0, 0)):
        """添加直线"""
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'line',
            'data': {
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'color': color
            }
        }
        self._redraw()
        return obj_id
    
    def add_circle(self, cx, cy, radius, color=(0, 0, 0)):
        """添加圆"""
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'circle',
            'data': {
                'cx': cx, 'cy': cy, 'radius': radius, 'color': color
            }
        }
        self._redraw()
        return obj_id
    
    def add_curve(self, control_points, color=(0, 0, 0)):
        """添加曲线"""
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'curve',
            'data': {
                'control_points': control_points, 'color': color
            }
        }
        self._redraw()
        return obj_id
    
    def add_text(self, text, x, y, color=(0, 0, 0), font_size=24):
        """添加文本"""
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'text',
            'data': {
                'text': text, 'x': x, 'y': y, 'color': color, 'font_size': font_size
            }
        }
        self._redraw()
        return obj_id
    
    def remove_object(self, obj_id):
        """删除对象"""
        if obj_id in self.objects:
            del self.objects[obj_id]
            self._redraw()
            return True
        return False
    
    def remove_objects(self, obj_ids):
        """删除多个对象，返回被删除的对象数据"""
        deleted = []
        for obj_id in obj_ids:
            if obj_id in self.objects:
                deleted.append((obj_id, self.objects[obj_id].copy()))
                del self.objects[obj_id]
        self._redraw()
        return deleted
    
    def restore_objects(self, objects_data):
        """恢复对象"""
        for obj_id, obj_data in objects_data:
            self.objects[obj_id] = obj_data
        self._redraw()
    
    def clear_all(self):
        """清空所有对象"""
        cleared = list(self.objects.items())
        self.objects.clear()
        self._redraw()
        return cleared
    
    def set_clipping_window(self, x_min, y_min, x_max, y_max):
        """设置裁剪窗口"""
        self.clipping_window = ClippingWindow(x_min, y_min, x_max, y_max)
        self._redraw()
    
    def clip_objects(self, x_min, y_min, x_max, y_max, object_ids=None):
        """裁剪对象"""
        window = ClippingWindow(x_min, y_min, x_max, y_max)
        line_clipper = CohenSutherlandClipper(window)
        circle_clipper = CircleClipper(window)
        clipped_info = []
        objects_to_delete = []  # 收集要删除的对象ID
        
        if object_ids is None:
            object_ids = list(self.objects.keys())
        
        for obj_id in object_ids:
            if obj_id not in self.objects:
                continue
            
            obj = self.objects[obj_id]
            obj_type = obj['type']
            obj_data = obj['data']
            
            if obj_type == 'line':
                result = line_clipper.clip_line(
                    obj_data['x1'], obj_data['y1'],
                    obj_data['x2'], obj_data['y2']
                )
                if result:
                    # 更新线段端点
                    obj_data['x1'], obj_data['y1'], obj_data['x2'], obj_data['y2'] = result
                    clipped_info.append(obj_id)
                else:
                    # 线段完全在窗口外，标记为删除
                    clipped_info.append(obj_id)
                    objects_to_delete.append(obj_id)
            
            elif obj_type == 'point':
                # 检查点是否在窗口内
                x, y = obj_data['x'], obj_data['y']
                if not (x_min <= x <= x_max and y_min <= y <= y_max):
                    # 点在窗口外，标记为删除
                    clipped_info.append(obj_id)
                    objects_to_delete.append(obj_id)
                else:
                    clipped_info.append(obj_id)
            
            elif obj_type == 'circle':
                # 检查圆是否与窗口相交并裁剪
                cx, cy, radius = obj_data['cx'], obj_data['cy'], obj_data['radius']
                clip_result = circle_clipper.clip_circle(cx, cy, radius)
                
                if clip_result is None:
                    # 圆完全在窗口外，标记为删除
                    clipped_info.append(obj_id)
                    objects_to_delete.append(obj_id)
                elif clip_result == 'full':
                    # 圆完全在窗口内，保留，清除之前的裁剪信息
                    if 'clip_window' in obj_data:
                        del obj_data['clip_window']
                    clipped_info.append(obj_id)
                elif clip_result == 'partial' or isinstance(clip_result, list):
                    # 圆部分在窗口内，保存裁剪窗口信息用于绘制时裁剪
                    obj_data['clip_window'] = {
                        'x_min': x_min, 'y_min': y_min,
                        'x_max': x_max, 'y_max': y_max
                    }
                    if isinstance(clip_result, list):
                        obj_data['clip_angles'] = clip_result
                    clipped_info.append(obj_id)
                else:
                    clipped_info.append(obj_id)
            
            elif obj_type == 'curve':
                # 检查曲线是否与窗口相交
                control_points = obj_data['control_points']
                # 检查控制点的边界框是否与窗口相交
                min_x = min(p[0] for p in control_points)
                max_x = max(p[0] for p in control_points)
                min_y = min(p[1] for p in control_points)
                max_y = max(p[1] for p in control_points)
                
                # 如果边界框与窗口不相交，删除曲线
                if (max_x < x_min or min_x > x_max or 
                    max_y < y_min or min_y > y_max):
                    clipped_info.append(obj_id)
                    objects_to_delete.append(obj_id)
                else:
                    # 曲线与窗口相交，保存裁剪窗口信息用于绘制时裁剪
                    obj_data['clip_window'] = {
                        'x_min': x_min, 'y_min': y_min,
                        'x_max': x_max, 'y_max': y_max
                    }
                    clipped_info.append(obj_id)
            
            elif obj_type == 'text':
                # 检查文本位置是否在窗口内
                x, y = obj_data['x'], obj_data['y']
                if not (x_min <= x <= x_max and y_min <= y <= y_max):
                    # 文本在窗口外，标记为删除
                    clipped_info.append(obj_id)
                    objects_to_delete.append(obj_id)
                else:
                    clipped_info.append(obj_id)
        
        # 删除完全在窗口外的对象
        for obj_id in objects_to_delete:
            if obj_id in self.objects:
                del self.objects[obj_id]
        
        # 裁剪完成后清除裁剪窗口显示
        self.clipping_window = None
        
        self._redraw()
        return clipped_info
    
    def restore_clipped_objects(self, clipped_info):
        """恢复裁剪前的对象（简化实现）"""
        # 实际实现中需要保存裁剪前的状态
        pass
    
    def transform_objects(self, object_ids, transform_type, params):
        """变换对象"""
        for obj_id in object_ids:
            if obj_id not in self.objects:
                continue
            
            obj = self.objects[obj_id]
            obj_type = obj['type']
            obj_data = obj['data']
            
            # 圆的缩放需要特殊处理
            if obj_type == 'circle' and transform_type == 'scale':
                sx = params.get('sx', 1)
                sy = params.get('sy', 1)
                # 使用平均缩放因子，保持圆形
                scale_factor = (sx + sy) / 2.0
                center_x = params.get('center_x', 0)
                center_y = params.get('center_y', 0)
                
                # 变换圆心
                cx, cy = obj_data['cx'], obj_data['cy']
                # 平移到原点
                cx -= center_x
                cy -= center_y
                # 缩放
                cx *= scale_factor
                cy *= scale_factor
                # 平移回去
                cx += center_x
                cy += center_y
                
                # 更新圆心和半径
                obj_data['cx'] = cx
                obj_data['cy'] = cy
                obj_data['radius'] = obj_data['radius'] * scale_factor
            else:
                # 其他类型的变换
                # 获取对象的点
                points = self._get_object_points(obj_type, obj_data)
                
                # 执行变换
                if transform_type == 'translate':
                    tx, ty = params.get('tx', 0), params.get('ty', 0)
                    new_points = Transform.translate(points, tx, ty)
                elif transform_type == 'rotate':
                    angle = params.get('angle', 0)
                    center_x = params.get('center_x', 0)
                    center_y = params.get('center_y', 0)
                    new_points = Transform.rotate(points, angle, center_x, center_y)
                elif transform_type == 'scale':
                    sx, sy = params.get('sx', 1), params.get('sy', 1)
                    center_x = params.get('center_x', 0)
                    center_y = params.get('center_y', 0)
                    new_points = Transform.scale(points, sx, sy, center_x, center_y)
                else:
                    new_points = points
                
                # 更新对象数据
                self._update_object_from_points(obj_type, obj_data, new_points)
        
        self._redraw()
    
    def _get_object_points(self, obj_type, obj_data):
        """获取对象的点列表"""
        if obj_type == 'point':
            return [(obj_data['x'], obj_data['y'])]
        elif obj_type == 'line':
            return [(obj_data['x1'], obj_data['y1']), (obj_data['x2'], obj_data['y2'])]
        elif obj_type == 'circle':
            # 圆的变换需要特殊处理，这里简化
            return [(obj_data['cx'], obj_data['cy'])]
        elif obj_type == 'curve':
            return obj_data['control_points']
        elif obj_type == 'text':
            return [(obj_data['x'], obj_data['y'])]
        return []
    
    def _update_object_from_points(self, obj_type, obj_data, points):
        """从点列表更新对象数据"""
        if obj_type == 'point' and len(points) > 0:
            obj_data['x'], obj_data['y'] = points[0]
        elif obj_type == 'line' and len(points) >= 2:
            obj_data['x1'], obj_data['y1'] = points[0]
            obj_data['x2'], obj_data['y2'] = points[1]
        elif obj_type == 'circle' and len(points) > 0:
            obj_data['cx'], obj_data['cy'] = points[0]
        elif obj_type == 'curve':
            obj_data['control_points'] = points
        elif obj_type == 'text' and len(points) > 0:
            obj_data['x'], obj_data['y'] = points[0]
    
    def seed_fill(self, x, y, color):
        """种子填充"""
        SeedFiller.fill(self.canvas, x, y, color)
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'fill',
            'data': {'fill_type': 'seed', 'x': x, 'y': y, 'color': color}
        }
        return obj_id
    
    def scanline_fill(self, vertices, color):
        """扫描线填充"""
        ScanlineFiller.fill_polygon(self.canvas, vertices, color)
        obj_id = str(uuid.uuid4())
        self.objects[obj_id] = {
            'type': 'fill',
            'data': {'fill_type': 'scanline', 'vertices': vertices, 'color': color}
        }
        return obj_id
    
    def save_object_states(self, object_ids):
        """保存对象状态（用于撤销）"""
        states = []
        for obj_id in object_ids:
            if obj_id in self.objects:
                states.append((obj_id, self.objects[obj_id].copy()))
        return states
    
    def restore_object_states(self, states):
        """恢复对象状态"""
        for obj_id, obj_data in states:
            self.objects[obj_id] = obj_data
        self._redraw()
    
    def _redraw(self):
        """重绘画布"""
        # 清空画布
        self.canvas.fill((255, 255, 255))
        
        # 绘制所有对象
        for obj_id, obj in self.objects.items():
            obj_type = obj['type']
            obj_data = obj['data']
            
            if obj_type == 'point':
                point = Point(obj_data['x'], obj_data['y'])
                point.draw(self.canvas, obj_data['color'], obj_data.get('size', 1))
            elif obj_type == 'line':
                line = Line(obj_data['x1'], obj_data['y1'], 
                           obj_data['x2'], obj_data['y2'])
                line.draw(self.canvas, obj_data['color'])
            elif obj_type == 'circle':
                clip_angles = obj_data.get('clip_angles', None)
                circle = Circle(obj_data['cx'], obj_data['cy'], obj_data['radius'], clip_angles)
                # 如果有保存的裁剪窗口信息，使用它；否则使用当前的裁剪窗口
                clip_window_info = obj_data.get('clip_window', None)
                if clip_window_info:
                    from clipping import ClippingWindow
                    clip_window = ClippingWindow(
                        clip_window_info['x_min'], clip_window_info['y_min'],
                        clip_window_info['x_max'], clip_window_info['y_max']
                    )
                else:
                    clip_window = self.clipping_window if self.clipping_window else None
                circle.draw(self.canvas, obj_data['color'], clip_window=clip_window)
            elif obj_type == 'curve':
                curve = BezierCurve(obj_data['control_points'])
                # 如果有保存的裁剪窗口信息，使用它；否则使用当前的裁剪窗口
                clip_window_info = obj_data.get('clip_window', None)
                if clip_window_info:
                    from clipping import ClippingWindow
                    clip_window = ClippingWindow(
                        clip_window_info['x_min'], clip_window_info['y_min'],
                        clip_window_info['x_max'], clip_window_info['y_max']
                    )
                else:
                    clip_window = self.clipping_window if self.clipping_window else None
                curve.draw(self.canvas, obj_data['color'], segments=50, clip_window=clip_window)
            elif obj_type == 'text':
                text = Text(obj_data['text'], obj_data['x'], obj_data['y'],
                           obj_data.get('font_size', 24))
                text.draw(self.canvas, obj_data['color'])
        
        # 绘制裁剪窗口
        if self.clipping_window:
            self.clipping_window.draw(self.canvas)
    
    def get_canvas(self):
        """获取画布"""
        return self.canvas

