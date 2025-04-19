import bpy
import time


from .utils import *

classes = []
def register_class(cls):
    classes.append(cls)
    return cls

@register_class
class ExecuteReplayOperator(bpy.types.Operator):
    bl_idname = "object.execute_replay"
    bl_label = "Execute Replay"

    def execute(self, context):
        filePath = context.scene.replay_file_path
        if not filePath:
            self.report({'WARNING'}, "No file path provided.")
            return {'CANCELLED'}

        context.scene.console_output.clear()
        console_output = []
        input_events = readEvents(filePath, console_output, filter_specific=False, device_type=context.scene.input_device)

        for msg in console_output:
            self.report({'INFO'}, msg)

        context.scene.input_events.clear()
        for event in input_events:
            event_property = context.scene.input_events.add()
            event_property.Name = event.Name
            event_property.Time = event.Time
            event_property.Pressed = event.Pressed
            event_property.Duration = event.Duration

        return {'FINISHED'}


handler_CB3E6 = []

modal_operator = None
_event = None
_i = 0
start_time = None

# Operator to update the progress and redraw
@register_class
class DrawTriangleOperator(bpy.types.Operator):
    """Draw and Update Triangle Progress"""
    bl_idname = "view3d.draw_triangle_progress"
    bl_label = "Draw Triangle Progress"
    bl_options = {'REGISTER'}

    _handle = None
    
    @classmethod
    def poll(cls, context):
        # Disable the operator if it is already running
        return not context.scene.is_input_running
    
    def invoke(self, context, event):
        global start_time
        global filled_shape_pad

        addon_prefs = get_addon_preferences()

        bpy.context.scene.accelerate_keyboard = addon_prefs.Accelerate_color_keyboard_default
        bpy.context.scene.brake_keyboard = addon_prefs.Brake_color_keyboard_default
        bpy.context.scene.right_keyboard = addon_prefs.Right_color_keyboard_default
        bpy.context.scene.left_keyboard = addon_prefs.Left_color_keyboard_default


        bpy.context.scene.accelerate_pad = addon_prefs.Accelerate_color_pad_default
        bpy.context.scene.brake_pad = addon_prefs.Brake_color_pad_default

        filled_shape_pad = [(0.0, 0.0), (0.0, 0.0 ), (0.0, 0.0), (0.0, 0.0)]
        
        
        
        start_time = time.time()
        if is_debug_mode():
            print("Invoke called!")
            print("start_time = ", start_time )


        self.execute(context)

        return {'RUNNING_MODAL'}
    def modal(self, context, event):
        global _i
        
        global _event
        input_events = [scene_event for scene_event in context.scene.input_events]
        
        
        if event.type == 'ESC':  # Exit on ESC
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':  # Update progress periodically
            if is_debug_mode():
                print('I before = ', _i)

            if input_events[_i] == input_events[-1]:
                self.cancel(context)
                return {'CANCELLED'}

             
            _event = input_events[_i]

            if is_debug_mode():
                print('_event =', _event.Name)
                print('I after = ', _i)

            if context.area is not None:
                if is_debug_mode():
                    print("Tagging redraw.")
                context.area.tag_redraw()
            else:
                self.cancel(context)
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        global _event
        global modal_operator
        global start_time 
        modal_operator = self

        print("Executing operator.")
        context.scene.is_input_running = True

        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "Must run in the 3D Viewport")
            return {'CANCELLED'}

        # Add a timer for periodic updates
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.03, window=context.window) # 0.03 is perfect 

        
        device_type = context.scene.input_device
        if device_type == "KEYBOARD":
            print('Device = ', device_type)
            # Add the draw handler
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_shapes_keyboard, (_event, start_time), 'WINDOW', 'POST_PIXEL'
            )
        else:
            print('Device = ', device_type)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_shapes_pad, (_event, start_time), 'WINDOW', 'POST_PIXEL'
            )

        return {'RUNNING_MODAL'}
    def stop(self):
        """Stop the modal operator externally."""
        self._is_running = False
        context.scene.is_input_running = False

    def cancel(self, context):
        global _i
        _i = 0

        print("Cancelling operator.")
        if self._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.window_manager.event_timer_remove(self._timer)
            self._handle = None
        global modal_operator
        modal_operator = None
        context.scene.is_input_running = False
        context.area.tag_redraw()



