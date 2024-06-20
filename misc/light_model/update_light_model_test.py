import unittest
from unittest.mock import patch, call
import update_light_model


class TestUpdateLightModel(unittest.TestCase):

    @patch("update_light_model.reload_homeassistant_config")
    @patch("update_light_model.write_yaml_ordered")
    @patch("update_light_model.write_yaml")
    @patch("update_light_model.read_yaml")
    def test_update_light_model(
        self,
        read_yaml_mock,
        write_yaml_mock,
        write_yaml_ordered_mock,
        reload_homeassistant_config_mock,
    ):
        file_contents = {
            "lights.yaml": {
                "rooms": [
                    {
                        "bedroom": {
                            "friendly_name": "Bedroom",
                            "lights": {
                                "bedroom_dresser_light": {
                                    "friendly_name": "Dresser Light",
                                    "icon": "mdi:floor-lamp-outline",
                                    "zigbee_address": "0x00178801088baad1",
                                    "groups": ["Indirect"],
                                },
                                "bedroom_ceiling_light": {
                                    "friendly_name": "Ceiling Light",
                                    "icon": "mdi:ceiling-lamp",
                                    "dashboard_name": "Ceiling",
                                },
                                "bedroom_bed_light": {
                                    "friendly_name": "Bed Light",
                                    "zigbee_address": "0x00178801088baad2",
                                    "groups": ["Indirect"],
                                },
                            },
                            "groups": ["Indirect", "Unused"],
                        }
                    }
                ]
            },
            "bedroom/scenes.yaml": [
                {
                    "name": "some_scene",
                    "entities": {
                        "input_boolean": "something_unrelated",
                        "light.bedroom_bed_light": {"some": "light_configuration"},
                    },
                }
            ],
            "dashboards/overview.yaml": {
                "views": [
                    {
                        "title": "Bedroom",
                        "cards": [
                            {
                                "title": "Light Control",
                                "cards": [
                                    {
                                        "head": {"label": "Manual"},
                                        "entities": [
                                            {
                                                "type": "custom:slider-entity-row",
                                                "entity": "light.bedroom_bed_light",
                                                "name": "Bed Light",
                                                "toggle": True,
                                                "hide_when_off": True,
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
            "zigbee2mqtt/configuration.yaml": {
                "homeassistant": "true",
                "mqtt": {"base_topic": "foo"},
                "permit_join": "true",
                "devices": {
                    "0x00178801088baad1": {"friendly_name": "0x00178801088baad1"},
                    "0x00178801088baad2": {"friendly_name": "Bedroom Bed Light"},
                    "0x0017880100112ed7": {
                        "friendly_name": "Living Room Hue Light Bulb"
                    },
                },
            },
            "customize.yaml": {},
        }

        def read_yaml_side_effect(path):
            return file_contents[path]

        read_yaml_mock.side_effect = read_yaml_side_effect

        update_light_model.main()

        write_yaml_mock.assert_has_calls(
            [
                call(
                    "groups/bedroom_light_groups.yaml",
                    {
                        "all_bedroom_lights": {
                            "name": "All Bedroom Lights",
                            "icon": "mdi:lightbulb-group-outline",
                            "entities": [
                                "light.bedroom_dresser_light",
                                "light.bedroom_ceiling_light",
                                "light.bedroom_bed_light",
                            ],
                        },
                        "bedroom_indirect": {
                            "name": "Bedroom Indirect",
                            "icon": "mdi:lightbulb-group-outline",
                            "entities": [
                                "light.bedroom_dresser_light",
                                "light.bedroom_bed_light",
                            ],
                        },
                    },
                ),
                call(
                    "bedroom/lights.yaml",
                    [
                        {
                            "platform": "group",
                            "name": "All Bedroom Lights",
                            "entities": [
                                "light.bedroom_dresser_light",
                                "light.bedroom_ceiling_light",
                                "light.bedroom_bed_light",
                            ],
                        },
                        {
                            "platform": "group",
                            "name": "Bedroom Indirect",
                            "entities": [
                                "light.bedroom_dresser_light",
                                "light.bedroom_bed_light",
                            ],
                        },
                    ],
                ),
                call(
                    "bedroom/scenes.yaml",
                    [
                        {
                            "name": "some_scene",
                            "entities": {
                                "input_boolean": "something_unrelated",
                                "light.bedroom_bed_light": {
                                    "some": "light_configuration"
                                },
                                "light.bedroom_dresser_light": {"state": "off"},
                                "light.bedroom_ceiling_light": {"state": "off"},
                            },
                        }
                    ],
                ),
                call(
                    "zigbee2mqtt/configuration.yaml",
                    {
                        "homeassistant": "true",
                        "mqtt": {"base_topic": "foo"},
                        "permit_join": "true",
                        "devices": {
                            "0x00178801088baad1": {
                                "friendly_name": "Bedroom Dresser Light"
                            },
                            "0x00178801088baad2": {
                                "friendly_name": "Bedroom Bed Light"
                            },
                            "0x0017880100112ed7": {
                                "friendly_name": "Living Room Hue Light Bulb"
                            },
                        },
                    },
                ),
                call(
                    "dashboards/overview.yaml",
                    {
                        "views": [
                            {
                                "title": "Bedroom",
                                "cards": [
                                    {
                                        "title": "Light Control",
                                        "cards": [
                                            {
                                                "head": {"label": "Manual"},
                                                "entities": [
                                                    {
                                                        "type": "custom:slider-entity-row",
                                                        "entity": "light.bedroom_bed_light",
                                                        "name": "Bed Light",
                                                        "toggle": True,
                                                        "hide_when_off": True,
                                                    },
                                                    {
                                                        "type": "custom:slider-entity-row",
                                                        "entity": "light.bedroom_dresser_light",
                                                        "name": "Dresser Light",
                                                        "toggle": True,
                                                        "hide_when_off": True,
                                                    },
                                                    {
                                                        "type": "custom:slider-entity-row",
                                                        "entity": "light.bedroom_ceiling_light",
                                                        "name": "Ceiling",
                                                        "toggle": True,
                                                        "hide_when_off": True,
                                                    },
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                ),
            ]
        )
        write_yaml_ordered_mock.assert_has_calls(
            [
                call(
                    "customize.yaml",
                    {
                        "light.bedroom_dresser_light": {
                            "friendly_name": "Bedroom Dresser Light",
                            "icon": "mdi:floor-lamp-outline",
                        },
                        "light.bedroom_ceiling_light": {
                            "friendly_name": "Bedroom Ceiling Light",
                            "icon": "mdi:ceiling-lamp",
                        },
                        "light.bedroom_bed_light": {
                            "friendly_name": "Bedroom Bed Light"
                        },
                    },
                )
            ]
        )
        reload_homeassistant_config_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
