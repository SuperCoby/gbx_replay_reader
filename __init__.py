bl_info = {
    "author": "SuperCoby",
    "name": "GBX Replay Reader v1.0.0",
    "blender": (3, 0, 0),
    "category": "3D View",
}

import bpy
from bpy.types import AddonPreferences

import os
import gpu
import gpu_extras

from gpu_extras.batch import batch_for_shader

from pip._internal import main as install
try:
    import pygbx
except ImportError as e:
    install(["install", "pygbx"])
finally:
    pass


from . import ui
from . import utils
from . import Operators

if 'bpy' in locals():
    print('GBX Reloading')
    from importlib import reload
    import sys
    for k, v in list(sys.modules.items()):
        if 'gbx' in k:
            #print(k)
            reload(v)

classes = []
def register_class(cls):
    classes.append(cls)
    return cls


@register_class
class GBXReplayReaderPreferences(AddonPreferences): 
    bl_idname = __name__

    debug: bpy.props.BoolProperty(
        name="Enable Debug",
        description="Enable debug mode for detailed logging",
        default=False,
    )

    x_offset: bpy.props.IntProperty(
        name="X Offset",
        description="Move the inputs horizontally on the screen",
        default=0,
        min=-1000,
        max=1000
    )

    y_offset: bpy.props.IntProperty(
        name="Y Offset",
        description="Move the inputs vertically on the screen",
        default=0,
        min=-1000,
        max=1000
    )

    # Keyboard Colors
    Accelerate_color_keyboard_default: bpy.props.FloatVectorProperty(
        name="Accelerate Default (Keyboard)",
        description="Default color for accelerate (keyboard)",
        default=(0.0235, 0.7882, 0.4588, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Accelerate_color_keyboard_filled: bpy.props.FloatVectorProperty(
        name="Accelerate Filled (Keyboard)",
        description="Filled color for accelerate (keyboard)",
        default=(0.0, 0.584, 0.178, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Brake_color_keyboard_default: bpy.props.FloatVectorProperty(
        name="Brake Default (Keyboard)",
        description="Default color for brake (keyboard)",
        default=(0.9333, 0.0, 0.0, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Brake_color_keyboard_filled: bpy.props.FloatVectorProperty(
        name="Brake Filled (Keyboard)",
        description="Filled color for brake (keyboard)",
        default=(0.855, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Right_color_keyboard_default: bpy.props.FloatVectorProperty(
        name="Right Default (Keyboard)",
        description="Default color for right (keyboard)",
        default=(0.9569, 0.5176, 0.1961, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Right_color_keyboard_filled: bpy.props.FloatVectorProperty(
        name="Right Filled (Keyboard)",
        description="Filled color for right (keyboard)",
        default=(0.905, 0.231, 0.032, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Left_color_keyboard_default: bpy.props.FloatVectorProperty(
        name="Left Default (Keyboard)",
        description="Default color for left (keyboard)",
        default=(0.9569, 0.5176, 0.1961, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Left_color_keyboard_filled: bpy.props.FloatVectorProperty(
        name="Left Filled (Keyboard)",
        description="Filled color for left (keyboard)",
        default=(0.905, 0.231, 0.032, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # Pad Colors
    Accelerate_color_pad_default: bpy.props.FloatVectorProperty(
        name="Accelerate Default (Pad)",
        description="Default color for accelerate (pad)",
        default=(0.0235, 0.7882, 0.4588, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Accelerate_color_pad_filled: bpy.props.FloatVectorProperty(
        name="Accelerate Filled (Pad)",
        description="Filled color for accelerate (pad)",
        default=(0.0, 0.584, 0.178, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Brake_color_pad_default: bpy.props.FloatVectorProperty(
        name="Brake Default (Pad)",
        description="Default color for brake (pad)",
        default=(0.9333, 0.0, 0.0, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    Brake_color_pad_filled: bpy.props.FloatVectorProperty(
        name="Brake Filled (Pad)",
        description="Filled color for brake (pad)",
        default=(0.855, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    default_color_pad: bpy.props.FloatVectorProperty(
        name="Default Color (Pad)",
        description="Default generic color for pad inputs",
        default=(0.9569, 0.5176, 0.1961, 0.25),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )
    filled_color_pad: bpy.props.FloatVectorProperty(
        name="Filled Color (Pad)",
        description="Filled generic color for pad inputs",
        default=(0.905, 0.231, 0.032, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )



    def draw(self, context: bpy.types.Context):
        layout: UILayout = self.layout
        box = layout.box()

        row = box.row()
        row.label(text="Screen Position Offsets")
        row.prop(self, "x_offset")
        row.prop(self, "y_offset")

        row = box.row()
        row.label(text="Scale")
        row.prop(context.scene, "scale_factor")
        
        box = layout.box()
        box.label(text="Percentages Options:")
        row = box.row(align=False)
        row.label(text="Enable Percentage")
        row.prop(context.scene, "enable_percentage", text="")
        row.prop(context.scene, "percentage_color", text="")
        
        # Keyboard Colors Section
        box = layout.box()

        box.label(text="Keyboard Colors:")
        row = box.row()
        row.prop(self, "Accelerate_color_keyboard_default", text="Accelerate Default")
        row.prop(self, "Accelerate_color_keyboard_filled", text="Filled")

        row = box.row()
        row.prop(self, "Brake_color_keyboard_default", text="Brake Default")
        row.prop(self, "Brake_color_keyboard_filled", text="Filled")

        row = box.row()
        row.prop(self, "Right_color_keyboard_default", text="Right Default")
        row.prop(self, "Right_color_keyboard_filled", text="Filled")

        row = box.row()
        row.prop(self, "Left_color_keyboard_default", text="Left Default")
        row.prop(self, "Left_color_keyboard_filled", text="Filled")

        box = layout.box()
        box.label(text="Pad Colors:")
        row = box.row()
        
        row.prop(self, "Accelerate_color_pad_default", text="Accelerate Default")
        row.prop(self, "Accelerate_color_pad_filled", text="Filled")

        row = box.row()
        row.prop(self, "Brake_color_pad_default", text="Brake Default")
        row.prop(self, "Brake_color_pad_filled", text="Filled")

        row = box.row()
        row.prop(self, "default_color_pad", text="Right And Left Default Color")
        row.prop(self, "filled_color_pad", text="Filled Color")

        layout.separator()
        row2 = box.row()
        row2.prop(self, "debug")
        


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    ui.register()
    Operators.register()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    ui.unregister()
    Operators.unregister()

if __name__ == "__main__":
    register()

