from tools.scene import toggle_selected_scene


@service
def toggle_scene_from_input_select(scene_input_select, scene_prefix):
    toggle_selected_scene(scene_input_select, scene_prefix)
