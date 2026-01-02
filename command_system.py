"""
命令指令系统模块
设计命令来完成各种图形操作
"""
from enum import Enum


class CommandType(Enum):
    """命令类型枚举"""
    DRAW_POINT = "draw_point"
    DRAW_LINE = "draw_line"
    DRAW_CIRCLE = "draw_circle"
    DRAW_CURVE = "draw_curve"
    DRAW_TEXT = "draw_text"
    CLIP = "clip"
    TRANSFORM = "transform"
    FILL = "fill"
    DELETE = "delete"
    CLEAR = "clear"


class Command:
    """命令基类"""
    def __init__(self, command_type, params):
        self.command_type = command_type
        self.params = params
        self.executed = False
    
    def execute(self, graphics_system):
        """执行命令"""
        raise NotImplementedError
    
    def undo(self, graphics_system):
        """撤销命令"""
        raise NotImplementedError
    
    def to_dict(self):
        """转换为字典，用于序列化"""
        return {
            'type': self.command_type.value,
            'params': self.params
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建命令"""
        cmd_type = CommandType(data['type'])
        params = data['params']
        
        if cmd_type == CommandType.DRAW_POINT:
            return DrawPointCommand(params)
        elif cmd_type == CommandType.DRAW_LINE:
            return DrawLineCommand(params)
        elif cmd_type == CommandType.DRAW_CIRCLE:
            return DrawCircleCommand(params)
        elif cmd_type == CommandType.DRAW_CURVE:
            return DrawCurveCommand(params)
        elif cmd_type == CommandType.DRAW_TEXT:
            return DrawTextCommand(params)
        elif cmd_type == CommandType.CLIP:
            return ClipCommand(params)
        elif cmd_type == CommandType.TRANSFORM:
            return TransformCommand(params)
        elif cmd_type == CommandType.FILL:
            return FillCommand(params)
        elif cmd_type == CommandType.DELETE:
            return DeleteCommand(params)
        elif cmd_type == CommandType.CLEAR:
            return ClearCommand(params)
        return None


class DrawPointCommand(Command):
    """绘制点命令"""
    def __init__(self, params):
        super().__init__(CommandType.DRAW_POINT, params)
        self.object_id = None
    
    def execute(self, graphics_system):
        x, y, color, size = self.params['x'], self.params['y'], \
                           self.params.get('color', (0, 0, 0)), \
                           self.params.get('size', 1)
        self.object_id = graphics_system.add_point(x, y, color, size)
        self.executed = True
        return self.object_id
    
    def undo(self, graphics_system):
        if self.object_id:
            graphics_system.remove_object(self.object_id)


class DrawLineCommand(Command):
    """绘制直线命令"""
    def __init__(self, params):
        super().__init__(CommandType.DRAW_LINE, params)
        self.object_id = None
    
    def execute(self, graphics_system):
        x1, y1, x2, y2, color = self.params['x1'], self.params['y1'], \
                               self.params['x2'], self.params['y2'], \
                               self.params.get('color', (0, 0, 0))
        self.object_id = graphics_system.add_line(x1, y1, x2, y2, color)
        self.executed = True
        return self.object_id
    
    def undo(self, graphics_system):
        if self.object_id:
            graphics_system.remove_object(self.object_id)


class DrawCircleCommand(Command):
    """绘制圆命令"""
    def __init__(self, params):
        super().__init__(CommandType.DRAW_CIRCLE, params)
        self.object_id = None
    
    def execute(self, graphics_system):
        cx, cy, radius, color = self.params['cx'], self.params['cy'], \
                                self.params['radius'], \
                                self.params.get('color', (0, 0, 0))
        self.object_id = graphics_system.add_circle(cx, cy, radius, color)
        self.executed = True
        return self.object_id
    
    def undo(self, graphics_system):
        if self.object_id:
            graphics_system.remove_object(self.object_id)


class DrawCurveCommand(Command):
    """绘制曲线命令"""
    def __init__(self, params):
        super().__init__(CommandType.DRAW_CURVE, params)
        self.object_id = None
    
    def execute(self, graphics_system):
        control_points = self.params['control_points']
        color = self.params.get('color', (0, 0, 0))
        self.object_id = graphics_system.add_curve(control_points, color)
        self.executed = True
        return self.object_id
    
    def undo(self, graphics_system):
        if self.object_id:
            graphics_system.remove_object(self.object_id)


class DrawTextCommand(Command):
    """绘制文本命令"""
    def __init__(self, params):
        super().__init__(CommandType.DRAW_TEXT, params)
        self.object_id = None
    
    def execute(self, graphics_system):
        text, x, y, color, font_size = self.params['text'], \
                                       self.params['x'], self.params['y'], \
                                       self.params.get('color', (0, 0, 0)), \
                                       self.params.get('font_size', 24)
        self.object_id = graphics_system.add_text(text, x, y, color, font_size)
        self.executed = True
        return self.object_id
    
    def undo(self, graphics_system):
        if self.object_id:
            graphics_system.remove_object(self.object_id)


class ClipCommand(Command):
    """裁剪命令"""
    def __init__(self, params):
        super().__init__(CommandType.CLIP, params)
        self.clipped_objects = []
    
    def execute(self, graphics_system):
        x_min, y_min, x_max, y_max = self.params['x_min'], self.params['y_min'], \
                                     self.params['x_max'], self.params['y_max']
        object_ids = self.params.get('object_ids', None)
        self.clipped_objects = graphics_system.clip_objects(x_min, y_min, x_max, y_max, object_ids)
        self.executed = True
        return self.clipped_objects
    
    def undo(self, graphics_system):
        # 裁剪操作的撤销需要恢复原始对象
        graphics_system.restore_clipped_objects(self.clipped_objects)


class TransformCommand(Command):
    """变换命令"""
    def __init__(self, params):
        super().__init__(CommandType.TRANSFORM, params)
        self.original_states = []
    
    def execute(self, graphics_system):
        transform_type = self.params['transform_type']
        object_ids = self.params['object_ids']
        transform_params = self.params['transform_params']
        
        # 保存原始状态
        self.original_states = graphics_system.save_object_states(object_ids)
        
        # 执行变换
        graphics_system.transform_objects(object_ids, transform_type, transform_params)
        self.executed = True
    
    def undo(self, graphics_system):
        # 恢复原始状态
        graphics_system.restore_object_states(self.original_states)


class FillCommand(Command):
    """填充命令"""
    def __init__(self, params):
        super().__init__(CommandType.FILL, params)
        self.fill_id = None
    
    def execute(self, graphics_system):
        fill_type = self.params['fill_type']
        if fill_type == 'seed':
            x, y, color = self.params['x'], self.params['y'], self.params['color']
            self.fill_id = graphics_system.seed_fill(x, y, color)
        elif fill_type == 'scanline':
            vertices = self.params['vertices']
            color = self.params['color']
            self.fill_id = graphics_system.scanline_fill(vertices, color)
        self.executed = True
        return self.fill_id
    
    def undo(self, graphics_system):
        if self.fill_id:
            graphics_system.remove_object(self.fill_id)


class DeleteCommand(Command):
    """删除命令"""
    def __init__(self, params):
        super().__init__(CommandType.DELETE, params)
        self.deleted_objects = []
    
    def execute(self, graphics_system):
        object_ids = self.params['object_ids']
        self.deleted_objects = graphics_system.remove_objects(object_ids)
        self.executed = True
        return self.deleted_objects
    
    def undo(self, graphics_system):
        graphics_system.restore_objects(self.deleted_objects)


class ClearCommand(Command):
    """清空命令"""
    def __init__(self, params):
        super().__init__(CommandType.CLEAR, params)
        self.cleared_objects = []
    
    def execute(self, graphics_system):
        self.cleared_objects = graphics_system.clear_all()
        self.executed = True
        return self.cleared_objects
    
    def undo(self, graphics_system):
        graphics_system.restore_objects(self.cleared_objects)


class CommandManager:
    """命令管理器，支持撤销/重做"""
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []
        self.max_stack_size = 100
    
    def execute_command(self, command, graphics_system):
        """执行命令"""
        command.execute(graphics_system)
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()  # 清空重做栈
    
    def undo(self, graphics_system):
        """撤销"""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo(graphics_system)
            self.redo_stack.append(command)
    
    def redo(self, graphics_system):
        """重做"""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute(graphics_system)
            self.undo_stack.append(command)
    
    def can_undo(self):
        """是否可以撤销"""
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """是否可以重做"""
        return len(self.redo_stack) > 0

