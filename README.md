# sensehat_ros2

ROS 2 interfaces for the Raspberry Pi Sense HAT v2: sensor publishers, 8x8 LED
matrix control via a single `LedCommand` message, and 5-way joystick events.

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

## Stick interface

The 5-way joystick is published as discrete events on `sensehat/stick`
(`sensehat_ros2/msg/StickEvent`), one message per hardware event, in order.

| `direction` | Constant |
| ----------- | -------- |
| `0`         | `UP`     |
| `1`         | `DOWN`   |
| `2`         | `LEFT`   |
| `3`         | `RIGHT`  |
| `4`         | `MIDDLE` |

| `action` | Constant   | Meaning                        |
| -------- | ---------- | ------------------------------ |
| `0`      | `PRESSED`  | Stick pushed down              |
| `1`      | `RELEASED` | Stick let go                   |
| `2`      | `HELD`     | Still down (kernel autorepeat) |

`HELD` is kernel autorepeat while a direction stays down, so it is **not**
published unless `publish_held_events:=true`.

```bash
ros2 topic echo /sensehat/stick
ros2 run sensehat_ros2 sensehat_node -p publish_held_events:=true
```

In a subscriber, compare against the message constants:

```python
from sensehat_ros2.msg import StickEvent

def stick_callback(self, msg):
    if msg.direction == StickEvent.MIDDLE and msg.action == StickEvent.PRESSED:
        self.toggle_mode()
```

The node polls `SenseStick.get_events()` on a timer (`stick_poll_frequency`),
so do **not** also assign `sense.stick.direction_*` callbacks: both paths
consume the same evdev device and would steal events from each other.

### Level state for generic consumers

For nodes that expect a level signal rather than edges (teleop, rviz, joystick
demos), `sensehat/joy` (`sensor_msgs/Joy`) mirrors the buttons:

| `buttons` index | Direction |
| --------------- | --------- |
| `0`             | up        |
| `1`             | down      |
| `2`             | left      |
| `3`             | right     |
| `4`             | middle    |

Each entry is `1` while pressed and `0` otherwise. It is published when the
state changes and republished at `publish_frequency` so late-joining
subscribers still learn the current state. `axes` is left empty. Disable it
with `-p publish_joy:=false`.

### Example script

`examples/stick_listener.py` prints every event (`UP pressed`,
`MIDDLE released`, ...). Run it from the package source directory after
sourcing the workspace.

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
| `publish_stick_events`    | `true`          | Publish `sensehat/stick` events           |
| `publish_held_events`     | `false`         | Include autorepeat `HELD` events          |
| `publish_joy`             | `true`          | Publish the `sensor_msgs/Joy` mirror      |
| `stick_poll_frequency`    | `50.0`          | Joystick polling rate (Hz)                |

## Topics

Sensors: `sensehat/temperature`, `sensehat/humidity`, `sensehat/pressure`,
`sensehat/imu`, `sensehat/magnetometer`.

Stick: `sensehat/stick` (`StickEvent`) and `sensehat/joy` (`sensor_msgs/Joy`).

LED input: `sensehat/led` (`LedCommand`) and the legacy
`sensehat/led_display` (`std_msgs/String`).
