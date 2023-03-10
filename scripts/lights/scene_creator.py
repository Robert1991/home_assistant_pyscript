import yaml
import re
from os import path


class LightScene():
    light_intensity = None
    light_intensity_control_entity = None
    scene_name = ""
    light_states = []
    scene_group = ""

    def __init__(self, scene_name, scene_group, light_states, light_intensity_control_entity, scene_light_intensity):
        self.scene_name = scene_name
        self.scene_group = scene_group
        self.light_states = light_states
        self.light_intensity = scene_light_intensity
        self.light_intensity_control_entity = light_intensity_control_entity

    def create_light_scene_input_select_name(self, post_fix):
        return self.normalize(self.scene_group) + "_" + self.normalize(post_fix)

    def get_group_normalized(self):
        return self.normalize(self.scene_group)

    def get_name_normalized(self):
        return self.normalize(self.scene_name)

    def create_light_scene_path(self, homeassistant_conf_dir):
        scene_group_normalized = self.normalize(self.scene_group)
        path_to_scenes_file = path.join(
            homeassistant_conf_dir, scene_group_normalized, "scenes.yaml")
        return path_to_scenes_file

    def to_dict(self):
        dict_values = {"name": self.get_light_scene_name(), "entities": {}}
        for light_state in self.light_states:
            dict_values["entities"].update(light_state.to_dict_value())

        if self.light_intensity_control_entity:
            dict_values["entities"].update(
                {self.light_intensity_control_entity: str(self.light_intensity)})
        return dict_values

    def get_scene_name_normalized(self):
        return self.get_group_normalized() + "_" + self.get_name_normalized()

    def get_light_scene_name(self):
        return self.scene_group + " " + self.scene_name

    def normalize(self, to_be_normalized):
        return to_be_normalized.lower().replace(' ', '_')

    def get_light_intensity(self):
        return self.light_intensity


class LightSceneFactory:
    def create_light_scene(scene_name, scene_group, light_intensity_control, light_states, light_intensity_state):
        parsed_light_states = []
        for light_state in light_states:
            parsed_light_states.append(
                LightState.create_light_state(light_state, light_states[light_state]))
        if light_intensity_control:
            return LightScene(scene_name,
                              scene_group,
                              parsed_light_states,
                              light_intensity_control,
                              light_intensity_state)
        return LightScene(scene_name, scene_group, parsed_light_states, None, None)


class LightState:
    entity_id = ""
    state = ""
    color_states = []
    brightness = None
    color_temp = None

    def create_light_state(light_entity_id, light_state_attributes):
        light_on_off_state = light_state_attributes["state"]
        color_states = LightState.read_color_states(light_state_attributes)
        brightness = None
        color_temp = None
        if "brightness" in light_state_attributes:
            brightness = light_state_attributes["brightness"]
        if "color_temp" in light_state_attributes:
            color_temp = light_state_attributes["color_temp"]
        return LightState(light_entity_id, light_on_off_state, color_states, brightness, color_temp)

    def read_color_states(light_state):
        color_states = []
        if "hs_color" in light_state:
            h_value = light_state["hs_color"][0]
            s_value = light_state["hs_color"][1]
            color_states.append(HSColorState(h_value, s_value))
        if "rgb_color" in light_state:
            r_value = light_state["rgb_color"][0]
            g_value = light_state["rgb_color"][1]
            b_value = light_state["rgb_color"][2]
            color_states.append(RGBColorState(r_value, g_value, b_value))
        if "xy_color" in light_state:
            x_value = light_state["xy_color"][0]
            y_value = light_state["xy_color"][1]
            color_states.append(XYColorState(x_value, y_value))
        return color_states

    def __init__(self, entity_id, state, color_states, brightness, color_temp):
        self.entity_id = entity_id
        self.state = state
        self.brightness = brightness
        self.color_temp = color_temp
        if color_states:
            self.color_states = color_states

    def to_dict_value(self):
        dict_entry = {self.entity_id: {"state": self.state}}
        if self.brightness:
            dict_entry[self.entity_id].update({"brightness": self.brightness})
        if self.color_temp:
            dict_entry[self.entity_id].update({"color_temp": self.color_temp})
        for color in self.color_states:
            dict_entry[self.entity_id].update(color.to_dict_value())
        return dict_entry


class ColorState:
    def __init___(self):
        pass

    def to_dict_value(self):
        pass


class HSColorState:
    h_value = 0
    s_value = 0

    def __init__(self, h_value, s_value):
        self.h_value = h_value
        self.s_value = s_value

    def to_dict_value(self):
        return {"hs_color": [self.h_value, self.s_value]}


