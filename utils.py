import bpy
import os
import gpu
import gpu_extras
import blf
import time

from gpu_extras.batch import batch_for_shader

from pygbx import Gbx, GbxType

def get_addon_preferences():
    if bpy.app.version >= (4, 2, 0):
        return bpy.context.preferences.addons["bl_ext.user_default.gbxreplayreader"].preferences
    else:
        return bpy.context.preferences.addons["gbx_replay_reader"].preferences

def is_debug_mode():
    return get_addon_preferences().debug

    

def calculate_steer(name, value, flags):
	if name != "Steer":
		return bool(value)
	
	if flags == 1 and value == 0: # Full left
		value = -65536
	elif flags == 255: # Right
		value = (value - 65536) * -1
	elif flags == 0: # Left
		value = value * -1

	return(value)/65536


class InputData:
    def __init__(self, name=None, time=None, pressed=None, duration=None):
        self.Name = name
        self.Time = time  # en millisecondes
        self.Pressed = pressed
        self.Duration = duration

def readEvents(filePath, console_output, filter_specific=False, device_type='KEYBOARD'):
    if not os.path.exists(filePath):
        console_output.append(f"File ({filePath}) not found.")
        return []

    try:
        fileGbx = Gbx(filePath)
        ghost = fileGbx.get_class_by_id(GbxType.CTN_GHOST)
        if not ghost:
            console_output.append("Not a Replay.Gbx file.")
            return []

        input_events = []
        detected_device_type = "KEYBOARD"  # Default to keyboard
        
        if ghost.control_entries:

            # Check all entries to determine the device type globally
            for entry in ghost.control_entries:
                if abs(entry.enabled) > 1:  # Continuous values indicate PAD
                    detected_device_type = "PAD"
                    break  # No need to check further


            entries = ghost.control_entries
            for i, entry in enumerate(entries):
                # Determine the duration as the time until the next event
                if i < len(entries) - 1:
                    duration = entries[i + 1].time - entry.time
                else:
                    duration = 0  # Last entry has no next event, duration is 0

                inputData = InputData(
                    name=entry.event_name,
                    pressed=(
                        calculate_steer(entry.event_name, entry.enabled, entry.flags)
                        if detected_device_type == 'PAD'
                        else float(entry.enabled)
                    ),
                    time=entry.time,
                    duration=duration
                )

                input_events.append(inputData)


                if not filter_specific:
                    console_output.append(f"{i} Input Event: {inputData.Name} | Time: {inputData.Time} | Pressed: {inputData.Pressed} | Duration: {inputData.Duration}")
                elif inputData.Pressed and inputData.Name in ['SteerRight', 'SteerLeft', 'Brake', 'Accelerate']:
                    console_output.append(f"{inputData.Name}")

            bpy.context.scene.input_device = detected_device_type

        else:
            console_output.append("No inputs found.")

        return input_events

    except Exception as e:
        console_output.append(f"Error processing file: {e}")
        return []


def draw_shape(vertices, indices, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    # Importation correcte depuis gpu_extras
    from gpu_extras.batch import batch_for_shader 
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)

def draw_text(position, text, size, color=(1.0, 1.0, 1.0, 1.0)):
    """Draw text at a specific position."""
    font_id = 0  # Default font
    blf.position(font_id, position[0], position[1], 0)
    blf.size(font_id, size)
    blf.color(font_id, *color)
    blf.draw(font_id, text)

def calculate_text_offset(percentage):
    """Calculate offset based on the number of digits in the percentage."""
    num_digits = len(str(percentage))
    return num_digits * 12

def start_input_timer():
    return time.time()


def force_redraw():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    return 0.01

