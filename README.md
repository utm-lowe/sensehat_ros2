# sensehat_ros2

ROS 2 interfaces for the Raspberry Pi Sense HAT v2: sensor publishers plus an
8x8 LED matrix controlled by a single `LedCommand` message.

## Build

```bash
cd ~/reelfoot_ws
colcon build --packages-select sensehat_ros2
source install/setup.bash
```

## Run

```bash
ros2 run sensehat_ros2 sensehat_node
```

## LED interface

All LED control goes through `sensehat/led` (`sensehat_ros2/msg/LedCommand`).
The message selects a mode with `type` and fills in the matching payload.

| `type` | Constant    | Sense HAT call | Payload          |
| ------ | ----------- | -------------- | ---------------- |
| `0`    | `CHARACTER` | `show_letter`  | `character`      |
| `1`    | `MESSAGE`   | `show_message` | `message`        |
| `2`    | `PIXELS`    | `set_pixels`   | `pixels`         |

An all-zero colour (`r=0, g=0, b=0`) means "not specified" and the node
parameters are used instead. `scroll_speed <= 0` also falls back to the
parameter default.

### Character

```bash
ros2 topic pub --once /sensehat/led sensehat_ros2/msg/LedCommand \
  "{type: 0, character: {character: 'A', text_color: {r: 255, g: 64, b: 0}}}"
```

`character` must be exactly one character; the Sense HAT font is ASCII-only and
unknown glyphs are drawn as `?`.

### Scrolling message

```bash
ros2 topic pub --once /sensehat/led sensehat_ros2/msg/LedCommand \
  "{type: 1, message: {message: 'Hello ROS', scroll_speed: 0.05}}"
```

The scroll is blocking on the node's LED worker thread, so new commands queue up
behind it (queue size is bounded, the oldest pending command is dropped when it
fills).

### Pixels

64 `RGB` entries in row-major order, top-left first. Fixed-size array, so a
wrong length is rejected by the message type itself. CLI YAML is impractical, so
use the example:

```bash
python3 examples/publish_pixels.py
```

### Example scripts

| Script                            | Mode        |
| --------------------------------- | ----------- |
| `examples/publish_character.py`   | `CHARACTER` |
| `examples/publish_hello_world.py` | `MESSAGE`   |
| `examples/publish_pixels.py`      | `PIXELS`    |

Run them from the package source directory after sourcing the workspace.

### Legacy topic

`sensehat/led_display` (`std_msgs/String`) still works and is mapped to a
`MESSAGE` command with default colours. Disable it with
`-p legacy_string_topic:=false`.

## Parameters

| Parameter                 | Default         | Meaning                                   |
| ------------------------- | --------------- | ----------------------------------------- |
| `publish_frequency`       | `10.0`          | Sensor publishing rate (Hz)               |
| `default_text_color`      | `[255, 255, 255]` | Foreground when a colour is omitted     |
| `default_background_color`| `[0, 0, 0]`     | Background when a colour is omitted       |
| `scroll_speed`            | `0.1`           | Seconds per scroll frame                  |
| `rotation`                | `0`             | `0`, `90`, `180` or `270`                 |
| `led_queue_size`          | `8`             | Pending LED commands before drop-oldest   |
| `legacy_string_topic`     | `true`          | Enable the `std_msgs/String` LED topic    |

## Sensor topics

`sensehat/temperature`, `sensehat/humidity`, `sensehat/pressure`,
`sensehat/imu`, `sensehat/magnetometer`.