class XYColorState(ColorState):
    x_value = 0
    y_value = 0

    def __init__(self, x_value, y_value):
        self.x_value = x_value
        self.y_value = y_value

    def to_dict_value(self):
        return {"xy_color": [self.x_value, self.y_value]}


class RGBColorState(ColorState):
    red = 0
    green = 0
    blue = 0

    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    def to_dict_value(self):
        return {"rgb_color": [self.red, self.green, self.blue]}


def get_generated_input_numbers_path(scene_group_name):
    return path.join(
        "/config/",
        "input/input_number",
        scene_group_name + "_generated.yaml")


@pyscript_compile
def get_scene_group_light_intensity_input_numbers(generated_input_number_file_path):
    if path.isfile(generated_input_number_file_path):
        with open(generated_input_number_file_path) as input_number_file:
            return yaml.full_load(input_number_file)
    return None


def get_scene_input_select_options(light_scene_group, light_scene_array):
    light_scene_group_filter = \
        re.compile(
            re.escape(light_scene_group.replace("_", " ")), re.IGNORECASE)
    light_scene_names = []
    for light_scene in light_scene_array:
        light_scene_name = \
            light_scene_group_filter.sub(
                '', light_scene["name"]).strip(' ')
        light_scene_names.append(light_scene_name)
    light_scene_names.sort()
    return light_scene_names


def create_scene_input_select_dict(input_select_options, input_select_names):
    input_select_dict = {}
    for input_select_name in input_select_names:
        input_select_dict.update(
            {input_select_name: {"options": input_select_options.copy()}})
    return input_select_dict


def get_generated_input_select_path(scene_group_name):
    return path.join(
        "/config/",
        "input/input_select",
        scene_group_name + "_generated.yaml")


@pyscript_compile
def truncate_file(file_path):
    with open(file_path, "a") as file_to_be_truncated:
        file_to_be_truncated.truncate(0)


@pyscript_compile
def write_yaml_dict_to_file(file_path, yaml_dict):
    with open(file_path, 'w') as file:
        yaml.dump(yaml_dict, file)


def regenerate_scene_input_selects(new_light_scene, all_light_scenes, time_based_scene_config=None):
    light_scene_options = get_scene_input_select_options(
        new_light_scene.get_group_normalized(), all_light_scenes)

    input_select_names = [
        new_light_scene.create_light_scene_input_select_name(
            "automatic_light_scene_generated"),
        new_light_scene.create_light_scene_input_select_name(
            "light_scene_generated"),
        new_light_scene.create_light_scene_input_select_name("scene_generator_light_scene_generated")]
    if time_based_scene_config:
        time_based_scene_options = state.getattr(time_based_scene_config)
        for option in time_based_scene_options["options"]:
            option_split = option.split('/')
            if len(option_split) == 2:
                input_select_names.append(option_split[1])

    generated_input_select_file_path = get_generated_input_select_path(
        new_light_scene.get_group_normalized())

    if len(light_scene_options) > 0:
        input_selects = create_scene_input_select_dict(
            light_scene_options, input_select_names)
        write_yaml_dict_to_file(
            generated_input_select_file_path, input_selects)
    else:
        truncate_file(generated_input_select_file_path)

    input_select.reload()


@pyscript_compile
def read_existing_light_scenes(light_scene_file_path):
    with open(light_scene_file_path, "r") as light_scene_file:
        yaml_file = yaml.full_load(light_scene_file)
        if isinstance(yaml_file, type(None)):
            return []
        return yaml_file


def delete_scene_light_intensity_in_input_numbers(light_scene):
    normalized_group_name = light_scene.get_group_normalized()
    generated_input_number_file_path = get_generated_input_numbers_path(
        normalized_group_name)

    generated_input_numbers = get_scene_group_light_intensity_input_numbers(
        generated_input_number_file_path)

    if generated_input_numbers:
        light_scene_input_number_name = light_scene.get_scene_name_normalized() + \
            "_light_intensity"
        if light_scene_input_number_name in generated_input_numbers:
            del generated_input_numbers[light_scene_input_number_name]
            write_yaml_dict_to_file(
                get_generated_input_numbers_path(light_scene.get_group_normalized()), generated_input_numbers)
            input_number.reload()


