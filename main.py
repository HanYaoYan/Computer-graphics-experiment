"""
计算机图形学实验 - 主程序
图形交互系统
"""
import pygame
import sys
import math
import os
from graphics_system import GraphicsSystem
from file_format import GraphicsFileFormat
from command_system import CommandManager, CommandType, DrawPointCommand, \
    DrawLineCommand, DrawCircleCommand, DrawCurveCommand, DrawTextCommand, \
    ClipCommand, TransformCommand, FillCommand, DeleteCommand, ClearCommand


class GraphicsEditor:
    """图形编辑器主类"""
    
    def __init__(self):
        pygame.init()
        self.width = 1000
        self.height = 700
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("计算机图形学实验 - 图形交互系统")
        
        # 创建图形系统
        self.graphics_system = GraphicsSystem(800, 600)
        
        # 工具栏区域
        self.toolbar_rect = pygame.Rect(800, 0, 200, self.height)
        
        # 当前工具
        self.current_tool = 'select'
        self.tools = {
            'select': '选择',
            'point': '点',
            'line': '直线',
            'circle': '圆',
            'curve': '曲线',
            'text': '文本',
            'clip': '裁剪',
            'fill_seed': '种子填充',
            'fill_scanline': '扫描填充',
            'transform': '变换',
            'zoom': '缩放'
        }
        
        # 绘图状态
        self.drawing = False
        self.start_pos = None
        self.current_pos = None
        self.curve_points = []
        self.selected_objects = []
        
        # 缩放状态
        self.zoom_factor = 1.0
        self.effective_zoom_factor = 1.0  # 实际有效的缩放因子（考虑尺寸限制）
        self.zoom_center = (400, 300)  # 缩放中心点
        self.zoom_start_y = None  # 缩放开始时的鼠标Y坐标
        
        # 变换输入状态
        self.transform_input_mode = None  # 'translate', 'rotate', 'scale'
        self.input_text = ""
        self.input_active = False
        self.input_prompt = ""
        
        # 文本输入状态
        self.text_input_mode = False  # 是否处于文本输入模式
        self.text_input_pos = None  # 文本输入位置 (x, y)
        
        # 颜色选择
        self.current_color = (0, 0, 0)
        self.colors = [
            (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 128, 128)
        ]
        
        # 字体 - 使用支持中文的字体
        # Windows系统字体路径
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/msyh.ttc",   # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
            None  # 如果找不到，使用默认字体
        ]
        
        self.font = None
        self.small_font = None
        
        for font_path in font_paths:
            try:
                if font_path and os.path.exists(font_path):
                    self.font = pygame.font.Font(font_path, 24)
                    self.small_font = pygame.font.Font(font_path, 18)
                    break
            except:
                continue
        
        # 如果所有字体都失败，使用默认字体
        if self.font is None:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        
        # 文件路径
        self.current_file = None
        
        # 消息提示
        self.message = ""
        self.message_timer = 0
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.QUIT:
            return False
        
        # 鼠标事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.handle_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event)
        
        # 键盘事件
        elif event.type == pygame.KEYDOWN:
            self.handle_key_down(event)
        
        return True
    
    def handle_mouse_down(self, event):
        """处理鼠标按下"""
        x, y = event.pos
        
        # 检查是否点击工具栏
        if self.toolbar_rect.collidepoint(x, y):
            self.handle_toolbar_click(x, y)
            return
        
        # 转换到画布坐标（考虑缩放）
        canvas_x, canvas_y = self.screen_to_canvas(x, y)
        
        if self.current_tool == 'select':
            # 选择工具：点击对象进行选择
            self.select_object_at(canvas_x, canvas_y)
        
        elif self.current_tool == 'point':
            cmd = DrawPointCommand({
                'x': canvas_x, 'y': canvas_y,
                'color': self.current_color, 'size': 2
            })
            self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
        
        elif self.current_tool == 'line':
            self.drawing = True
            self.start_pos = (canvas_x, canvas_y)
        
        elif self.current_tool == 'circle':
            self.drawing = True
            self.start_pos = (canvas_x, canvas_y)
        
        elif self.current_tool == 'curve':
            # 长按绘制：按下鼠标开始记录点
            self.drawing = True
            self.start_pos = (canvas_x, canvas_y)
            self.curve_points = [(canvas_x, canvas_y)]  # 初始化曲线点列表
        
        elif self.current_tool == 'text':
            # 启动文本输入模式
            self.text_input_mode = True
            self.text_input_pos = (canvas_x, canvas_y)
            self.input_text = ""
            # 取消变换输入（如果正在输入）
            if self.input_active:
                self.cancel_transform_input()
        
        elif self.current_tool == 'clip':
            # 开始绘制裁剪窗口
            self.drawing = True
            self.start_pos = (canvas_x, canvas_y)
        
        elif self.current_tool == 'fill_seed':
            cmd = FillCommand({
                'fill_type': 'seed',
                'x': canvas_x, 'y': canvas_y,
                'color': self.current_color
            })
            self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
        
        elif self.current_tool == 'fill_scanline':
            # 需要先选择多边形顶点，这里简化处理
            if not hasattr(self, 'polygon_points'):
                self.polygon_points = []
            self.polygon_points.append((canvas_x, canvas_y))
            if len(self.polygon_points) >= 3:
                cmd = FillCommand({
                    'fill_type': 'scanline',
                    'vertices': self.polygon_points,
                    'color': self.current_color
                })
                self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                self.polygon_points = []
        
        elif self.current_tool == 'zoom':
            # 缩放工具：开始缩放
            self.drawing = True
            self.start_pos = (canvas_x, canvas_y)
            self.zoom_start_y = y
            self.zoom_center = (canvas_x, canvas_y)
            # 如果有选中的对象，初始化对象缩放因子
            if len(self.selected_objects) > 0:
                self.object_zoom_factor = 1.0
    
    def handle_mouse_up(self, event):
        """处理鼠标释放"""
        if not self.drawing:
            return
        
        x, y = event.pos
        # 转换到画布坐标（考虑缩放）
        canvas_x, canvas_y = self.screen_to_canvas(x, y)
        
        if self.current_tool == 'line':
            if self.start_pos:
                cmd = DrawLineCommand({
                    'x1': self.start_pos[0], 'y1': self.start_pos[1],
                    'x2': canvas_x, 'y2': canvas_y,
                    'color': self.current_color
                })
                self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                self.drawing = False
        
        elif self.current_tool == 'circle':
            if self.start_pos:
                radius = math.sqrt(
                    (canvas_x - self.start_pos[0]) ** 2 +
                    (canvas_y - self.start_pos[1]) ** 2
                )
                cmd = DrawCircleCommand({
                    'cx': self.start_pos[0], 'cy': self.start_pos[1],
                    'radius': radius, 'color': self.current_color
                })
                self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                self.drawing = False
        
        elif self.current_tool == 'curve':
            # 长按绘制：释放鼠标时完成曲线绘制
            if self.start_pos and len(self.curve_points) >= 2:
                # 如果点数少于4个，使用线性插值补充到4个控制点
                if len(self.curve_points) < 4:
                    # 补充控制点使其成为4个
                    while len(self.curve_points) < 4:
                        if len(self.curve_points) == 1:
                            # 只有一个点，添加3个相同点
                            self.curve_points.extend([self.curve_points[0]] * 3)
                        elif len(self.curve_points) == 2:
                            # 两个点，在中间和末尾各添加一个
                            mid = ((self.curve_points[0][0] + self.curve_points[1][0]) / 2,
                                  (self.curve_points[0][1] + self.curve_points[1][1]) / 2)
                            self.curve_points.append(mid)
                            self.curve_points.append(self.curve_points[1])
                        elif len(self.curve_points) == 3:
                            # 三个点，添加最后一个点
                            self.curve_points.append(self.curve_points[2])
                
                # 使用所有点，分段绘制多条贝塞尔曲线以保留完整轨迹
                # 每4个点为一组，每组绘制一条贝塞尔曲线
                for i in range(0, len(self.curve_points) - 3, 3):
                    # 使用4个连续的点作为控制点（重叠一个点以保持连续性）
                    control_points = self.curve_points[i:i+4]
                    if len(control_points) == 4:
                        cmd = DrawCurveCommand({
                            'control_points': control_points,
                            'color': self.current_color
                        })
                        self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                
                # 处理剩余的点（如果还有3个或更少的点）
                remaining = len(self.curve_points) % 4
                if remaining > 0 and len(self.curve_points) >= 4:
                    # 使用最后4个点再绘制一条曲线
                    control_points = self.curve_points[-4:]
                    cmd = DrawCurveCommand({
                        'control_points': control_points,
                        'color': self.current_color
                    })
                    self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                
                self.curve_points = []
            self.drawing = False
        
        elif self.current_tool == 'clip':
            if self.start_pos:
                # 完成裁剪窗口并执行裁剪
                x_min = min(self.start_pos[0], canvas_x)
                y_min = min(self.start_pos[1], canvas_y)
                x_max = max(self.start_pos[0], canvas_x)
                y_max = max(self.start_pos[1], canvas_y)
                
                # 确保窗口大小合理
                if abs(x_max - x_min) > 10 and abs(y_max - y_min) > 10:
                    self.graphics_system.set_clipping_window(x_min, y_min, x_max, y_max)
                    cmd = ClipCommand({
                        'x_min': x_min, 'y_min': y_min,
                        'x_max': x_max, 'y_max': y_max
                    })
                    self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                self.drawing = False
        
        elif self.current_tool == 'zoom':
            # 缩放工具：结束缩放
            self.drawing = False
            self.zoom_start_y = None
            # 清除对象缩放因子
            if hasattr(self, 'object_zoom_factor'):
                delattr(self, 'object_zoom_factor')
    
    def handle_mouse_motion(self, event):
        """处理鼠标移动"""
        if self.drawing and self.start_pos:
            self.current_pos = event.pos
            # 如果是曲线工具，记录移动轨迹
            if self.current_tool == 'curve':
                x, y = event.pos
                # 限制点的密度，避免点太多（每10像素记录一个点）
                if len(self.curve_points) == 0 or \
                   ((x - self.curve_points[-1][0]) ** 2 + (y - self.curve_points[-1][1]) ** 2) > 100:
                    self.curve_points.append((x, y))
                    # 限制最大点数，避免内存问题
                    if len(self.curve_points) > 100:
                        # 保留前几个点和最后几个点
                        self.curve_points = self.curve_points[:10] + self.curve_points[-10:]
            # 如果是缩放工具，计算缩放比例
            elif self.current_tool == 'zoom' and self.zoom_start_y is not None:
                x, y = event.pos
                # 如果有选中的对象，缩放选中的对象；否则缩放整个画布视图
                if len(self.selected_objects) > 0:
                    # 缩放选中的对象
                    # 计算鼠标移动的距离（向上为放大，向下为缩小）
                    dy = self.zoom_start_y - y  # 向上移动为正值
                    # 根据移动距离计算缩放比例（每100像素对应0.1的缩放变化）
                    scale_change = dy / 1000.0  # 缩放变化量
                    # 累积缩放因子（从1.0开始）
                    if not hasattr(self, 'object_zoom_factor'):
                        self.object_zoom_factor = 1.0
                    new_object_zoom = self.object_zoom_factor * (1.0 + scale_change)
                    # 限制缩放范围（0.1倍到5倍）
                    new_object_zoom = max(0.1, min(5.0, new_object_zoom))
                    if abs(new_object_zoom - self.object_zoom_factor) > 0.01:  # 避免过于频繁的更新
                        # 计算相对缩放比例
                        relative_scale = new_object_zoom / self.object_zoom_factor
                        # 应用缩放变换到选中的对象
                        center_x, center_y = self._calculate_selection_center()
                        self.apply_transform('scale', {
                            'sx': relative_scale,
                            'sy': relative_scale,
                            'center_x': center_x,
                            'center_y': center_y
                        })
                        self.object_zoom_factor = new_object_zoom
                        self.zoom_start_y = y  # 更新起始位置，实现累积缩放
                else:
                    # 缩放整个画布视图
                    # 计算鼠标移动的距离（向上为放大，向下为缩小）
                    dy = self.zoom_start_y - y  # 向上移动为正值
                    # 根据移动距离计算缩放比例（每100像素对应0.1的缩放变化）
                    scale_change = dy / 1000.0  # 缩放变化量
                    new_zoom = self.zoom_factor * (1.0 + scale_change)
                    # 限制缩放范围（0.1倍到10倍，允许更大的缩放）
                    new_zoom = max(0.1, min(10.0, new_zoom))
                    if abs(new_zoom - self.zoom_factor) > 0.01:  # 避免过于频繁的更新
                        self.zoom_factor = new_zoom
                        self.zoom_start_y = y  # 更新起始位置，实现累积缩放
    
    def handle_toolbar_click(self, x, y):
        """处理工具栏点击"""
        # 工具按钮
        tool_y = 20
        for tool_name, tool_label in self.tools.items():
            if 10 <= x - 800 <= 190 and tool_y <= y <= tool_y + 30:
                self.current_tool = tool_name
                if tool_name == 'fill_scanline':
                    self.polygon_points = []
                # 切换工具时取消输入
                if self.input_active:
                    self.cancel_transform_input()
                break
            tool_y += 35
        
        # 命令系统按钮
        if 810 <= x <= 895 and 680 <= y <= 705:
            # 撤销按钮
            if self.graphics_system.command_manager.can_undo():
                self.graphics_system.command_manager.undo(self.graphics_system)
        elif 905 <= x <= 990 and 680 <= y <= 705:
            # 重做按钮
            if self.graphics_system.command_manager.can_redo():
                self.graphics_system.command_manager.redo(self.graphics_system)
        
        # 颜色选择
        color_y = 400
        for i, color in enumerate(self.colors):
            if 10 <= x - 800 <= 50 and color_y <= y <= color_y + 30:
                self.current_color = color
                break
            if (i + 1) % 4 == 0:
                color_y += 35
            else:
                color_y += 0
        
        # 文件操作按钮
        if 10 <= x - 800 <= 190 and 550 <= y <= 580:
            self.save_file()
        elif 10 <= x - 800 <= 190 and 590 <= y <= 620:
            self.load_file()
        elif 10 <= x - 800 <= 190 and 630 <= y <= 660:
            cmd = ClearCommand({})
            self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
    
    def handle_key_down(self, event):
        """处理键盘按下"""
        # Ctrl+Z: 撤销
        if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.graphics_system.command_manager.undo(self.graphics_system)
        # Ctrl+Y: 重做
        elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.graphics_system.command_manager.redo(self.graphics_system)
        # Ctrl+S: 保存
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.save_file()
        # Ctrl+O: 打开
        elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.load_file()
        # 变换快捷键（需要先选择对象）
        elif self.current_tool == 'transform' and len(self.selected_objects) > 0:
            # 方向键：平移
            if event.key == pygame.K_UP:
                self.apply_transform('translate', {'tx': 0, 'ty': -10})
            elif event.key == pygame.K_DOWN:
                self.apply_transform('translate', {'tx': 0, 'ty': 10})
            elif event.key == pygame.K_LEFT:
                self.apply_transform('translate', {'tx': -10, 'ty': 0})
            elif event.key == pygame.K_RIGHT:
                self.apply_transform('translate', {'tx': 10, 'ty': 0})
            # T: 平移（输入坐标）
            elif event.key == pygame.K_t:
                self.start_transform_input('translate')
            # R: 旋转（输入角度）
            elif event.key == pygame.K_r:
                self.start_transform_input('rotate')
            # S: 缩放（输入缩放因子）
            elif event.key == pygame.K_s:
                self.start_transform_input('scale')
            # Delete: 删除选中的对象
            elif event.key == pygame.K_DELETE:
                self.delete_selected_objects()
            # Enter: 确认输入
            elif event.key == pygame.K_RETURN and self.input_active:
                self.confirm_transform_input()
            # Escape: 取消输入
            elif event.key == pygame.K_ESCAPE and self.input_active:
                self.cancel_transform_input()
            # 输入文本
            elif self.input_active:
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.unicode.isprintable():
                    self.input_text += event.unicode
        
        # 文本输入模式
        elif self.text_input_mode:
            if event.key == pygame.K_RETURN:
                # 确认文本输入
                if self.text_input_pos and len(self.input_text) > 0:
                    cmd = DrawTextCommand({
                        'text': self.input_text, 
                        'x': self.text_input_pos[0], 
                        'y': self.text_input_pos[1],
                        'color': self.current_color, 
                        'font_size': 24
                    })
                    self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
                self.text_input_mode = False
                self.text_input_pos = None
                self.input_text = ""
            elif event.key == pygame.K_ESCAPE:
                # 取消文本输入
                self.text_input_mode = False
                self.text_input_pos = None
                self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                if len(self.input_text) > 0:
                    self.input_text = self.input_text[:-1]
            elif event.unicode.isprintable():
                self.input_text += event.unicode
        
        # 选择工具快捷键
        elif self.current_tool == 'select':
            # Delete: 删除选中的对象
            if event.key == pygame.K_DELETE:
                self.delete_selected_objects()
            # A: 全选
            elif event.key == pygame.K_a and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.select_all_objects()
    
    def select_object_at(self, x, y):
        """在指定位置选择对象"""
        import math
        # 根据缩放因子调整选择阈值（屏幕上的像素阈值转换为画布坐标阈值）
        # 屏幕上的阈值除以缩放因子得到画布上的阈值
        # 使用有效缩放因子，确保与显示一致
        # 先计算有效缩放因子（如果还没有计算）
        if abs(self.zoom_factor - 1.0) > 0.01:
            self._get_zoom_offset()  # 这会计算并设置 effective_zoom_factor
        effective_zoom = getattr(self, 'effective_zoom_factor', 1.0)
        
        screen_threshold_point = 10
        screen_threshold_line = 5
        screen_threshold_circle = 5
        screen_threshold_text = 20
        screen_threshold_curve = 10
        
        # 转换为画布坐标阈值，使用有效缩放因子
        canvas_threshold_point = screen_threshold_point / max(0.1, effective_zoom)
        canvas_threshold_line = screen_threshold_line / max(0.1, effective_zoom)
        canvas_threshold_circle = screen_threshold_circle / max(0.1, effective_zoom)
        canvas_threshold_text = screen_threshold_text / max(0.1, effective_zoom)
        canvas_threshold_curve = screen_threshold_curve / max(0.1, effective_zoom)
        
        # 查找点击位置的对象
        selected_id = None
        min_dist = float('inf')
        
        for obj_id, obj in self.graphics_system.objects.items():
            obj_type = obj['type']
            obj_data = obj['data']
            
            # 计算点到对象的距离
            dist = None
            if obj_type == 'point':
                px, py = obj_data['x'], obj_data['y']
                dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if dist < canvas_threshold_point:
                    if dist < min_dist:
                        min_dist = dist
                        selected_id = obj_id
            elif obj_type == 'line':
                x1, y1 = obj_data['x1'], obj_data['y1']
                x2, y2 = obj_data['x2'], obj_data['y2']
                # 计算点到线段的距离
                dx = x2 - x1
                dy = y2 - y1
                length_sq = dx * dx + dy * dy
                if length_sq < 1e-10:  # 线段长度接近0，视为点
                    dist = math.sqrt((x - x1) ** 2 + (y - y1) ** 2)
                else:
                    t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / length_sq))
                    proj_x = x1 + t * dx
                    proj_y = y1 + t * dy
                    dist = math.sqrt((x - proj_x) ** 2 + (y - proj_y) ** 2)
                # 增加选择阈值，使直线更容易被选中
                if dist < canvas_threshold_line * 1.5:
                    if dist < min_dist:
                        min_dist = dist
                        selected_id = obj_id
            elif obj_type == 'circle':
                cx, cy = obj_data['cx'], obj_data['cy']
                radius = obj_data['radius']
                # 计算点到圆心的距离
                dist_to_center = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                # 计算点到圆的距离（点到圆周的距离）
                dist = abs(dist_to_center - radius)
                # 对于圆，只要点在圆内或距离圆周小于阈值，就能选中整个圆
                # 点在圆内：dist_to_center <= radius
                # 点在圆附近：dist <= canvas_threshold_circle
                if dist_to_center <= radius or dist <= canvas_threshold_circle:
                    # 使用点到圆周的距离作为选择优先级（距离越近优先级越高）
                    if dist < min_dist:
                        min_dist = dist
                        selected_id = obj_id
            elif obj_type == 'text':
                px, py = obj_data['x'], obj_data['y']
                dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if dist < canvas_threshold_text:
                    if dist < min_dist:
                        min_dist = dist
                        selected_id = obj_id
            elif obj_type == 'curve':
                # 检查是否点击在整条曲线上（不是单个线段）
                control_points = obj_data['control_points']
                if len(control_points) >= 2:
                    min_curve_dist = float('inf')
                    
                    # 对整条曲线进行采样，找到点到曲线的最短距离
                    # 使用更多的采样点以确保覆盖整条曲线
                    n = len(control_points) - 1
                    
                    def comb(n, k):
                        """计算组合数"""
                        if k > n or k < 0:
                            return 0
                        if k == 0 or k == n:
                            return 1
                        result = 1
                        for i in range(min(k, n - k)):
                            result = result * (n - i) // (i + 1)
                        return result
                    
                    # 采样曲线上的点，检查点到曲线的距离
                    # 使用更密集的采样（每2%采样一次，共51个点）以提高选择精度
                    for t in range(0, 101, 2):  # 采样51个点
                        t_val = t / 100.0
                        # 计算贝塞尔曲线上的点
                        px, py = 0, 0
                        for i, cp in enumerate(control_points):
                            bernstein = comb(n, i) * (t_val ** i) * ((1 - t_val) ** (n - i))
                            px += cp[0] * bernstein
                            py += cp[1] * bernstein
                        
                        # 计算点到采样点的距离
                        curve_dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                        if curve_dist < min_curve_dist:
                            min_curve_dist = curve_dist
                    
                    # 对于曲线，还需要检查相邻采样点之间的线段
                    # 这样可以更准确地检测点击是否在曲线上
                    for t in range(0, 100, 2):  # 检查相邻点之间的线段
                        t1 = t / 100.0
                        t2 = (t + 2) / 100.0
                        
                        # 计算两个采样点
                        px1, py1 = 0, 0
                        px2, py2 = 0, 0
                        for i, cp in enumerate(control_points):
                            bern1 = comb(n, i) * (t1 ** i) * ((1 - t1) ** (n - i))
                            bern2 = comb(n, i) * (t2 ** i) * ((1 - t2) ** (n - i))
                            px1 += cp[0] * bern1
                            py1 += cp[1] * bern1
                            px2 += cp[0] * bern2
                            py2 += cp[1] * bern2
                        
                        # 计算点到线段的距离
                        dx = px2 - px1
                        dy = py2 - py1
                        length_sq = dx * dx + dy * dy
                        if length_sq > 1e-10:
                            t_param = max(0, min(1, ((x - px1) * dx + (y - py1) * dy) / length_sq))
                            proj_x = px1 + t_param * dx
                            proj_y = py1 + t_param * dy
                            segment_dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
                            if segment_dist < min_curve_dist:
                                min_curve_dist = segment_dist
                    
                    # 如果点到曲线的最短距离小于阈值，选中整条曲线
                    if min_curve_dist < canvas_threshold_curve * 1.5:  # 曲线选择阈值稍大一些
                        if min_curve_dist < min_dist:
                            min_dist = min_curve_dist
                            selected_id = obj_id
        
        # 更新选择
        if selected_id:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                # Shift+点击：多选
                if selected_id in self.selected_objects:
                    self.selected_objects.remove(selected_id)
                    # 如果是曲线，也移除相关的曲线段
                    if self.graphics_system.objects[selected_id]['type'] == 'curve':
                        self._remove_related_curves(selected_id)
                else:
                    self.selected_objects.append(selected_id)
                    # 如果是曲线，也选中相关的曲线段
                    if self.graphics_system.objects[selected_id]['type'] == 'curve':
                        self._add_related_curves(selected_id)
            else:
                # 单选
                self.selected_objects = [selected_id]
                # 如果是曲线，也选中相关的曲线段
                if self.graphics_system.objects[selected_id]['type'] == 'curve':
                    self._add_related_curves(selected_id)
        else:
            # 点击空白处，取消选择
            if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                self.selected_objects = []
    
    def select_all_objects(self):
        """全选所有对象"""
        self.selected_objects = list(self.graphics_system.objects.keys())
    
    def _add_related_curves(self, curve_id):
        """添加与指定曲线相关的所有曲线段（通过控制点重叠判断）"""
        if curve_id not in self.graphics_system.objects:
            return
        
        curve_obj = self.graphics_system.objects[curve_id]
        if curve_obj['type'] != 'curve':
            return
        
        curve_control_points = curve_obj['data']['control_points']
        if len(curve_control_points) < 2:
            return
        
        # 获取第一条和最后一条控制点，用于匹配
        first_point = curve_control_points[0]
        last_point = curve_control_points[-1]
        
        # 查找所有相关的曲线段
        for obj_id, obj in self.graphics_system.objects.items():
            if obj_id == curve_id or obj_id in self.selected_objects:
                continue
            
            if obj['type'] == 'curve':
                other_control_points = obj['data']['control_points']
                if len(other_control_points) < 2:
                    continue
                
                other_first = other_control_points[0]
                other_last = other_control_points[-1]
                
                # 检查控制点是否重叠或接近（阈值5像素）
                threshold = 5.0
                def points_close(p1, p2):
                    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5 < threshold
                
                # 如果两条曲线的端点重叠或接近，认为是相关的
                if (points_close(first_point, other_first) or 
                    points_close(first_point, other_last) or
                    points_close(last_point, other_first) or
                    points_close(last_point, other_last)):
                    if obj_id not in self.selected_objects:
                        self.selected_objects.append(obj_id)
                        # 递归查找更多相关的曲线段
                        self._add_related_curves(obj_id)
    
    def _remove_related_curves(self, curve_id):
        """移除与指定曲线相关的所有曲线段"""
        if curve_id not in self.graphics_system.objects:
            return
        
        curve_obj = self.graphics_system.objects[curve_id]
        if curve_obj['type'] != 'curve':
            return
        
        curve_control_points = curve_obj['data']['control_points']
        if len(curve_control_points) < 2:
            return
        
        # 获取第一条和最后一条控制点，用于匹配
        first_point = curve_control_points[0]
        last_point = curve_control_points[-1]
        
        # 查找所有相关的曲线段并移除
        to_remove = []
        for obj_id in self.selected_objects:
            if obj_id == curve_id:
                continue
            
            if obj_id in self.graphics_system.objects:
                obj = self.graphics_system.objects[obj_id]
                if obj['type'] == 'curve':
                    other_control_points = obj['data']['control_points']
                    if len(other_control_points) < 2:
                        continue
                    
                    other_first = other_control_points[0]
                    other_last = other_control_points[-1]
                    
                    # 检查控制点是否重叠或接近（阈值5像素）
                    threshold = 5.0
                    def points_close(p1, p2):
                        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5 < threshold
                    
                    # 如果两条曲线的端点重叠或接近，认为是相关的
                    if (points_close(first_point, other_first) or 
                        points_close(first_point, other_last) or
                        points_close(last_point, other_first) or
                        points_close(last_point, other_last)):
                        to_remove.append(obj_id)
        
        # 移除相关的曲线段
        for obj_id in to_remove:
            if obj_id in self.selected_objects:
                self.selected_objects.remove(obj_id)
    
    def apply_transform(self, transform_type, params):
        """应用变换"""
        if len(self.selected_objects) == 0:
            return
        
        # 计算变换中心（所有选中对象的中心）
        if 'center_x' not in params or 'center_y' not in params:
            center_x, center_y = self._calculate_selection_center()
            params['center_x'] = center_x
            params['center_y'] = center_y
        
        from command_system import TransformCommand
        cmd = TransformCommand({
            'transform_type': transform_type,
            'object_ids': self.selected_objects.copy(),
            'transform_params': params
        })
        self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
    
    def _calculate_selection_center(self):
        """计算选中对象的中心点"""
        if len(self.selected_objects) == 0:
            return 400, 300  # 默认中心
        
        total_x = 0
        total_y = 0
        count = 0
        
        for obj_id in self.selected_objects:
            if obj_id not in self.graphics_system.objects:
                continue
            obj = self.graphics_system.objects[obj_id]
            obj_type = obj['type']
            obj_data = obj['data']
            
            points = self.graphics_system._get_object_points(obj_type, obj_data)
            for x, y in points:
                total_x += x
                total_y += y
                count += 1
        
        if count > 0:
            return total_x / count, total_y / count
        return 400, 300
    
    def start_transform_input(self, transform_type):
        """开始变换输入"""
        self.transform_input_mode = transform_type
        self.input_active = True
        self.input_text = ""
        if transform_type == 'translate':
            self.input_prompt = "输入平移 (tx,ty):"
        elif transform_type == 'rotate':
            self.input_prompt = "输入角度(度):"
        elif transform_type == 'scale':
            self.input_prompt = "输入缩放 (sx,sy):"
    
    def confirm_transform_input(self):
        """确认变换输入"""
        if not self.input_active or len(self.selected_objects) == 0:
            return
        
        try:
            if self.transform_input_mode == 'translate':
                # 解析 "tx,ty" 或 "tx ty"
                parts = self.input_text.replace(',', ' ').split()
                if len(parts) >= 2:
                    tx, ty = float(parts[0]), float(parts[1])
                    self.apply_transform('translate', {'tx': tx, 'ty': ty})
                elif len(parts) == 1:
                    tx = float(parts[0])
                    self.apply_transform('translate', {'tx': tx, 'ty': tx})
            elif self.transform_input_mode == 'rotate':
                # 解析角度（度转弧度）
                angle_deg = float(self.input_text)
                angle_rad = math.radians(angle_deg)
                center_x, center_y = self._calculate_selection_center()
                self.apply_transform('rotate', {
                    'angle': angle_rad,
                    'center_x': center_x,
                    'center_y': center_y
                })
            elif self.transform_input_mode == 'scale':
                # 解析 "sx,sy" 或 "sx sy" 或单个值
                parts = self.input_text.replace(',', ' ').split()
                if len(parts) >= 2:
                    sx, sy = float(parts[0]), float(parts[1])
                elif len(parts) == 1:
                    sx = sy = float(parts[0])
                else:
                    return
                center_x, center_y = self._calculate_selection_center()
                self.apply_transform('scale', {
                    'sx': sx,
                    'sy': sy,
                    'center_x': center_x,
                    'center_y': center_y
                })
        except ValueError:
            pass  # 输入无效，忽略
        
        self.cancel_transform_input()
    
    def cancel_transform_input(self):
        """取消变换输入"""
        self.input_active = False
        self.input_text = ""
        self.transform_input_mode = None
        self.input_prompt = ""
    
    def delete_selected_objects(self):
        """删除选中的对象"""
        if len(self.selected_objects) == 0:
            return
        
        from command_system import DeleteCommand
        cmd = DeleteCommand({
            'object_ids': self.selected_objects.copy()
        })
        self.graphics_system.command_manager.execute_command(cmd, self.graphics_system)
        self.selected_objects = []
    
    def save_file(self):
        """保存文件"""
        try:
            if self.current_file:
                GraphicsFileFormat.save(self.graphics_system, self.current_file)
                self.show_message(f"已保存到: {self.current_file}")
            else:
                # 简化：使用默认文件名
                filename = "graphics_save.json"
                GraphicsFileFormat.save(self.graphics_system, filename)
                self.current_file = filename
                self.show_message(f"已保存到: {filename}")
        except Exception as e:
            self.show_message(f"保存失败: {str(e)}", error=True)
    
    def load_file(self):
        """加载文件"""
        try:
            # 简化：使用默认文件名
            filename = "graphics_save.json"
            if GraphicsFileFormat.load(self.graphics_system, filename):
                self.current_file = filename
                self.show_message(f"已加载: {filename}")
                # 清除选择状态
                self.selected_objects = []
            else:
                self.show_message(f"文件不存在: {filename}", error=True)
        except Exception as e:
            self.show_message(f"加载失败: {str(e)}", error=True)
    
    def draw_toolbar(self):
        """绘制工具栏"""
        # 工具栏背景
        pygame.draw.rect(self.screen, (240, 240, 240), self.toolbar_rect)
        pygame.draw.line(self.screen, (200, 200, 200), 
                        (800, 0), (800, self.height), 2)
        
        # 工具按钮
        y = 20
        for tool_name, tool_label in self.tools.items():
            color = (100, 150, 255) if self.current_tool == tool_name else (200, 200, 200)
            pygame.draw.rect(self.screen, color, (810, y, 180, 30))
            text = self.small_font.render(tool_label, True, (0, 0, 0))
            self.screen.blit(text, (820, y + 5))
            
            y += 35
        
        # 显示变换工具快捷键提示
        hint_height = 0
        if self.current_tool == 'transform':
            y_hint = 20 + len(self.tools) * 35 + 10
            hint_text = self.small_font.render("方向键:平移", True, (100, 100, 100))
            self.screen.blit(hint_text, (810, y_hint))
            hint_text = self.small_font.render("T:平移输入 R:旋转输入", True, (100, 100, 100))
            self.screen.blit(hint_text, (810, y_hint + 18))
            hint_text = self.small_font.render("S:缩放输入 Del:删除", True, (100, 100, 100))
            self.screen.blit(hint_text, (810, y_hint + 36))
            hint_height = 54  # 3行 * 18像素
        elif self.current_tool == 'select':
            y_hint = 20 + len(self.tools) * 35 + 10
            hint_text = self.small_font.render("Shift:多选 Ctrl+A:全选", True, (100, 100, 100))
            self.screen.blit(hint_text, (810, y_hint))
            hint_text = self.small_font.render("Del:删除", True, (100, 100, 100))
            self.screen.blit(hint_text, (810, y_hint + 18))
            hint_height = 36  # 2行 * 18像素
        
        # 颜色选择 - 根据提示信息高度动态调整位置
        y = 20 + len(self.tools) * 35 + 10 + hint_height + 30
        if y < 400:  # 确保最小间距
            y = 400
        text = self.small_font.render("颜色:", True, (0, 0, 0))
        self.screen.blit(text, (810, y - 20))
        for i, color in enumerate(self.colors):
            pygame.draw.rect(self.screen, color, (810 + (i % 4) * 50, y + (i // 4) * 35, 40, 30))
            if color == self.current_color:
                pygame.draw.rect(self.screen, (255, 255, 0), 
                               (810 + (i % 4) * 50, y + (i // 4) * 35, 40, 30), 3)
        
        # 文件操作
        y = 550
        pygame.draw.rect(self.screen, (150, 200, 150), (810, y, 180, 30))
        text = self.small_font.render("保存 (Ctrl+S)", True, (0, 0, 0))
        self.screen.blit(text, (820, y + 5))
        
        y += 40
        pygame.draw.rect(self.screen, (150, 200, 150), (810, y, 180, 30))
        text = self.small_font.render("打开 (Ctrl+O)", True, (0, 0, 0))
        self.screen.blit(text, (820, y + 5))
        
        y += 40
        pygame.draw.rect(self.screen, (200, 150, 150), (810, y, 180, 30))
        text = self.small_font.render("清空", True, (0, 0, 0))
        self.screen.blit(text, (820, y + 5))
        
        # 命令系统图形界面
        y = 680
        # 撤销按钮
        undo_color = (150, 200, 150) if self.graphics_system.command_manager.can_undo() else (200, 200, 200)
        pygame.draw.rect(self.screen, undo_color, (810, y, 85, 25))
        text = self.small_font.render("撤销", True, (0, 0, 0))
        self.screen.blit(text, (820, y + 3))
        
        # 重做按钮
        redo_color = (150, 200, 150) if self.graphics_system.command_manager.can_redo() else (200, 200, 200)
        pygame.draw.rect(self.screen, redo_color, (905, y, 85, 25))
        text = self.small_font.render("重做", True, (0, 0, 0))
        self.screen.blit(text, (915, y + 3))
        
        # 命令历史显示
        y = 710
        undo_count = len(self.graphics_system.command_manager.undo_stack)
        redo_count = len(self.graphics_system.command_manager.redo_stack)
        hint = f"历史: {undo_count}  可重做: {redo_count}"
        text = self.small_font.render(hint, True, (100, 100, 100))
        self.screen.blit(text, (810, y))
        
        # 文本输入对话框
        if self.text_input_mode:
            self.draw_text_input_dialog()
        
        # 变换输入对话框
        if self.input_active:
            self.draw_input_dialog()
    
    def draw_message(self):
        """绘制消息提示"""
        if not self.message:
            return
        
        # 消息框位置（在工具栏顶部）
        message_rect = pygame.Rect(810, 10, 180, 40)
        color = (255, 100, 100) if getattr(self, 'message_error', False) else (100, 255, 100)
        pygame.draw.rect(self.screen, color, message_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), message_rect, 2)
        
        # 消息文本（自动换行）
        words = self.message.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_surface = self.small_font.render(test_line, True, (0, 0, 0))
            if text_surface.get_width() <= message_rect.width - 10:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # 显示消息（最多2行）
        for i, line in enumerate(lines[:2]):
            text_surface = self.small_font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (message_rect.x + 5, message_rect.y + 5 + i * 18))
    
    def draw_text_input_dialog(self):
        """绘制文本输入对话框"""
        if not self.text_input_pos:
            return
        
        # 转换文本位置到屏幕坐标
        screen_x, screen_y = self.canvas_to_screen(self.text_input_pos[0], self.text_input_pos[1])
        
        # 对话框背景（在文本位置附近）
        dialog_rect = pygame.Rect(screen_x - 100, screen_y - 50, 400, 100)
        # 确保对话框不超出屏幕
        if dialog_rect.x < 0:
            dialog_rect.x = 10
        if dialog_rect.y < 0:
            dialog_rect.y = 10
        if dialog_rect.right > self.width - 200:
            dialog_rect.x = self.width - 200 - dialog_rect.width
        if dialog_rect.bottom > self.height:
            dialog_rect.y = self.height - dialog_rect.height
        
        pygame.draw.rect(self.screen, (255, 255, 255), dialog_rect)
        pygame.draw.rect(self.screen, (0, 0, 255), dialog_rect, 3)
        
        # 提示文本
        prompt_text = self.font.render("输入文本:", True, (0, 0, 0))
        self.screen.blit(prompt_text, (dialog_rect.x + 10, dialog_rect.y + 10))
        
        # 输入框
        input_rect = pygame.Rect(dialog_rect.x + 10, dialog_rect.y + 40, dialog_rect.width - 20, 30)
        pygame.draw.rect(self.screen, (240, 240, 240), input_rect)
        pygame.draw.rect(self.screen, (0, 0, 255), input_rect, 2)
        
        # 输入文本
        input_display = self.input_text + "|"  # 显示光标
        input_surface = self.font.render(input_display, True, (0, 0, 0))
        self.screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
        
        # 提示
        hint_text = self.small_font.render("Enter确认, Esc取消", True, (100, 100, 100))
        self.screen.blit(hint_text, (dialog_rect.x + 10, dialog_rect.y + 75))
    
    def draw_input_dialog(self):
        """绘制输入对话框"""
        # 对话框背景
        dialog_rect = pygame.Rect(200, 250, 400, 150)
        pygame.draw.rect(self.screen, (255, 255, 255), dialog_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 3)
        
        # 提示文本
        prompt_text = self.font.render(self.input_prompt, True, (0, 0, 0))
        self.screen.blit(prompt_text, (220, 270))
        
        # 输入框
        input_rect = pygame.Rect(220, 300, 360, 30)
        pygame.draw.rect(self.screen, (240, 240, 240), input_rect)
        pygame.draw.rect(self.screen, (0, 0, 255), input_rect, 2)
        
        # 输入文本
        input_display = self.input_text + "|"  # 显示光标
        input_surface = self.font.render(input_display, True, (0, 0, 0))
        self.screen.blit(input_surface, (230, 305))
        
        # 提示
        hint_text = self.small_font.render("Enter确认, Esc取消", True, (100, 100, 100))
        self.screen.blit(hint_text, (220, 340))
    
    def _get_zoom_offset(self):
        """计算缩放后的偏移量（统一计算，确保一致性，保持宽高比）"""
        if abs(self.zoom_factor - 1.0) > 0.01:
            canvas = self.graphics_system.get_canvas()
            canvas_width = canvas.get_width()
            canvas_height = canvas.get_height()
            
            # 计算理想的缩放尺寸（不限制，允许超出屏幕）
            ideal_scaled_width = canvas_width * self.zoom_factor
            ideal_scaled_height = canvas_height * self.zoom_factor
            
            # 限制缩放后的尺寸不超过屏幕（仅用于显示，不影响缩放因子）
            max_width = self.width - 200
            max_height = self.height
            
            # 计算两个方向的最大允许缩放因子（保持宽高比，仅用于限制显示）
            max_zoom_x = max_width / canvas_width
            max_zoom_y = max_height / canvas_height
            # 计算显示时的有效缩放因子（如果超出屏幕，则限制显示尺寸）
            display_zoom = min(self.zoom_factor, max_zoom_x, max_zoom_y)
            
            # 但实际的有效缩放因子就是用户设置的缩放因子（不限制）
            self.effective_zoom_factor = self.zoom_factor
            
            # 使用显示缩放因子计算显示尺寸（保持宽高比）
            scaled_width = int(canvas_width * display_zoom)
            scaled_height = int(canvas_height * display_zoom)
            
            # 计算偏移（以缩放中心为基准，使用实际缩放因子）
            offset_x = int(self.zoom_center[0] * (1 - self.zoom_factor))
            offset_y = int(self.zoom_center[1] * (1 - self.zoom_factor))
            # 确保画布不会超出边界（但允许负偏移，表示画布超出屏幕）
            offset_x = min(offset_x, max_width - scaled_width)
            offset_y = min(offset_y, max_height - scaled_height)
            # 允许负偏移，但限制在合理范围内
            offset_x = max(-scaled_width + 100, min(offset_x, max_width - 100))
            offset_y = max(-scaled_height + 100, min(offset_y, max_height - 100))
            return offset_x, offset_y, scaled_width, scaled_height
        else:
            self.effective_zoom_factor = 1.0
            return 0, 0, self.graphics_system.canvas_width, self.graphics_system.canvas_height
    
    def screen_to_canvas(self, screen_x, screen_y):
        """将屏幕坐标转换为画布坐标（考虑缩放）"""
        if abs(self.zoom_factor - 1.0) > 0.01:
            offset_x, offset_y, _, _ = self._get_zoom_offset()
            # 使用有效缩放因子进行坐标转换
            effective_zoom = getattr(self, 'effective_zoom_factor', self.zoom_factor)
            # 转换坐标：从屏幕坐标减去偏移，再除以有效缩放因子
            canvas_x = (screen_x - offset_x) / effective_zoom
            canvas_y = (screen_y - offset_y) / effective_zoom
            return int(canvas_x), int(canvas_y)
        else:
            return screen_x, screen_y
    
    def canvas_to_screen(self, canvas_x, canvas_y):
        """将画布坐标转换为屏幕坐标（考虑缩放）"""
        if abs(self.zoom_factor - 1.0) > 0.01:
            offset_x, offset_y, _, _ = self._get_zoom_offset()
            # 使用有效缩放因子进行坐标转换
            effective_zoom = getattr(self, 'effective_zoom_factor', self.zoom_factor)
            # 转换坐标：先乘以有效缩放因子，再加上偏移
            screen_x = canvas_x * effective_zoom + offset_x
            screen_y = canvas_y * effective_zoom + offset_y
            return int(screen_x), int(screen_y)
        else:
            return canvas_x, canvas_y
    
    def draw_selection_marks(self):
        """绘制选中对象的标记"""
        for obj_id in self.selected_objects:
            if obj_id not in self.graphics_system.objects:
                continue
            
            obj = self.graphics_system.objects[obj_id]
            obj_type = obj['type']
            obj_data = obj['data']
            
            # 绘制选择框（需要转换坐标，使用有效缩放因子）
            effective_zoom = getattr(self, 'effective_zoom_factor', self.zoom_factor if abs(self.zoom_factor - 1.0) > 0.01 else 1.0)
            
            if obj_type == 'point':
                x, y = obj_data['x'], obj_data['y']
                screen_x, screen_y = self.canvas_to_screen(x, y)
                size = max(1, int(5 * effective_zoom))
                pygame.draw.rect(self.screen, (0, 255, 0), 
                               (screen_x - size, screen_y - size, size * 2, size * 2), 2)
            elif obj_type == 'line':
                x1, y1 = obj_data['x1'], obj_data['y1']
                x2, y2 = obj_data['x2'], obj_data['y2']
                # 转换到屏幕坐标
                screen_x1, screen_y1 = self.canvas_to_screen(x1, y1)
                screen_x2, screen_y2 = self.canvas_to_screen(x2, y2)
                size = max(1, int(5 * effective_zoom))
                # 绘制端点标记
                pygame.draw.circle(self.screen, (0, 255, 0), (screen_x1, screen_y1), size, 2)
                pygame.draw.circle(self.screen, (0, 255, 0), (screen_x2, screen_y2), size, 2)
            elif obj_type == 'circle':
                cx, cy = obj_data['cx'], obj_data['cy']
                radius = obj_data['radius']
                # 转换到屏幕坐标
                screen_cx, screen_cy = self.canvas_to_screen(cx, cy)
                screen_radius = int(radius * effective_zoom)
                size = max(1, int(5 * effective_zoom))
                # 绘制边界框
                pygame.draw.circle(self.screen, (0, 255, 0), 
                                 (screen_cx, screen_cy), screen_radius, 2)
                pygame.draw.circle(self.screen, (0, 255, 0), 
                                 (screen_cx, screen_cy), size, 2)  # 中心点标记
            elif obj_type == 'curve':
                control_points = obj_data['control_points']
                size = max(1, int(4 * effective_zoom))
                # 绘制控制点
                for px, py in control_points:
                    screen_px, screen_py = self.canvas_to_screen(px, py)
                    pygame.draw.circle(self.screen, (0, 255, 0), 
                                     (screen_px, screen_py), size, 1)
            elif obj_type == 'text':
                x, y = obj_data['x'], obj_data['y']
                screen_x, screen_y = self.canvas_to_screen(x, y)
                pygame.draw.rect(self.screen, (0, 255, 0), 
                               (screen_x - 5, screen_y - 5, 100, 30), 2)
    
    def draw_preview(self):
        """绘制预览（绘制过程中的临时图形）"""
        if not self.drawing or not self.start_pos or not self.current_pos:
            return
        
        canvas_x, canvas_y = self.current_pos
        
        if self.current_tool == 'line':
            # 转换到屏幕坐标
            screen_start = self.canvas_to_screen(self.start_pos[0], self.start_pos[1])
            screen_end = self.canvas_to_screen(canvas_x, canvas_y)
            pygame.draw.line(self.screen, self.current_color,
                           screen_start, screen_end, 1)
        
        elif self.current_tool == 'circle':
            radius = int(math.sqrt(
                (canvas_x - self.start_pos[0]) ** 2 +
                (canvas_y - self.start_pos[1]) ** 2
            ))
            # 转换到屏幕坐标，使用有效缩放因子
            screen_center = self.canvas_to_screen(self.start_pos[0], self.start_pos[1])
            effective_zoom = getattr(self, 'effective_zoom_factor', self.zoom_factor if abs(self.zoom_factor - 1.0) > 0.01 else 1.0)
            screen_radius = int(radius * effective_zoom)
            pygame.draw.circle(self.screen, self.current_color,
                             screen_center, screen_radius, 1)
        
        elif self.current_tool == 'curve':
            # 绘制曲线预览
            if len(self.curve_points) >= 2:
                # 绘制点之间的连线作为预览（需要转换坐标）
                for i in range(len(self.curve_points) - 1):
                    screen_p1 = self.canvas_to_screen(self.curve_points[i][0], self.curve_points[i][1])
                    screen_p2 = self.canvas_to_screen(self.curve_points[i + 1][0], self.curve_points[i + 1][1])
                    pygame.draw.line(self.screen, self.current_color,
                                   screen_p1, screen_p2, 1)
        
        elif self.current_tool == 'clip':
            # 绘制裁剪窗口预览
            x_min = min(self.start_pos[0], canvas_x)
            y_min = min(self.start_pos[1], canvas_y)
            x_max = max(self.start_pos[0], canvas_x)
            y_max = max(self.start_pos[1], canvas_y)
            # 转换到屏幕坐标
            screen_x1, screen_y1 = self.canvas_to_screen(x_min, y_min)
            screen_x2, screen_y2 = self.canvas_to_screen(x_max, y_max)
            pygame.draw.rect(self.screen, (255, 0, 0),
                           (screen_x1, screen_y1, screen_x2 - screen_x1, screen_y2 - screen_y1), 2)
        
        elif self.current_tool == 'zoom':
            # 显示缩放比例
            if len(self.selected_objects) > 0:
                # 如果有选中的对象，显示对象缩放比例
                object_zoom = getattr(self, 'object_zoom_factor', 1.0)
                zoom_text = f"对象缩放: {object_zoom:.2f}x ({len(self.selected_objects)}个对象)"
            else:
                # 否则显示画布视图缩放比例
                zoom_text = f"视图缩放: {self.zoom_factor:.2f}x"
            text_surface = self.small_font.render(zoom_text, True, (0, 0, 0))
            # 绘制半透明背景
            bg_rect = pygame.Rect(5, 5, text_surface.get_width() + 10, text_surface.get_height() + 10)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(200)
            bg_surface.fill((255, 255, 255))
            self.screen.blit(bg_surface, bg_rect)
            self.screen.blit(text_surface, (10, 10))
    
    def show_message(self, text, error=False):
        """显示消息提示"""
        self.message = text
        self.message_timer = 180  # 3秒（60fps * 3）
        self.message_error = error
    
    def run(self):
        """运行主循环"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            
            # 绘制
            self.screen.fill((255, 255, 255))
            
            # 绘制画布（应用缩放）
            canvas = self.graphics_system.get_canvas()
            if abs(self.zoom_factor - 1.0) > 0.01:
                # 需要缩放，使用统一的偏移计算
                offset_x, offset_y, scaled_width, scaled_height = self._get_zoom_offset()
                scaled_canvas = pygame.transform.scale(canvas, (scaled_width, scaled_height))
                self.screen.blit(scaled_canvas, (offset_x, offset_y))
            else:
                # 不需要缩放，直接绘制
                self.screen.blit(canvas, (0, 0))
            
            # 绘制选中对象的标记
            self.draw_selection_marks()
            
            # 绘制预览
            self.draw_preview()
            
            # 绘制工具栏
            self.draw_toolbar()
            
            # 更新消息计时器
            if self.message_timer > 0:
                self.message_timer -= 1
                if self.message_timer <= 0:
                    self.message = ""
            
            # 绘制消息提示
            if self.message:
                self.draw_message()
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    editor = GraphicsEditor()
    editor.run()

