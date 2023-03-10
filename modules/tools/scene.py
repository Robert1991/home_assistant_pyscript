from tools.entity import call_service_within_entity_domain


def normalize(scene_name_part):
    return scene_name_part.lower().replace(" ", "_")


def create_scene_entity_id(scene_prefix, scene_name_from_input_select):
    normalized_scene_prefix = normalize(scene_prefix)
    normalized_scene_name_from_input_select = normalize(
        scene_name_from_input_select)
    return "scene." + normalized_scene_prefix + "_" + normalized_scene_name_from_input_select


def toggle_selected_scene(scene_input_select, scene_prefix):
    current_scene_name = state.get(scene_input_select)
    scene_entity_id = create_scene_entity_id(scene_prefix, current_scene_name)
    call_service_within_entity_domain(
        scene_entity_id, "turn_on", entity_id=scene_entity_id)