def create_light_scene_from_current_light_state(scene_name, light_group, scene_group, light_intensity_control):
    log.info("Creating light scene '" + scene_name +
             "' for scene group '" + scene_group + "'")

    light_group_attributes = state.getattr(light_group)
    lights_in_group = light_group_attributes["entity_id"]

    light_states = {}
    for light in lights_in_group:
        light_state_attributes = state.getattr(light)

        light_states[light] = {}
        light_states[light]["state"] = str(state.get(light))
        if "brightness" in light_state_attributes:
            light_states[light]["brightness"] = light_state_attributes["brightness"]
        if "color_temp" in light_state_attributes:
            light_states[light]["color_temp"] = light_state_attributes["color_temp"]
        if "hs_color" in light_state_attributes:
            light_states[light]["hs_color"] = light_state_attributes["hs_color"]
        if "rgb_color" in light_state_attributes:
            light_states[light]["rgb_color"] = light_state_attributes["rgb_color"]
        if "xy_color" in light_state_attributes:
            light_states[light]["xy_color"] = light_state_attributes["xy_color"]
        if "friendly_name" in light_state_attributes:
            light_states[light]["friendly_name"] = light_state_attributes["friendly_name"]

    if light_intensity_control:
        light_intensity_state = int(float(state.get(
            light_intensity_control)))
    else:
        light_intensity_state = None

    return LightSceneFactory.create_light_scene(
        scene_name, scene_group, light_intensity_control, light_states, light_intensity_state)


@service
def create_light_scene(scene_name=None, light_group=None, scene_group=None, time_based_scene_config=None, light_intensity_control=None):
    log.info("Creating light scene '" + scene_name +
             "' for scene group '" + scene_group + "'")
    light_scene = create_light_scene_from_current_light_state(
        scene_name, light_group, scene_group, light_intensity_control)
    light_scene_name = light_scene.get_light_scene_name()
    light_scene_file_path = light_scene.create_light_scene_path("/config/")
    log.info("creating light scene %s in %s" %
             (light_scene_name, light_scene_file_path))
    stored_light_scenes = read_existing_light_scenes(light_scene_file_path)

    for stored_light_scene in stored_light_scenes:
        log.info(stored_light_scene["name"])
        if light_scene.get_light_scene_name() == stored_light_scene["name"]:
            log.error("Unable to create light scene '" + scene_name +
                      "' because scene with same name already exists")
            return

    light_scene_dict = light_scene.to_dict()
    stored_light_scenes.append(light_scene_dict)

    write_yaml_dict_to_file(light_scene_file_path, stored_light_scenes)

    scene.reload()

    regenerate_scene_input_selects(
        light_scene, stored_light_scenes, time_based_scene_config)


@service
def update_light_scene(scene_name=None, light_group=None, scene_group=None, light_intensity_control=None):
    light_scene = create_light_scene_from_current_light_state(
        scene_name, light_group, scene_group, light_intensity_control)

    light_scene_name = light_scene.get_light_scene_name()
    light_scene_file_path = light_scene.create_light_scene_path("/config/")
    log.info("updating light scene %s in %s" %
             (light_scene_name, light_scene_file_path))
    stored_light_scenes = read_existing_light_scenes(light_scene_file_path)

    new_light_scene_array = []
    for stored_light_scene in stored_light_scenes:
        if light_scene_name.lower().replace(' ', '_')  \
                == stored_light_scene["name"].lower().replace(' ', '_'):
            new_light_scene_array.append(light_scene.to_dict())
        else:
            new_light_scene_array.append(stored_light_scene)

    light_scene_file_path = light_scene.create_light_scene_path("/config/")
    write_yaml_dict_to_file(
        light_scene_file_path, new_light_scene_array)

    scene.reload()


@service
def delete_light_scene(scene_name=None, scene_group=None, time_based_scene_config=None):
    light_scene = LightScene(scene_name, scene_group, None, None, None)
    light_scene_file_path = light_scene.create_light_scene_path(
        "/config/")

    light_scene_name = light_scene.get_light_scene_name()
    light_scene_file_path = light_scene.create_light_scene_path("/config/")
    log.info("deleting light scene %s from %s" %
             (light_scene_name, light_scene_file_path))
    stored_light_scenes = read_existing_light_scenes(light_scene_file_path)

    new_light_scene_array = []
    for stored_light_scene in stored_light_scenes:
        if light_scene.get_scene_name_normalized() != stored_light_scene["name"].lower().replace(' ', '_'):
            new_light_scene_array.append(stored_light_scene)

    write_yaml_dict_to_file(light_scene_file_path,
                            new_light_scene_array)
    scene.reload()

    regenerate_scene_input_selects(light_scene, new_light_scene_array,
                                   time_based_scene_config)
    delete_scene_light_intensity_in_input_numbers(light_scene)
