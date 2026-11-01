#!/usr/bin/env python3
"""Draw a single character on the LED matrix.

Usage:
    ros2 run sensehat_ros2 sensehat_node      # in another terminal
    python3 examples/publish_character.py     # after sourcing the workspace

Edit `CHARACTER`, `TEXT_COLOR` and `BACKGROUND_COLOR` to change the output.
"""

import time

import rclpy
from rclpy.node import Node

from sensehat_ros2.msg import LedCommand

CHARACTER = 'A'
TEXT_COLOR = (255, 96, 0)     # orange
BACKGROUND_COLOR = (0, 0, 32)  # dark blue


def make_command():
    command = LedCommand()
    command.type = LedCommand.CHARACTER
    command.character.character = CHARACTER
    command.character.text_color.r = TEXT_COLOR[0]
    command.character.text_color.g = TEXT_COLOR[1]
    command.character.text_color.b = TEXT_COLOR[2]
    command.character.background_color.r = BACKGROUND_COLOR[0]
    command.character.background_color.g = BACKGROUND_COLOR[1]
    command.character.background_color.b = BACKGROUND_COLOR[2]
    return command


def main():
    rclpy.init()
    node = Node('led_character_example')
    publisher = node.create_publisher(LedCommand, 'sensehat/led', 10)

    command = make_command()

    # Wait briefly for the subscriber so the first message is not lost.
    deadline = time.monotonic() + 2.0
    while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
        time.sleep(0.1)

    for _ in range(3):
        publisher.publish(command)
        time.sleep(0.2)

    node.get_logger().info(f"Published character '{CHARACTER}'")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
