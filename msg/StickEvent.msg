# Single event from the Sense HAT 5-way joystick.
# One message per device event, in the order the events occurred.
#
# Only `pressed` and `released` are published by default; `held` (kernel
# autorepeat while a direction stays down) must be enabled with the
# `publish_held_events` parameter.

std_msgs/Header header

uint8 UP=0
uint8 DOWN=1
uint8 LEFT=2
uint8 RIGHT=3
uint8 MIDDLE=4

# Which way the stick moved (or MIDDLE for the centre press).
uint8 direction

uint8 PRESSED=0
uint8 RELEASED=1
uint8 HELD=2

# What happened: pushed down, let go, or still held.
uint8 action