def draw_shapes_keyboard(dummy, dummy2):
    global _i
    global _event
    global start_time
    
    addon_prefs = get_addon_preferences()

    Accelerate_color_keyboard_default = addon_prefs.Accelerate_color_keyboard_default
    Accelerate_color_keyboard_filled = addon_prefs.Accelerate_color_keyboard_filled
    Brake_color_keyboard_default = addon_prefs.Brake_color_keyboard_default
    Brake_color_keyboard_filled = addon_prefs.Brake_color_keyboard_filled
    Right_color_keyboard_default = addon_prefs.Right_color_keyboard_default
    Right_color_keyboard_filled = addon_prefs.Right_color_keyboard_filled
    Left_color_keyboard_default = addon_prefs.Left_color_keyboard_default
    Left_color_keyboard_filled = addon_prefs.Left_color_keyboard_filled


    x_offset = addon_prefs.x_offset
    y_offset = addon_prefs.y_offset
    
    if is_debug_mode():
        print('Drawing KEYBOARD')
    current_time = time.time() - start_time

    # Definitions for the Keyboard
    # quads = [
    #     [(705.0 + x_offset, 290.0 + y_offset), (755.0 + x_offset, 290.0 + y_offset), (705.0 + x_offset, 240.0 + y_offset), (755.0 + x_offset, 240.0 + y_offset)],  # Accelerate
    #     [(705.0 + x_offset, 235.0 + y_offset), (755.0 + x_offset, 235.0 + y_offset), (705.0 + x_offset, 185.0 + y_offset), (755.0 + x_offset, 185.0 + y_offset)],  # Brake
    #     [(650.0 + x_offset, 235.0 + y_offset), (700.0 + x_offset, 235.0 + y_offset), (650.0 + x_offset, 185.0 + y_offset), (700.0 + x_offset, 185.0 + y_offset)],  # SteerLeft
    #     [(760.0 + x_offset, 235.0 + y_offset), (810.0 + x_offset, 235.0 + y_offset), (760.0 + x_offset, 185.0 + y_offset), (810.0 + x_offset, 185.0 + y_offset)]   # SteerRight
    # ]

    scale_factor = bpy.context.scene.scale_factor 
    center_x, center_y = 730.0, 235.0  # center of scaling

    quads = [
    [
        ((705.0 - center_x) * scale_factor + center_x + x_offset, (290.0 - center_y) * scale_factor + center_y + y_offset),
        ((755.0 - center_x) * scale_factor + center_x + x_offset, (290.0 - center_y) * scale_factor + center_y + y_offset),
        ((705.0 - center_x) * scale_factor + center_x + x_offset, (240.0 - center_y) * scale_factor + center_y + y_offset),
        ((755.0 - center_x) * scale_factor + center_x + x_offset, (240.0 - center_y) * scale_factor + center_y + y_offset),
    ],  # Accelerate
    [
        ((705.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
        ((755.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
        ((705.0 - center_x) * scale_factor + center_x + x_offset, (185.0 - center_y) * scale_factor + center_y + y_offset),
        ((755.0 - center_x) * scale_factor + center_x + x_offset, (185.0 - center_y) * scale_factor + center_y + y_offset),
    ],  # Brake
    [
        ((650.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
        ((700.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
        ((650.0 - center_x) * scale_factor + center_x + x_offset, (185.0 - center_y) * scale_factor + center_y + y_offset),
        ((700.0 - center_x) * scale_factor + center_x + x_offset, (185.0 - center_y) * scale_factor + center_y + y_offset),
    ],  # SteerLeft
    [
        ((760.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
        ((810.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
        ((760.0 - center_x) * scale_factor + center_x + x_offset, (185.0 - center_y) * scale_factor + center_y + y_offset),
        ((810.0 - center_x) * scale_factor + center_x + x_offset, (185.0 - center_y) * scale_factor + center_y + y_offset),
    ],  # SteerRight
    ]


    events_order = ['Accelerate', 'Brake', 'SteerLeft', 'SteerRight']

    # Combine shapes (triangles for PAD and quads for both devices)
    shapes = quads

    draw_shape(shapes[0], [(0, 1, 2), (2, 1, 3)], bpy.context.scene.accelerate_keyboard)
    draw_shape(shapes[1], [(0, 1, 2), (2, 1, 3)], bpy.context.scene.brake_keyboard)
    draw_shape(shapes[2], [(0, 1, 2), (2, 1, 3)], bpy.context.scene.left_keyboard)
    draw_shape(shapes[3], [(0, 1, 2), (2, 1, 3)], bpy.context.scene.right_keyboard)

    event = _event
    
    event_time_seconds = event.Time / 1000.0
   
    
    elapsed_time = current_time - event_time_seconds
    if is_debug_mode():
        print("event.Time = ", event.Time)
        print("event_time_seconds = ", event_time_seconds)
        print("_event.duration / 1000 = ", _event.Duration / 1000)
        print("current_time = ", current_time)
        print("elapsed_time = ", elapsed_time)

    if elapsed_time < 0.0:
        return 0
    else:
        _i += 1


    for shape, event_name in zip(shapes, events_order):
        if is_debug_mode():
            print('event.Name ', event.Name)
            print('event_name ', event_name)
        if event.Name == 'SteerRight': 
            if event.Pressed > 0:
                bpy.context.scene.right_keyboard  = Right_color_keyboard_filled
            else:
                bpy.context.scene.right_keyboard  = Right_color_keyboard_default
        elif event.Name == 'SteerLeft':
            if event.Pressed > 0:
                bpy.context.scene.left_keyboard  = Left_color_keyboard_filled
            else:
                bpy.context.scene.left_keyboard  = Left_color_keyboard_default
 
        elif event.Name == 'Accelerate': 
            if event.Pressed > 0:
                bpy.context.scene.accelerate_keyboard  = Accelerate_color_keyboard_filled
            else:
                bpy.context.scene.accelerate_keyboard  = Accelerate_color_keyboard_default
        elif event.Name == 'Brake':
            if event.Pressed > 0:
                bpy.context.scene.brake_keyboard  = Brake_color_keyboard_filled 
            else:
                bpy.context.scene.brake_keyboard  = Brake_color_keyboard_default



def draw_shapes_pad(dummy, dummy2):
    global _i
    global _event
    global start_time
    global Accelerate_color_pad
    global Brake_color_pad

    global filled_shape_pad

    if is_debug_mode():
        print('Drawing PAD')

    addon_prefs = get_addon_preferences()

    Accelerate_color_pad_default = addon_prefs.Accelerate_color_pad_default
    Accelerate_color_pad_filled = addon_prefs.Accelerate_color_pad_filled
    Brake_color_pad_default = addon_prefs.Brake_color_pad_default
    Brake_color_pad_filled = addon_prefs.Brake_color_pad_filled
    default_color = addon_prefs.default_color_pad
    filled_color = addon_prefs.filled_color_pad

    x_offset = addon_prefs.x_offset
    y_offset = addon_prefs.y_offset

    # triangles = [
    #     [(580.0 + x_offset, 240.0 + y_offset), (700.0 + x_offset, 300.0 + y_offset), (700.0 + x_offset, 175.5 + y_offset)],  # SteerLeft
    #     [(880.0 + x_offset, 240.0 + y_offset), (760.0 + x_offset, 300.0 + y_offset), (760.0 + x_offset, 175.0 + y_offset)]   # SteerRight
    # ]
    # quads = [
    #     [(705.0 + x_offset, 300.0 + y_offset), (755.0 + x_offset, 300.0 + y_offset), (705.0 + x_offset, 240.0 + y_offset), (755.0 + x_offset, 240.0 + y_offset)],  # Accelerate
    #     [(705.0 + x_offset, 235.0 + y_offset), (755.0 + x_offset, 235.0 + y_offset), (705.0 + x_offset, 175.0 + y_offset), (755.0 + x_offset, 175.0 + y_offset)]   # Brake
    # ]

    scale_factor = bpy.context.scene.scale_factor 
    center_x, center_y = 730.0, 235.0  # center of scaling

    triangles = [
        [
            ((580.0 - center_x) * scale_factor + center_x + x_offset, (240.0 - center_y) * scale_factor + center_y + y_offset),
            ((700.0 - center_x) * scale_factor + center_x + x_offset, (300.0 - center_y) * scale_factor + center_y + y_offset),
            ((700.0 - center_x) * scale_factor + center_x + x_offset, (175.5 - center_y) * scale_factor + center_y + y_offset),
        ],  # SteerLeft
        [
            ((880.0 - center_x) * scale_factor + center_x + x_offset, (240.0 - center_y) * scale_factor + center_y + y_offset),
            ((760.0 - center_x) * scale_factor + center_x + x_offset, (300.0 - center_y) * scale_factor + center_y + y_offset),
            ((760.0 - center_x) * scale_factor + center_x + x_offset, (175.0 - center_y) * scale_factor + center_y + y_offset),
        ],  # SteerRight
    ]

    quads = [
        [
            ((705.0 - center_x) * scale_factor + center_x + x_offset, (300.0 - center_y) * scale_factor + center_y + y_offset),
            ((755.0 - center_x) * scale_factor + center_x + x_offset, (300.0 - center_y) * scale_factor + center_y + y_offset),
            ((705.0 - center_x) * scale_factor + center_x + x_offset, (240.0 - center_y) * scale_factor + center_y + y_offset),
            ((755.0 - center_x) * scale_factor + center_x + x_offset, (240.0 - center_y) * scale_factor + center_y + y_offset),
        ],  # Accelerate
        [
            ((705.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
            ((755.0 - center_x) * scale_factor + center_x + x_offset, (235.0 - center_y) * scale_factor + center_y + y_offset),
            ((705.0 - center_x) * scale_factor + center_x + x_offset, (175.0 - center_y) * scale_factor + center_y + y_offset),
            ((755.0 - center_x) * scale_factor + center_x + x_offset, (175.0 - center_y) * scale_factor + center_y + y_offset),
        ],  # Brake
    ]

    shapes_pad = triangles + quads

    current_time = time.time() - start_time

    events_order = ['SteerLeft', 'SteerRight', 'Accelerate', 'Brake']
    for shape in shapes_pad:
        color = default_color
        if len(shape) == 3:  # Triangle pour Pad
            draw_shape(shape, [(0, 1, 2)], color)
            # center = (
            # sum(v[0] for v in shape) / 3,
            # sum(v[1] for v in shape) / 3,
            # )
            # print(center)
    
    draw_shape(shapes_pad[2], [(0, 1, 2), (2, 1, 3)], bpy.context.scene.accelerate_pad)
    draw_shape(shapes_pad[3], [(0, 1, 2), (2, 1, 3)], bpy.context.scene.brake_pad)

    draw_shape(filled_shape_pad, [(0, 1, 2), (0, 2, 3)], filled_color)

    if bpy.context.scene.enable_percentage:
        if bpy.context.scene.left_percentage > 0:
            text_offset = calculate_text_offset(bpy.context.scene.left_percentage)
            left_text_pos = ((670 - text_offset - center_x)*scale_factor + center_x + x_offset, (230 - center_y)*scale_factor + center_y + y_offset)
            draw_text(left_text_pos, str(bpy.context.scene.left_percentage) + "%", size=20*scale_factor, color=bpy.context.scene.percentage_color)     

        if bpy.context.scene.right_percentage > 0:
            right_text_pos = ((770 - center_x)*scale_factor + center_x + x_offset, (230 - center_y)*scale_factor + center_y + y_offset)
            draw_text(right_text_pos, str(bpy.context.scene.right_percentage) + "%", size=20*scale_factor, color=bpy.context.scene.percentage_color)

    event = _event 
    event_time_seconds = event.Time / 1000.0
    elapsed_time = current_time - event_time_seconds
    if is_debug_mode():
        print("event.Time = ", event.Time)
        print("event_time_seconds = ", event_time_seconds)
        print("_event.duration / 1000 = ", _event.Duration / 1000)
        print("current_time = ", current_time)
        print("elapsed_time = ", elapsed_time)
        print("event_time_seconds + (context.scene.input_events[_i].Duration / 1000) = ", event_time_seconds + (bpy.context.scene.input_events[_i].Duration / 1000))


    for shape, event_name in zip(shapes_pad, events_order):
        
        if is_debug_mode():
            print('event.Name = ', event.Name, "event.Pressed = ", event.Pressed)  

        if event.Name == 'Steer' and event.Pressed <= 0 :
            bpy.context.scene.right_percentage = 0
            if event_name == 'SteerLeft':
                progress = - event.Pressed
                if is_debug_mode():
                    print('progress ', progress)
                # Calculate the bottom vertices for the trapezoid (as progress increases)
                bottom_left = (
                    shape[0][0] * (progress) + shape[1][0] * (1.0 - progress),
                    shape[0][1] * (progress) + shape[1][1] * (1.0 - progress)
                )
                bottom_right = (
                    shape[0][0] * (progress) + shape[2][0] * (1.0 - progress),
                    shape[0][1] * (progress) + shape[2][1] * (1.0 - progress)
                )

                # Define the filled trapezoid vertices
                filled_vertices = [
                    shape[1],  # Top (fixed)
                    shape[2],  # Bottom right (fixed)
                    bottom_right,          # Bottom right (varies with progress)
                    bottom_left            # Bottom left (varies with progress)
                ]

                filled_shape_pad = filled_vertices

                #draw_shape(filled_shape_pad, [(0, 1, 2), (0, 2, 3)], filled_color)

                bpy.context.scene.left_percentage = round(progress * 100)


        elif event.Name == 'Steer' and event.Pressed >= 0:
            bpy.context.scene.left_percentage = 0
            if event_name == 'SteerRight':
                progress = event.Pressed
                if is_debug_mode():
                    print('progress ', progress)

                # Calculate the bottom vertices for the trapezoid (as progress increases)
                bottom_left = (
                    shape[0][0] * (progress) + shape[1][0] * (1.0 - progress),
                    shape[0][1] * (progress) + shape[1][1] * (1.0 - progress)
                )
                bottom_right = (
                    shape[0][0] * (progress) + shape[2][0] * (1.0 - progress),
                    shape[0][1] * (progress) + shape[2][1] * (1.0 - progress)
                )

                # Define the filled trapezoid vertices
                filled_vertices = [
                    shape[1],  # Top (fixed)
                    shape[2],  # Bottom right (fixed)
                    bottom_right,          # Bottom right (varies with progress)
                    bottom_left            # Bottom left (varies with progress)
                ]


                filled_shape_pad = filled_vertices
                #draw_shape(filled_shape_pad, [(0, 1, 2), (0, 2, 3)], filled_color)
                
                bpy.context.scene.right_percentage = round(progress * 100)

        elif event.Name == 'Accelerate': 
            if event.Pressed > 0:
                bpy.context.scene.accelerate_pad = Accelerate_color_pad_filled
            else:
                bpy.context.scene.accelerate_pad = Accelerate_color_pad_default
        elif event.Name == 'Brake':
            if event.Pressed > 0:
                bpy.context.scene.brake_pad = Brake_color_pad_filled
            else:
                bpy.context.scene.brake_pad = Brake_color_pad_default
                
    if current_time > event_time_seconds + (bpy.context.scene.input_events[_i].Duration / 1000):
        _i += 1
    else:
        return 0


@register_class
class InputEventProperty(bpy.types.PropertyGroup):
    Name: bpy.props.StringProperty()
    Time: bpy.props.IntProperty()
    Pressed: bpy.props.FloatProperty()
    Duration: bpy.props.IntProperty()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.replay_file_path = bpy.props.StringProperty(name="File Path", subtype='FILE_PATH')
    bpy.types.Scene.input_device = bpy.props.EnumProperty(
        name="Input Device",
        description="Select the input device",
        items=[
            ('KEYBOARD', "Keyboard", "Use keyboard controls"),
            ('PAD', "Pad", "Use pad controls"),
        ],
        default='KEYBOARD',
    )
    bpy.types.Scene.console_output = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.Scene.input_events = bpy.props.CollectionProperty(type=InputEventProperty)

    bpy.types.Scene.is_input_running = bpy.props.BoolProperty(
    name="Is Input Running",
    description="Tracks if the Start Input operator is running",
    default=False
)

    # Color Holders 
    bpy.types.Scene.accelerate_keyboard = bpy.props.FloatVectorProperty(
        name="Accelerate Keyboard",
        description="Color for accelerate (keyboard)",
        default=(0.0235, 0.7882, 0.4588, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    bpy.types.Scene.brake_keyboard = bpy.props.FloatVectorProperty(
        name="Brake Keyboard",
        description="Color for brake (keyboard)",
        default=(0.9333, 0.0, 0.0, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    bpy.types.Scene.right_keyboard = bpy.props.FloatVectorProperty(
        name="Right Keyboard",
        description="Color for right (keyboard)",
        default=(0.9569, 0.5176, 0.1961, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    bpy.types.Scene.left_keyboard = bpy.props.FloatVectorProperty(
        name="Left Keyboard",
        description="Color for left (keyboard)",
        default=(0.905, 0.231, 0.032, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    bpy.types.Scene.accelerate_pad = bpy.props.FloatVectorProperty(
        name="Accelerate Pad",
        description="Color for accelerate (pad)",
        default=(0.0235, 0.7882, 0.4588, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    bpy.types.Scene.brake_pad = bpy.props.FloatVectorProperty(
        name="Brake Pad",
        description="Color for brake (pad)",
        default=(0.855, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # Scale
    bpy.types.Scene.scale_factor = bpy.props.FloatProperty(
        name="Scale Factor",
        description="Scale the size of the shapes",
        default=1.0,
        min=0.1,
        max=5.0
    )

    # percentage
    bpy.types.Scene.percentage_color = bpy.props.FloatVectorProperty(
        name="Percentage Color",
        description="Color for percentages (pad)",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    bpy.types.Scene.enable_percentage = bpy.props.BoolProperty(
    name="Enable Percentage",
    description="Enable Percentage for Pad Input",
    default=True
    )

    bpy.types.Scene.left_percentage = bpy.props.IntProperty(
    name="Left Percentage",
    description="Left Percentage",
    default=0,
    min=0,
    max=100
    )

    bpy.types.Scene.right_percentage = bpy.props.IntProperty(
    name="Right Percentage",
    description="Right Percentage",
    default=0,
    min=0,
    max=100
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.replay_file_path
    del bpy.types.Scene.input_device
    del bpy.types.Scene.console_output
    del bpy.types.Scene.input_events
    del bpy.types.Scene.is_input_running 

    # color holders
    del bpy.types.Scene.accelerate_keyboard
    del bpy.types.Scene.brake_keyboard
    del bpy.types.Scene.right_keyboard
    del bpy.types.Scene.left_keyboard
    del bpy.types.Scene.accelerate_pad
    del bpy.types.Scene.brake_pad

    # scale
    del bpy.types.Scene.scale_factor
    # percentage
    del bpy.types.Scene.enable_percentage
    del bpy.types.Scene.percentage_color
    del bpy.types.Scene.left_percentage
    del bpy.types.Scene.right_percentage