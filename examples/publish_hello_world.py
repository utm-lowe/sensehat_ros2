#!/usr/bin/env python3
"""Scroll "Hello World" across the LED matrix.

Usage:
    ros2 run sensehat_ros2 sensehat_node      # in another terminal
    python3 examples/publish_hello_world.py   # after sourcing the workspace

The scroll itself runs on the node, so this script exits while the text is still
scrolling.
"""

import time

import rclpy
from rclpy.node import Node

from sensehat_ros2.msg import LedCommand

MESSAGE = 'Hello World'
SCROLL_SPEED = 0.08  # seconds per frame, 0.0 uses the node default
TEXT_COLOR = (0, 255, 128)
BACKGROUND_COLOR = (0, 0, 0)


def make_command():
    command = LedCommand()
    command.type = LedCommand.MESSAGE
    command.message.message = MESSAGE
    command.message.scroll_speed = SCROLL_SPEED
    command.message.text_color.r = TEXT_COLOR[0]
    command.message.text_color.g = TEXT_COLOR[1]
    command.message.text_color.b = TEXT_COLOR[2]
    command.message.background_color.r = BACKGROUND_COLOR[0]
    command.message.background_color.g = BACKGROUND_COLOR[1]
    command.message.background_color.b = BACKGROUND_COLOR[2]
    return command


def main():
    rclpy.init()
    node = Node('led_message_example')
    publisher = node.create_publisher(LedCommand, 'sensehat/led', 10)

    command = make_command()

    # Wait briefly for the subscriber so the first message is not lost.
    deadline = time.monotonic() + 2.0
    while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
        time.sleep(0.1)

    # Publish once: repeating it would queue the same scroll several times.
    publisher.publish(command)

    node.get_logger().info(f"Published message '{MESSAGE}'")
    time.sleep(0.2)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
