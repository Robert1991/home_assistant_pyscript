# Home assistant pyscript automations

This repository comprises my homeassistant automations (https://www.home-assistant.io/) written with pyscript (https://hacs-pyscript.readthedocs.io). I use these automations on my own smart home server as well as the one I've running at my parents place.

## Apps

### Activity based entity control

This app can be used to control an entity based on the state of some binary sensor detecting some activity. An example would be turning off the light when no actitvity was detected in a certain room. This app can also be used to toggle scenes based on activity.

#### Configuration in pyscript_config.yaml:

```yaml
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
        skip_turn_on: [if this is true, the entity will only be turned off, e.g. you want to turn off your TV with this automation,but you don't want to have it turned on when activity is detected] (optional, default: false)
        time_based_scene_switch: (optional)
          scene_switch_configuration_entity: [input select showing which configurations are available. This input select maps which scene will be toggled at which time. e.g. 'bedroom_night_light_start_time/bedroom_night_light_choosen_scene' would map the input datetime 'bedroom_night_light_start_time' to the scene chosen in input select 'bedroom_night_light_choosen_scene']
          automation_enabled_entity: [input boolean in home assistant to switch the time based setting of the scenes on/off]
      light_intensity_control: (optional)
          threshold_entity: [input number setting the threshold for toggling the entity]
          light_sensor_entity: [sensor displaying the current state of light emission which will be compared with the threshold]
```

#### Examples:

*Turning off your TV in the living room based on activity detection in the same room:*
```yaml
allow_all_imports: true
hass_is_global: true
apps:
  activity_based_entity_control: 
     - living_room_tv_auto_off:
        entity: media_player.tv_livingroom
        motion_sensor_entity: binary_sensor.living_room_tv_is_playing
        automation_enabled_entity: input_boolean.living_room_turn_off_tv_when_idle_automation_enabled
        turn_off_timeout_entity: input_number.tv_living_room_idle_turn_off_timeout
        turn_off_timer_entity: timer.living_room_tv_auto_off
        skip_turn_on: true
```

**Turning on/off lights in bedroom with different scene's toggled at different times a day:**
```yaml
allow_all_imports: true
hass_is_global: true
apps:
  activity_based_entity_control: 
    - bedroom_light_control:
        entity: light.all_bedroom_lights
        motion_sensor_entity: binary_sensor.bedroom_sensor_motion_detected
        automation_enabled_entity: input_boolean.bedroom_light_automation_is_enabled
        turn_off_timeout_entity: input_number.bedroom_light_turn_off_timeout
        turn_off_timer_entity: timer.bedroom_light_turn_off_timer
        scene_toggle_entity: input_select.bedroom_automatic_light_scene_generated
        scene_group_prefix: bedroom
        time_based_scene_switch:
          scene_switch_configuration_entity: input_select.bedroom_time_based_scenes
          automation_enabled_entity: input_boolean.bedroom_automatic_scene_mode_enabled
        light_intensity_control:
          threshold_entity: input_number.bedroom_light_toogle_intensity_threshold
          light_sensor_entity: sensor.bedroom_sensor_light_intensity
```
with input select entities:

input_select.bedroom_automatic_light_scene:
```yaml
bedroom_automatic_light_scene:
  options:
  - Colorful
  - Night Light
  - Relaxed
  - Work
```

input_select.bedroom_time_based_scenes:
```yaml
bedroom_time_based_scenes:
  options:
    - bedroom_night_light_start_time/bedroom_night_light_choosen_scene
    - bedroom_day_light_start_time/bedroom_day_light_choosen_scene
```

input_select.bedroom_night_light_choosen_scene:
```yaml
bedroom_night_light_choosen_scene:
  options:
  - Colorful
  - Night Light
  - Relaxed
  - Work
```

input_select.bedroom_day_light_choosen_scene:
```yaml
bedroom_day_light_choosen_scene:
  options:
  - Colorful
  - Night Light
  - Relaxed
  - Work
```


### Battery observer

This automation observes different entities displaying the battery state of certain devices. You can define an input number, to determine at which percentage you want a notification sent about low battery state.

#### Configuration in pyscript_config.yaml:

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  battery_observer:
    default_threshold_entity: [input number between 0 and 100 defining the nofitication threshold]
    observed_entities: 
      - entity: [entity displaying battery percentag between 0 and 100]
      - ...
    reminder_timeout: [timeout for resending the notification in minutes]
```

#### Example:

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  battery_observer:
    default_threshold_entity: input_number.default_battery_alert_threshold
    observed_entities: 
      - entity: sensor.bedroom_button_1_battery
      - entity: sensor.bedroom_button_2_battery
    reminder_timeout: 720
```

### Entity Unavailable Notification Service

This app currently logs if an entity gets unavailable. The plan is to have it send push notifcations in the future.

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  entity_unavailable_notification_service:
    - entity: [entity to be observed]
      notify_every: [notification resend timeout in minutes]
      message: [message which will be send with the notification]
    - [...]
```

#### Example

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  entity_unavailable_notification_service:
    - entity: light.bedroom_light
      notify_every: 60
      message: Bedroom Light is unavailable
    - entity: light.kitchen_light
      message: Kitchen Light is unavailable
      notify_every: 60
```

### Home server update

With this app, you can setup pyscript to update your home assistant server, if it is run via docker compose on an ubuntu server using apt. In order to do that, you'll need an binary command line sensor indicating, that updates are available. This binary sensor works by using a sensor, which indicates the update count. This sensor is based on a command line sensor, also implemented within this respository.

If you want to use this automation, you'll first need to define the following two sensors:

**Command line sensor for showing update state:**
```yaml
- platform: command_line
  name: home_server_update_state
  command: /config/pyscript/sensors/update_sensor.py
  value_template: "{{ value_json['total_updates'] }}"
  json_attributes:
    - total_updates
    - security_updates
```

**Binary sensor indicating whether there are updates:**

```yaml
- platform: template
  sensors:
    home_server_updates_available:
      value_template: >
        {{ states('sensor.home_server_update_state') | int > 0 or state_attr('sensor.home_server_update_state', 'security_updates') | int > 0}}
```

To have pyscript updating your server, it uses the *home_server_update* service, which is described below. The automation has to be configured like the following in the pyscript config file:

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  home_server_update:
    update_log: [file to store the logs produced by the home server update]
```

#### Home server update service

Another prerequisite to have pyscript updating your server, is to configure pyscript globally to be able to access the server, where home assistant is run on. Pyscript accesses your server via ssh, so you'll need to exchange ssh keys between your server and the home assistant container. After that you'll need to do the following global pyscript configurations:

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  home_server_update:
    update_log: [file to store the logs produced by the home server update]
global:
  host_server:
    ssh_key: [path to homeassistant private ssh key]
    ssh_login: [login on server]
    ssh_sudo: [sudo password for sudo on server]
```

#### Example

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  home_server_update:
    update_log: /config/tmp/apt_update.log
global:
  host_server:
    ssh_key: "/config/.ssh/id_rsa"
    ssh_login: "robert@some-server"
    ssh_sudo: !secret host_sudo
```

