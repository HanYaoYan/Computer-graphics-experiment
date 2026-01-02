"""
图形文件格式模块
实现图形的保存和打开功能
"""
import json
import os
from command_system import Command, CommandType


class GraphicsFileFormat:
    """图形文件格式处理类"""
    
    @staticmethod
    def save(graphics_system, filepath):
        """保存图形到文件
        filepath: 文件路径
        """
        data = {
            'version': '1.0',
            'canvas_size': {
                'width': graphics_system.canvas_width,
                'height': graphics_system.canvas_height
            },
            'objects': [],
            'commands': []
        }
        
        # 保存所有图形对象
        for obj_id, obj_data in graphics_system.objects.items():
            obj_info = {
                'id': obj_id,
                'type': obj_data['type'],
                'data': obj_data['data']
            }
            data['objects'].append(obj_info)
        
        # 保存命令历史（用于撤销/重做）
        try:
            for cmd in graphics_system.command_manager.undo_stack:
                cmd_dict = cmd.to_dict()
                if cmd_dict:
                    data['commands'].append(cmd_dict)
        except Exception as e:
            # 如果命令序列化失败，只保存对象数据
            print(f"警告: 命令历史保存失败: {e}")
        
        # 写入JSON文件
        try:
            # 确保目录存在
            import os
            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"文件写入失败: {str(e)}")
        
        return True
    
    @staticmethod
    def load(graphics_system, filepath):
        """从文件加载图形
        filepath: 文件路径
        """
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 清空当前图形
        graphics_system.clear_all()
        
        # 恢复画布大小（如果需要）
        if 'canvas_size' in data:
            canvas_size = data['canvas_size']
            # 注意：这里可能需要重新创建画布，实际实现中可能需要调整
        
        # 加载对象
        if 'objects' in data:
            for obj_info in data['objects']:
                obj_type = obj_info['type']
                obj_data = obj_info['data']
                
                if obj_type == 'point':
                    graphics_system.add_point(
                        obj_data['x'], obj_data['y'],
                        tuple(obj_data['color']), obj_data.get('size', 1)
                    )
                elif obj_type == 'line':
                    graphics_system.add_line(
                        obj_data['x1'], obj_data['y1'],
                        obj_data['x2'], obj_data['y2'],
                        tuple(obj_data['color'])
                    )
                elif obj_type == 'circle':
                    graphics_system.add_circle(
                        obj_data['cx'], obj_data['cy'],
                        obj_data['radius'],
                        tuple(obj_data['color'])
                    )
                elif obj_type == 'curve':
                    graphics_system.add_curve(
                        obj_data['control_points'],
                        tuple(obj_data['color'])
                    )
                elif obj_type == 'text':
                    graphics_system.add_text(
                        obj_data['text'],
                        obj_data['x'], obj_data['y'],
                        tuple(obj_data['color']),
                        obj_data.get('font_size', 24)
                    )
        
        # 恢复命令历史（可选）
        if 'commands' in data:
            graphics_system.command_manager.undo_stack = []
            for cmd_dict in data['commands']:
                cmd = Command.from_dict(cmd_dict)
                if cmd:
                    graphics_system.command_manager.undo_stack.append(cmd)
        
        return True

