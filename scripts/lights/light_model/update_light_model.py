from yaml_tools import read_yaml, write_yaml, write_yaml_ordered
from homeassistant_access import reload_homeassistant_config


class Light:
    def __init__(
        self,
        name,
        friendly_name=None,
        dashboard_name=None,
        zigbee_address=None,
        icon=None,
        groups=None,
    ):
        self.name = name
        self.friendly_name = friendly_name
        self.dashboard_name = dashboard_name
        self.zigbee_address = zigbee_address
        self.icon = icon
        self.groups = groups if groups else []

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, friendly_name={self.friendly_name}, zigbee_address={self.zigbee_address}, icon={self.icon}, groups={self.groups})"

    def domain_name(self):
        return f"light.{self.name}"

    def to_customize_dict(self):
        customize_dict = {"friendly_name": self.friendly_name}
        if self.icon:
            customize_dict["icon"] = self.icon
        return customize_dict

    def to_dashboard_dict(self):
        return {
            "type": "custom:slider-entity-row",
            "entity": self.domain_name(),
            "name": self.dashboard_name,
            "toggle": True,
            "hide_when_off": True,
        }


class Group:
    def __init__(self, id, name, lights=None):
        self.id = id
        self.name = name
        self.lights = lights if lights else []

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, lights={self.lights})"

    def to_group_dict(self):
        return {
            "name": self.name,
            "icon": "mdi:lightbulb-group-outline",
            "entities": self.lights,
        }

    def to_light_group_dict(self):
        return {"platform": "group", "name": self.name, "entities": self.lights}


class Room:
    def __init__(self, name, friendly_name, lights=None, groups=None):
        self.name = name
        self.friendly_name = friendly_name
        self.lights = lights if lights else []
        self.groups = groups if groups else []

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, friendly_name={self.friendly_name}, lights={self.lights})"


def update_dashboard(overview_dashboard, room, light):
    room_dashboard = [
        view
        for view in overview_dashboard["views"]
        if view.get("title") == room.friendly_name
    ][0]
    light_control_card = [
        card for card in room_dashboard["cards"] if card.get("title") == "Light Control"
    ][0]
    manual_light_control_card = [
        card
        for card in light_control_card["cards"]
        if card.get("head") and card.get("head").get("label") == "Manual"
    ][0]
    dashboard_entry = [
        light_entry
        for light_entry in manual_light_control_card["entities"]
        if light_entry.get("entity") == light.domain_name()
    ]
    if not dashboard_entry:
        manual_light_control_card["entities"].append(light.to_dashboard_dict())


def update_customize_configuration(customize_configuration, light):
    customize_configuration[f"light.{light.name}"] = light.to_customize_dict()


def update_zigbee_configuration(zigbee2mqtt_configuration, light):
    if (
        light.zigbee_address
        and light.zigbee_address in zigbee2mqtt_configuration["devices"]
    ):
        zigbee_light_config = zigbee2mqtt_configuration["devices"][light.zigbee_address]
        zigbee_light_config["friendly_name"] = light.friendly_name


def update_room_scenes(room_scenes, light):
    if room_scenes:
        for scene in room_scenes:
            if light.domain_name() not in scene["entities"]:
                scene["entities"][light.domain_name()] = {"state": "off"}


def create_all_lights_group_for_room(room):
    all_lights_in_room = [f"light.{light.name}" for light in room.lights]
    return Group(
        id=f"all_{room.name}_lights",
        name=f"All {room.friendly_name} Lights",
        lights=all_lights_in_room,
    )


def write_light_groups_to_yaml(room, groups):
    group_list = []
    for group in groups:
        group_list.append(group.to_light_group_dict())
    write_yaml(f"{room.name}/lights.yaml", group_list)


def write_groups_to_yaml(room, groups):
    groups_dict = {}
    for group in groups:
        groups_dict[group.id] = group.to_group_dict()
    write_yaml(f"groups/{room.name}_light_groups.yaml", groups_dict)


def collect_all_light_groups_from_room(room):
    groups = []
    groups.append(create_all_lights_group_for_room(room))
    for group in room.groups:
        lights_in_group = [
            light.domain_name() for light in room.lights if group in light.groups
        ]
        if len(lights_in_group) > 0:
            group_id = room.name + "_" + group.lower().replace(" ", "_")
            groups.append(
                Group(
                    id=group_id,
                    name=f"{room.friendly_name} {group}",
                    lights=lights_in_group,
                )
            )
    return groups


def collect_lights_in_room(room_details):
    lights = []
    for light_name in room_details["lights"].keys():
        light_details = room_details["lights"][light_name]
        dashboard_name = (
            light_details["dashboard_name"]
            if "dashboard_name" in light_details
            else light_details["friendly_name"]
        )
        light_friendly_name = (
            room_details["friendly_name"] + " " + light_details["friendly_name"]
        )
        icon = light_details["icon"] if "icon" in light_details else None
        light_zigbee_address = (
            light_details["zigbee_address"]
            if "zigbee_address" in light_details
            else None
        )
        groups_of_light = light_details["groups"] if "groups" in light_details else None
        light = Light(
            name=light_name,
            friendly_name=light_friendly_name,
            dashboard_name=dashboard_name,
            zigbee_address=light_zigbee_address,
            icon=icon,
            groups=groups_of_light,
        )
        lights.append(light)
    return lights


def get_rooms_from_model():
    rooms = []
    for room_entry in read_yaml("lights.yaml")["rooms"]:
        for room_name, room_details in room_entry.items():
            groups_of_room = (
                room_details["groups"] if "groups" in room_details else None
            )
            room = Room(
                name=room_name,
                friendly_name=room_details["friendly_name"],
                lights=collect_lights_in_room(room_details),
                groups=groups_of_room,
            )
            rooms.append(room)
    return rooms


def main():
    zigbee2mqtt_configuration = read_yaml("zigbee2mqtt/configuration.yaml")
    customize_configuration = read_yaml("customize.yaml")
    overview_dashboard = read_yaml("dashboards/overview.yaml")

    for room in get_rooms_from_model():
        print(f"Updating light model for {room}")
        groups = collect_all_light_groups_from_room(room)
        write_groups_to_yaml(room, groups)
        write_light_groups_to_yaml(room, groups)

        room_scenes = read_yaml(f"{room.name}/scenes.yaml")
        for light in room.lights:
            update_room_scenes(room_scenes, light)
            update_zigbee_configuration(zigbee2mqtt_configuration, light)
            update_customize_configuration(customize_configuration, light)
            update_dashboard(overview_dashboard, room, light)

        write_yaml(f"{room.name}/scenes.yaml", room_scenes)

    write_yaml("zigbee2mqtt/configuration.yaml", zigbee2mqtt_configuration)
    write_yaml("dashboards/overview.yaml", overview_dashboard)
    write_yaml_ordered("customize.yaml", customize_configuration)

    reload_homeassistant_config()


if __name__ == "__main__":
    main()
