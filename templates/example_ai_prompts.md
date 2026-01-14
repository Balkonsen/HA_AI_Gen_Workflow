# Example AI Prompts and Responses

This document contains real-world examples of AI interactions using your exported HA configuration.

## 📚 Table of Contents

1. [Simple Lighting Automation](#example-1-simple-lighting-automation)
2. [Complex Morning Routine](#example-2-complex-morning-routine)
3. [Energy Monitoring Dashboard](#example-3-energy-monitoring-dashboard)
4. [Climate Control Automation](#example-4-climate-control-automation)
5. [Security System](#example-5-security-system)
6. [Template Sensors](#example-6-template-sensors)
7. [Debugging Existing Automation](#example-7-debugging-existing-automation)

---

## Example 1: Simple Lighting Automation

### 🤖 Prompt to AI

```markdown
Based on my configuration (AI_CONTEXT.json attached), I can see I have:
- sensor.living_room_motion
- light.living_room_main
- sensor.sun_elevation

Please create an automation that:
1. Turns on the living room light when motion is detected
2. Only after sunset
3. Sets brightness to 80% if before 10 PM, 30% if after
4. Turns off after 5 minutes of no motion
5. Uses a friendly name and proper ID
```

### ✅ AI Response

```yaml
# File: motion_lighting.yaml
# Place in: /config/ai_imports/pending/

automation:
  - id: '1705234567890'
    alias: "Living Room Motion Lighting"
    description: "Smart motion-activated lighting with time-based brightness"
    mode: restart
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_motion
        to: 'on'
    condition:
      - condition: sun
        after: sunset
        after_offset: "-00:30:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room_main
        data:
          brightness_pct: >
            {% if now().hour < 22 %}
              80
            {% else %}
              30
            {% endif %}
          transition: 1
      - wait_for_trigger:
          - platform: state
            entity_id: binary_sensor.living_room_motion
            to: 'off'
            for:
              minutes: 5
        timeout:
          minutes: 60
      - service: light.turn_off
        target:
          entity_id: light.living_room_main
        data:
          transition: 2
```

### 📝 Import Instructions

```bash
# 1. Save the response
nano /config/ai_imports/pending/motion_lighting.yaml
# Paste, save (Ctrl+X, Y, Enter)

# 2. Import
ha-ai-workflow import
# Enter branch: feature/motion-lighting
# Type DEPLOY to confirm

# 3. Verify
# Check in HA UI: Settings → Automations & Scenes
```

---

## Example 2: Complex Morning Routine

### 🤖 Prompt to AI

```markdown
Looking at my setup:
- Entities: sensor.bedroom_temperature, light.bedroom_ceiling, 
  switch.coffee_maker, cover.bedroom_blinds, media_player.bedroom_speaker
- Person: person.john

Create a morning routine automation that:
1. Triggers at 6:30 AM on weekdays
2. Only if I'm home
3. Gradually increases bedroom lights over 10 minutes (sunrise effect)
4. Opens blinds halfway
5. Starts coffee maker
6. Plays morning news briefing
7. Adjusts temperature to 72°F
8. Can be disabled via input_boolean
```

### ✅ AI Response

```yaml
# File: morning_routine.yaml
# Place in: /config/ai_imports/pending/

# First, create the input_boolean helper
input_boolean:
  morning_routine_enabled:
    name: "Enable Morning Routine"
    icon: mdi:weather-sunset-up
    initial: true

automation:
  - id: '1705234567891'
    alias: "Morning Routine - Weekdays"
    description: "Comprehensive morning wake-up routine"
    mode: single
    trigger:
      - platform: time
        at: "06:30:00"
    condition:
      - condition: state
        entity_id: input_boolean.morning_routine_enabled
        state: 'on'
      - condition: state
        entity_id: person.john
        state: 'home'
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      # Step 1: Gradual light increase (sunrise effect)
      - repeat:
          count: 10
          sequence:
            - service: light.turn_on
              target:
                entity_id: light.bedroom_ceiling
              data:
                brightness_pct: "{{ repeat.index * 10 }}"
                kelvin: "{{ 2700 + (repeat.index * 100) }}"
            - delay:
                seconds: 60
      
      # Step 2: Open blinds halfway
      - service: cover.set_cover_position
        target:
          entity_id: cover.bedroom_blinds
        data:
          position: 50
      
      # Step 3: Start coffee maker
      - service: switch.turn_on
        target:
          entity_id: switch.coffee_maker
      
      # Step 4: Wait 30 seconds then play news
      - delay:
          seconds: 30
      - service: media_player.play_media
        target:
          entity_id: media_player.bedroom_speaker
        data:
          media_content_id: "https://npr-news.streaming.adswizz.com/morning-edition"
          media_content_type: "music"
      - service: media_player.volume_set
        target:
          entity_id: media_player.bedroom_speaker
        data:
          volume_level: 0.3
      
      # Step 5: Adjust climate
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom
        data:
          temperature: 72
          hvac_mode: heat_cool
      
      # Step 6: Send notification
      - service: notify.mobile_app
        data:
          message: "Good morning! Your morning routine is complete."
          title: "☀️ Morning Routine"
```

### 📝 Customization Notes

```yaml
# To customize:
# 1. Change wake time: line 17 "at: 06:30:00"
# 2. Adjust sunrise duration: line 38 "count: 10" (minutes)
# 3. Change blinds position: line 51 "position: 50" (0-100)
# 4. Modify temperature: line 79 "temperature: 72"
# 5. Change news source: line 67 "media_content_id"
```

---

## Example 3: Energy Monitoring Dashboard

### 🤖 Prompt to AI

```markdown
I have these power monitoring sensors:
- sensor.kitchen_power
- sensor.living_room_power
- sensor.bedroom_power
- sensor.office_power
- sensor.total_home_power
- sensor.solar_production (if generating)

Create a Lovelace dashboard that shows:
1. Total current consumption
2. Individual room breakdown with gauges
3. Daily/weekly cost estimates ($0.15/kWh)
4. Historical graphs (24h, 7d, 30d)
5. Top consumers
6. Solar production vs consumption (if applicable)

Use modern card designs with colors.
```

### ✅ AI Response

```yaml
# File: energy_dashboard.yaml
# Place in: /config/ai_imports/pending/

# First, add template sensors for calculations
template:
  - sensor:
      - name: "Daily Energy Cost"
        unique_id: daily_energy_cost
        unit_of_measurement: "USD"
        state: >
          {{ (states('sensor.total_home_power') | float * 24 * 0.15) | round(2) }}
        icon: mdi:currency-usd
      
      - name: "Top Power Consumer"
        unique_id: top_power_consumer
        state: >
          {% set sensors = [
            ('Kitchen', states('sensor.kitchen_power') | float),
            ('Living Room', states('sensor.living_room_power') | float),
            ('Bedroom', states('sensor.bedroom_power') | float),
            ('Office', states('sensor.office_power') | float)
          ] %}
          {{ sensors | sort(attribute=1, reverse=true) | first | first }}

# Lovelace Dashboard
# Add to your ui-lovelace.yaml or create via UI

title: Energy Monitoring
views:
  - title: Power Usage
    path: energy
    icon: mdi:lightning-bolt
    badges: []
    cards:
      # Current Total Power
      - type: gauge
        entity: sensor.total_home_power
        name: Current Power Usage
        unit: W
        min: 0
        max: 5000
        severity:
          green: 0
          yellow: 2000
          red: 3500
        needle: true
      
      # Daily Cost Card
      - type: entities
        title: 💰 Energy Costs
        entities:
          - entity: sensor.daily_energy_cost
            name: "Estimated Daily Cost"
            icon: mdi:currency-usd
          - type: custom:bar-card
            entity: sensor.total_home_power
            name: "Current Usage"
            unit_of_measurement: W
            min: 0
            max: 5000
            severity:
              - value: 0
                color: '#4CAF50'
              - value: 2000
                color: '#FFC107'
              - value: 3500
                color: '#F44336'
      
      # Room Breakdown
      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.kitchen_power
            name: Kitchen
            unit: W
            min: 0
            max: 1500
            severity:
              green: 0
              yellow: 800
              red: 1200
          
          - type: gauge
            entity: sensor.living_room_power
            name: Living Room
            unit: W
            min: 0
            max: 1500
            severity:
              green: 0
              yellow: 800
              red: 1200
      
      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.bedroom_power
            name: Bedroom
            unit: W
            min: 0
            max: 1000
            severity:
              green: 0
              yellow: 500
              red: 800
          
          - type: gauge
            entity: sensor.office_power
            name: Office
            unit: W
            min: 0
            max: 1000
            severity:
              green: 0
              yellow: 500
              red: 800
      
      # Historical Graph - 24 Hours
      - type: history-graph
        title: Power Usage - Last 24 Hours
        hours_to_show: 24
        refresh_interval: 60
        entities:
          - entity: sensor.total_home_power
            name: Total
          - entity: sensor.kitchen_power
            name: Kitchen
          - entity: sensor.living_room_power
            name: Living Room
          - entity: sensor.bedroom_power
            name: Bedroom
          - entity: sensor.office_power
            name: Office
      
      # Top Consumer
      - type: markdown
        content: >
          ## 🏆 Current Top Consumer
          
          **{{ states('sensor.top_power_consumer') }}**
          
          Using **{{ states('sensor.' ~ states('sensor.top_power_consumer').lower().replace(' ', '_') ~ '_power') }}W**
        title: Top Power Consumer
      
      # Statistics Card
      - type: entities
        title: 📊 Statistics
        entities:
          - type: custom:multiple-entity-row
            entity: sensor.total_home_power
            name: Current Total
            unit: W
            state_header: Now
            entities:
              - entity: sensor.total_home_power
                name: Avg (1h)
                attribute: mean
          
          - entity: sensor.daily_energy_cost
            name: Est. Daily Cost
          
          - type: section
            label: By Room
          
          - entity: sensor.kitchen_power
            name: Kitchen
            secondary_info: last-changed
          
          - entity: sensor.living_room_power
            name: Living Room
            secondary_info: last-changed
          
          - entity: sensor.bedroom_power
            name: Bedroom
            secondary_info: last-changed
          
          - entity: sensor.office_power
            name: Office
            secondary_info: last-changed
```

### 📝 Required Custom Cards

```yaml
# Install via HACS:
# 1. bar-card
# 2. multiple-entity-row

# Or add manually to ui-lovelace.yaml resources:
resources:
  - url: /hacsfiles/bar-card/bar-card.js
    type: module
  - url: /hacsfiles/lovelace-multiple-entity-row/multiple-entity-row.js
    type: module
```

---

## Example 4: Climate Control Automation

### 🤖 Prompt to AI

```markdown
My setup includes:
- climate.bedroom
- climate.living_room
- sensor.outdoor_temperature
- sensor.bedroom_temperature
- sensor.living_room_temperature
- person.john

Create smart climate control that:
1. Maintains different temps for day/night
2. Adjusts based on outdoor temperature
3. Reduces heating/cooling when nobody home
4. "Eco mode" when away > 2 hours
5. Pre-heat/cool before arrival
6. Considers season (winter/summer modes)
```

### ✅ AI Response

```yaml
# File: smart_climate.yaml
# Place in: /config/ai_imports/pending/

# Input helpers for settings
input_number:
  target_temp_day:
    name: "Target Temperature (Day)"
    min: 65
    max: 78
    step: 0.5
    unit_of_measurement: "°F"
    icon: mdi:thermometer
    initial: 72
  
  target_temp_night:
    name: "Target Temperature (Night)"
    min: 60
    max: 75
    step: 0.5
    unit_of_measurement: "°F"
    icon: mdi:thermometer
    initial: 68
  
  target_temp_away:
    name: "Target Temperature (Away)"
    min: 55
    max: 80
    step: 0.5
    unit_of_measurement: "°F"
    icon: mdi:thermometer
    initial: 65

input_boolean:
  smart_climate_enabled:
    name: "Smart Climate Control"
    icon: mdi:thermostat-auto
    initial: true

# Template sensors for logic
template:
  - binary_sensor:
      - name: "Anyone Home"
        unique_id: anyone_home
        device_class: occupancy
        state: >
          {{ is_state('person.john', 'home') }}
      
      - name: "Is Nighttime"
        unique_id: is_nighttime
        state: >
          {{ now().hour >= 22 or now().hour < 6 }}
      
      - name: "Is Summer"
        unique_id: is_summer
        state: >
          {{ now().month in [6, 7, 8, 9] }}
  
  - sensor:
      - name: "Target Temperature"
        unique_id: target_temperature
        unit_of_measurement: "°F"
        state: >
          {% if not is_state('binary_sensor.anyone_home', 'on') %}
            {{ states('input_number.target_temp_away') }}
          {% elif is_state('binary_sensor.is_nighttime', 'on') %}
            {{ states('input_number.target_temp_night') }}
          {% else %}
            {{ states('input_number.target_temp_day') }}
          {% endif %}

# Automations
automation:
  # Main climate adjustment
  - id: '1705234567892'
    alias: "Smart Climate - Adjust Temperature"
    description: "Automatically adjust climate based on presence and time"
    mode: queued
    trigger:
      # Trigger on time changes
      - platform: time_pattern
        minutes: "/15"
      # Trigger on presence changes
      - platform: state
        entity_id: person.john
        to: 
          - 'home'
          - 'not_home'
        for:
          minutes: 5
      # Trigger on time of day
      - platform: time
        at:
          - "06:00:00"  # Morning
          - "22:00:00"  # Night
    condition:
      - condition: state
        entity_id: input_boolean.smart_climate_enabled
        state: 'on'
    action:
      - variables:
          target_temp: "{{ states('sensor.target_temperature') | float }}"
          outdoor_temp: "{{ states('sensor.outdoor_temperature') | float }}"
          is_summer: "{{ is_state('binary_sensor.is_summer', 'on') }}"
          hvac_mode: >
            {% if is_summer %}
              {% if outdoor_temp > target_temp + 5 %}
                cool
              {% else %}
                auto
              {% endif %}
            {% else %}
              {% if outdoor_temp < target_temp - 5 %}
                heat
              {% else %}
                auto
              {% endif %}
            {% endif %}
      
      # Set bedroom climate
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom
        data:
          temperature: "{{ target_temp }}"
          hvac_mode: "{{ hvac_mode }}"
      
      # Set living room climate
      - service: climate.set_temperature
        target:
          entity_id: climate.living_room
        data:
          temperature: "{{ target_temp }}"
          hvac_mode: "{{ hvac_mode }}"
  
  # Pre-arrival climate adjustment
  - id: '1705234567893'
    alias: "Smart Climate - Pre-Arrival"
    description: "Prepare home climate before arrival"
    mode: single
    trigger:
      - platform: zone
        entity_id: person.john
        zone: zone.home
        event: enter
    condition:
      - condition: state
        entity_id: input_boolean.smart_climate_enabled
        state: 'on'
      # Only if been away more than 1 hour
      - condition: template
        value_template: >
          {{ (as_timestamp(now()) - as_timestamp(states.person.john.last_changed)) > 3600 }}
    action:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.bedroom
            - climate.living_room
        data:
          temperature: "{{ states('input_number.target_temp_day') }}"
          hvac_mode: "{{ 'cool' if is_state('binary_sensor.is_summer', 'on') else 'heat' }}"
      
      - service: notify.mobile_app
        data:
          message: "Welcome home! Pre-heating/cooling your home."
          title: "🏠 Climate Control"
  
  # Energy-saving eco mode
  - id: '1705234567894'
    alias: "Smart Climate - Eco Mode"
    description: "Enable eco mode when away for extended period"
    mode: single
    trigger:
      - platform: state
        entity_id: person.john
        to: 'not_home'
        for:
          hours: 2
    condition:
      - condition: state
        entity_id: input_boolean.smart_climate_enabled
        state: 'on'
    action:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.bedroom
            - climate.living_room
        data:
          temperature: "{{ states('input_number.target_temp_away') }}"
          hvac_mode: "auto"
      
      - service: climate.set_preset_mode
        target:
          entity_id:
            - climate.bedroom
            - climate.living_room
        data:
          preset_mode: "eco"
```

---

## Example 5: Security System

### 🤖 Prompt to AI

```markdown
Security entities I have:
- binary_sensor.front_door
- binary_sensor.back_door
- binary_sensor.garage_door
- binary_sensor.motion_hallway
- binary_sensor.motion_living_room
- camera.front_door
- camera.backyard

Create a security system with:
1. Arm/disarm modes (home, away, night)
2. Entry delay when arriving
3. Notifications on breach
4. Camera snapshots on motion
5. Siren simulation (flash lights)
6. Automatic arming when leaving
```

### ✅ AI Response

```yaml
# File: security_system.yaml
# Place in: /config/ai_imports/pending/

# Alarm control panel
alarm_control_panel:
  - platform: manual
    name: "Home Security"
    code: "1234"
    code_arm_required: false
    arming_time: 30
    delay_time: 30
    trigger_time: 300
    disarmed:
      trigger_time: 0
    armed_home:
      arming_time: 0
      delay_time: 0
    armed_away:
      arming_time: 30
      delay_time: 30

# Input helpers
input_boolean:
  security_notifications:
    name: "Security Notifications"
    icon: mdi:bell-ring
    initial: true
  
  security_camera_snapshots:
    name: "Camera Snapshots on Motion"
    icon: mdi:camera
    initial: true

# Automations
automation:
  # Auto-arm when leaving
  - id: '1705234567895'
    alias: "Security - Auto Arm Away"
    description: "Automatically arm security when everyone leaves"
    mode: single
    trigger:
      - platform: state
        entity_id: person.john
        to: 'not_home'
        for:
          minutes: 5
    condition:
      - condition: state
        entity_id: alarm_control_panel.home_security
        state: 'disarmed'
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.home_security
      
      - service: notify.mobile_app
        data:
          message: "Security system armed (Away mode)"
          title: "🔒 Security System"
  
  # Auto-disarm when arriving
  - id: '1705234567896'
    alias: "Security - Auto Disarm on Arrival"
    description: "Notify to disarm when arriving home"
    mode: single
    trigger:
      - platform: zone
        entity_id: person.john
        zone: zone.home
        event: enter
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: alarm_control_panel.home_security
            state: 'disarmed'
    action:
      - service: notify.mobile_app
        data:
          message: "Welcome home! Don't forget to disarm the security system."
          title: "🔒 Security Alert"
          data:
            actions:
              - action: "DISARM_SECURITY"
                title: "Disarm Now"
  
  # Door/window breach detection
  - id: '1705234567897'
    alias: "Security - Breach Detection"
    description: "Detect and alert on security breaches"
    mode: queued
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.front_door
          - binary_sensor.back_door
          - binary_sensor.garage_door
        to: 'on'
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: alarm_control_panel.home_security
            state: 'disarmed'
    action:
      # Flash lights (siren simulation)
      - repeat:
          count: 10
          sequence:
            - service: light.turn_on
              target:
                entity_id: all
              data:
                brightness_pct: 100
                rgb_color: [255, 0, 0]
            - delay:
                milliseconds: 500
            - service: light.turn_off
              target:
                entity_id: all
            - delay:
                milliseconds: 500
      
      # Trigger alarm
      - service: alarm_control_panel.alarm_trigger
        target:
          entity_id: alarm_control_panel.home_security
      
      # Send notification
      - condition: state
        entity_id: input_boolean.security_notifications
        state: 'on'
      
      - service: notify.mobile_app
        data:
          message: "⚠️ SECURITY BREACH: {{ trigger.to_state.attributes.friendly_name }}"
          title: "🚨 SECURITY ALERT"
          data:
            priority: high
            sound: alarm.mp3
            actions:
              - action: "VIEW_CAMERA"
                title: "View Camera"
              - action: "DISARM_SECURITY"
                title: "Disarm"
  
  # Motion detection with camera snapshot
  - id: '1705234567898'
    alias: "Security - Motion Camera Snapshot"
    description: "Take camera snapshot on motion when armed"
    mode: queued
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.motion_hallway
          - binary_sensor.motion_living_room
        to: 'on'
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: alarm_control_panel.home_security
            state: 'disarmed'
      - condition: state
        entity_id: input_boolean.security_camera_snapshots
        state: 'on'
    action:
      - service: camera.snapshot
        target:
          entity_id: camera.front_door
        data:
          filename: "/config/www/snapshots/security_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
      
      - service: notify.mobile_app
        data:
          message: "Motion detected: {{ trigger.to_state.attributes.friendly_name }}"
          title: "🎥 Security Camera"
          data:
            image: "/local/snapshots/security_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
  
  # Night mode activation
  - id: '1705234567899'
    alias: "Security - Auto Night Mode"
    description: "Automatically enable night mode at bedtime"
    mode: single
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: person.john
        state: 'home'
      - condition: state
        entity_id: alarm_control_panel.home_security
        state: 'disarmed'
    action:
      - service: alarm_control_panel.alarm_arm_night
        target:
          entity_id: alarm_control_panel.home_security
      
      - service: notify.mobile_app
        data:
          message: "Security system armed (Night mode)"
          title: "🌙 Security System"
```

---

## Example 6: Template Sensors

### 🤖 Prompt to AI

```markdown
Create useful template sensors for:
1. Count of lights currently on
2. Count of doors/windows open
3. "Someone home" binary sensor
4. Average indoor temperature
5. Power usage status (low/medium/high)
6. Time until next sunrise/sunset
7. Trash day reminder (weekly)
```

### ✅ AI Response

```yaml
# File: template_sensors.yaml
# Place in: /config/ai_imports/pending/

template:
  - sensor:
      # Count lights on
      - name: "Lights On Count"
        unique_id: lights_on_count
        state: >
          {{ states.light 
             | selectattr('state', 'eq', 'on') 
             | list | count }}
        icon: mdi:lightbulb-on
        unit_of_measurement: "lights"
      
      # Count doors/windows open
      - name: "Open Doors Windows"
        unique_id: open_doors_windows
        state: >
          {{ states.binary_sensor 
             | selectattr('attributes.device_class', 'eq', 'door') 
             | selectattr('state', 'eq', 'on') 
             | list | count 
             + states.binary_sensor 
             | selectattr('attributes.device_class', 'eq', 'window') 
             | selectattr('state', 'eq', 'on') 
             | list | count }}
        icon: >
          {% if this.state | int > 0 %}
            mdi:door-open
          {% else %}
            mdi:door-closed
          {% endif %}
        unit_of_measurement: "open"
      
      # Average indoor temperature
      - name: "Average Indoor Temperature"
        unique_id: avg_indoor_temp
        state: >
          {% set temps = [
            states('sensor.living_room_temperature') | float(0),
            states('sensor.bedroom_temperature') | float(0),
            states('sensor.kitchen_temperature') | float(0)
          ] %}
          {{ (temps | sum / temps | length) | round(1) }}
        unit_of_measurement: "°F"
        icon: mdi:thermometer
        device_class: temperature
      
      # Power usage status
      - name: "Power Usage Status"
        unique_id: power_usage_status
        state: >
          {% set power = states('sensor.total_home_power') | float(0) %}
          {% if power < 1000 %}
            Low
          {% elif power < 3000 %}
            Medium
          {% elif power < 5000 %}
            High
          {% else %}
            Very High
          {% endif %}
        icon: >
          {% set power = states('sensor.total_home_power') | float(0) %}
          {% if power < 1000 %}
            mdi:gauge-low
          {% elif power < 3000 %}
            mdi:gauge
          {% else %}
            mdi:gauge-full
          {% endif %}
      
      # Time until next sunrise
      - name: "Time Until Sunrise"
        unique_id: time_until_sunrise
        state: >
          {% set sunrise = as_timestamp(states.sun.sun.attributes.next_rising) %}
          {% set now = as_timestamp(now()) %}
          {% set diff = sunrise - now %}
          {% if diff > 3600 %}
            {{ (diff / 3600) | round(1) }} hours
          {% elif diff > 0 %}
            {{ (diff / 60) | round(0) }} minutes
          {% else %}
            Sunrise has passed
          {% endif %}
        icon: mdi:weather-sunset-up
      
      # Time until next sunset
      - name: "Time Until Sunset"
        unique_id: time_until_sunset
        state: >
          {% set sunset = as_timestamp(states.sun.sun.attributes.next_setting) %}
          {% set now = as_timestamp(now()) %}
          {% set diff = sunset - now %}
          {% if diff > 3600 %}
            {{ (diff / 3600) | round(1) }} hours
          {% elif diff > 0 %}
            {{ (diff / 60) | round(0) }} minutes
          {% else %}
            Sunset has passed
          {% endif %}
        icon: mdi:weather-sunset-down
      
      