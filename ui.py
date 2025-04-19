import bpy

class ReplayProcessorPanel(bpy.types.Panel):
    bl_label = "Replay Processor"
    bl_idname = "REPLAY_PT_Processor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Replay Processor"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Enter the path to the Replay.Gbx file:")
        box.prop(context.scene, "replay_file_path", text="")

        box = layout.box()       
        box.prop(context.scene, "input_device", text="Device")
        box.operator("object.execute_replay", text="Execute")
        
        box = layout.box()
        box.operator('view3d.draw_triangle_progress', text='Start Input')
        #layout.operator('sna.endop_9a9fd', text='End Input')
        for msg in context.scene.console_output:
            layout.label(text=msg)

def register():
    bpy.utils.register_class(ReplayProcessorPanel)
    

def unregister():
    bpy.utils.unregister_class(ReplayProcessorPanel)
