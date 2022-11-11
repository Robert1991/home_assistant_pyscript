# Home assistant pyscript automations

This repository comprises my homeassistant automations written with pyscript. I use these automations on my own smart home server as well as the one I've running at my parents place.

## Apps

### Activity based entity control

This app can be used to control an entity based on the state of some binary sensor detecting some activity. An example would be turning off the light when no actitvity was detected in a certain room. This app can also be used to toggle scenes based on activity.

Configuration in pyscript_config.yaml

allow_all_imports: true
hass_is_global: true
apps:
  activity_based_entity_control: 
    - [name_of_configuration]:
        entity: [toggled entity in home assistant]
        motion_sensor_entity: [binary sensor in home assistant being observed by the automation]
        automation_enabled_entity: [input boolean in home assistant to switch the automation on/off]
        turn_off_timeout_entity: [input number entity for timeout of switching the entity]
        turn_off_timer_entity: [timer entity which needs to be created for the automation]
        scene_toggle_entity: [input_select showing the currently selected scene for this automation] (optional)
        scene_group_prefix: [prefix for all the scenes belonging to this automation, needed to switch the scene's e.g. scene_toggle_entity shows 'work' and scene_group_prefix shows office, scene name 'scene.office_work' will be generated] (optional)
        time_based_scene_switch: (optional)
          scene_switch_configuration_entity: [input select showing which configurations are available. This input select maps which scene will be toggled at which time. e.g. 'bedroom_night_light_start_time/bedroom_night_light_choosen_scene' would map the input datetime 'bedroom_night_light_start_time' to the scene chosen in input select 'bedroom_night_light_choosen_scene']
          automation_enabled_entity: [input boolean in home assistant to switch the time based setting of the scenes on/off]
      light_intensity_control: (optional)
          threshold_entity: [input number setting the threshold for toggling the entity]
          light_sensor_entity: [sensor displaying the current state of light emission which will be compared with the threshold]
