# Home assistant pyscript automations

This repository comprises my homeassistant automations (https://www.home-assistant.io/) written with pyscript (https://hacs-pyscript.readthedocs.io). I use these automations on my own smart home server as well as the one I've running at my parents place.
To use these automations, checkout this repository in your homeassistant conifguration directory and name it `pyscript`. Your pyscript configuration yaml file has to be placed outside the pyscript folder. Configure the following in your homeassistant configuration.yaml (e.g. you named your pyscript config yaml file 'pyscript_config.yaml'):

```yaml
default_config:

homeassistant:
  elevation: 130
  time_zone: Europe/Berlin
  customize: !include customize.yaml

pyscript: !include pyscript_config.yaml
```

# Apps

## Activity based entity control

This app can be used to control an entity based on the state of some binary sensor detecting some activity. An example would be turning off the light when no actitvity was detected in a certain room. This app can also be used to toggle scenes based on activity. 


### Configuration in pyscript_config.yaml:

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

### Examples:

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


## Battery observer

This automation observes different entities displaying the battery state of certain devices. You can define an input number, to determine at which percentage you want a notification sent about low battery state.

### Configuration in pyscript_config.yaml:

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

### Example:

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

## Entity Unavailable Notification Service

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

### Example

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

## Home server update

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

### Home server update service

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

### Example

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

## LCD Display Rotation

I wrote this app, as I've contructed an ESP8266 microcontoller based LCD display which is able to receive messages to be displayed via MQTT message queue topics. The device listens to a specific mqtt topic and displays the message sent.


```yaml
allow_all_imports: true
hass_is_global: true
apps:
  lcd_display_rotation:
    display_topic: [mqtt topic to listen to]
    rotate_timeout_entity: [input number entity for rotation timeout in seconds]
    rotation_enabled_entity: [input boolean entity for enabling/disabling rotation]
    displayed_entities:
      - entity: [entity which displays the value, e.g. sensor entity]
        name: [name shown on lcd display]
        unit: [unit of the displayed value]
      - ...
```

![IMG_1216](https://user-images.githubusercontent.com/8775020/201952749-ccfcf852-e65c-4ee6-90bc-4c81af222ca1.jpeg)

### Example

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  lcd_display_rotation:
    display_topic: mqtt_lcd_display/show
    rotate_timeout_entity: input_number.lcd_display_rotation_timeout
    rotation_enabled_entity: input_boolean.lcd_display_rotation_enabled
    displayed_entities:
      - entity: sensor.kitchen_humidity
        name: Humidity
        unit: "%"
      - entity: sensor.kitchen_temperature
        name: Temperature
        unit: "deg. C"
      - entity: sensor.power_sensor
        name: Energy Cons.
        unit: "W"
```

## Netatmo event logger

At the smart home at my parents house, we connected several netatmo security camers (e.g. https://www.netatmo.com/en-us/security/cam-outdoor). These cameras are able to detected humans, cars and animals. The netatmo event logger app will log these events and download the corresponding pictures from the netatmo cloud service. The events which will be logged with a picture are named "human", "animal", "vehicle", "movement" in the netatmo service. In order to get this automation running, you'll need to connect your netatmo account with your homeassistant (https://www.home-assistant.io/integrations/netatmo/). 
At the moment, pictures will be put statically to "/config/tmp/" within the homeassistant docker container.

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  netatmo_event_logger:
    event_log: [file name of the event log]
    cameras:
      - name: [name of camera, will be used as folder name for the picture store]
        id: [mac address of camera (this is the id used to identify the camera via netatmo cloud api and can be retrieved from homeassistant entity data)]
    max_snapshots: [number of snapshots to keep]
```

### Example

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  netatmo_event_logger:
    event_log: /config/tmp/netatmo_event.log
    cameras:
      - name: outside_camera_garage
        id: 70:ff:50:22:4e:ae
      - name: inside_camera_dining_room
        id: 70:ff:50:22:a0:f7
    max_snapshots: 100
```

## State observer

With this app you can observe the state of a given entity and have several actions triggered, if the entity changes to a certain interesting state. An example would be sending a notification to open the window if the humidity in your bathroom is over a certain critical threshold. At my former flat, I had a door sensor connected to my fridge door. If the frigde was opened for longer than a given timeout (e.g. 70 seconds) I was notified on my phone. After closing the fridge door again, I got another notification. With this app you can have a mulitple actions when the observed state is met by the entity and when it was left again.

```yaml
allow_all_imports: true
hass_is_global: true
apps:
state_observer:
  [name of the state observer]:
    observed_entity: [entity to be observed]
    observed_state: [target state which will trigger automations]
    timeout_input_number: [input number specifying how long the entity can be in the observed state without having the actions triggered (optional)]
    actions:
      - service: [service registered in home assistant which will be called]
        arguments:
          [service data (see example)]
      - ...
    state_resolved_actions:
      - service: [service registered in home assistant which will be called]
        arguments:
          [service data (see example)]
      - ...
```

### Examples:

Here the configuration for the described examples above:


```yaml
allow_all_imports: true
hass_is_global: true
apps:
 state_observer:
    trigger_alarm_when_fridge_is_open:
      observed_entity: binary_sensor.kitchen_sensor_door_sensor
      observed_state: "on"
      timeout_input_number: input_number.kitchen_frigde_door_open_alarm_timeout
      actions:
        - service: notify.mobile_app_iphone_von_robert
          arguments:
            title: "Fridge door was left open!"
            message: "Fridge door is open, close it to save the planet!"
            data:
              actions:
                - action: "URI"
                  title: "Open Kitchen Overview"
                  uri: "/lovelace/kitchen"
        - service: pyscript.light_blink
          arguments:
            entity: light.kitchen_ceiling_light_light_switch
            state_entity: binary_sensor.kitchen_sensor_door_sensor
            target_state: "on"
      state_resolved_actions:
        - service: notify.mobile_app_iphone_von_robert
          arguments:
            title: "Fridge was closed again."
            message: "Thanks for not ruining the planet!"
    trigger_alarm_when_plant_closet_is_too_hot:
      observed_entity: binary_sensor.humidity_is_too_high_in_bathroom
      observed_state: "on"
      actions:
        - service: notify.mobile_app_iphone_von_robert
          arguments:
            title: "Humidity Alarm"
            message: "Better open a window in the bathroom..."
            data:
              actions:
                - action: "URI"
                  title: "Open bathroom sensor overview"
                  uri: "/lovelace/bathroom"
      state_resolved_actions:
        - service: notify.mobile_app_iphone_von_robert
          arguments:
            title: "Humidity Alarm Resolved"
            message: "Calm down and have a coffee"
```

## Time based entity control

With this app you can toggle entites at given points of time. An example would be turning on a light at night time and turing it off at day time. Start and end of the interval will be given as input date_time.

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  time_based_entity_control:
    - [self chosen name of automation]:
        entity: [name of entity which will be toggled]
        interval_start: [input date time entity defining start time]
        interval_end: [input date time entity defining end time]
        target_state: [target state, can be "on" or "off"]
        automation_enabled_entity: [input boolean to disable automation]
    - ...
```

### Example

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  time_based_entity_control:
    - outside_light_control:
        entity: switch.outside_lights
        interval_start: input_datetime.outside_light_turn_on_time
        interval_end: input_datetime.outside_light_turn_off_time
        target_state: "on"
        automation_enabled_entity: input_boolean.outside_light_automation_enabled
```

## Timer switch controller

This app can be used, if you want to control an entity with a button to turn it off for example and have it e.g. turned on again after a certain time. At the house of my parents we connected oxygen pumps of a large fishtank to homeassistant. If my parents want to look at the fish, they press the button and the oxygen pumps turn off. That way my parents can have a look at their precious fishes. After a given timeout (e.g. 15 minutes) the pumps go back on without any interaction with the button anymore.

```
allow_all_imports: true
hass_is_global: true
apps:
  timer_switch_controller:
    - button_sensor: [sensor showing button state in homeassistant]
      switch_entity: [switch which will be turned off]
      timer_entity: [timer entity which needs to be defined in homeassistant]
      timeout_entity: [input number defining the timeout (in minutes) until entity will be turned on again]
```

### Example

```yaml
allow_all_imports: true
hass_is_global: true
apps:
  timer_switch_controller:
    - button_sensor: sensor.hue_smart_button_1_action
      switch_entity: switch.oxygen_pump_switch
      timer_entity: timer.reactivated_oxygen_pump_timer
      timeout_entity: input_number.reactivate_oxygen_pump_timeout
```

# Services

## Light blink

The light blink service can be used to have a light blink while a certain other entity is in a specific state. After that state was left, the light will toggle to its former state again. So if it was on, it will stay on and the other way around.

Usage:
```
service: pyscript.light_blink
data:
  entity: [light which will be turned on/off]
  state_entity: [entity defining the state when light will blink]
  target_state: [target state which the entity needs to be in]
  blink_timeout: [timeout between toggling in seconds]
```

### Example

I use this service together with the state observer app, to have my kitchen light blink when the frigde door is opened too long (e.g. somebody forgot to close it):
```
service: pyscript.light_blink
data:
  entity: light.kitchen_ceiling_light
  state_entity: binary_sensor.kitchen_sensor_door_sensor
  target_state: "on"
```

