#!/usr/bin/env python3
"""Publish a full 8x8 frame to /sensehat/led.

Usage:
    ros2 run sensehat_ros2 sensehat_node      # in another terminal
    python3 examples/publish_pixels.py        # after sourcing the workspace

The frame below draws a simple gradient; edit `frame()` to change it.
"""

import time

import rclpy
from rclpy.node import Node

from sensehat_ros2.msg import LedCommand


def frame():
    """Return 64 (r, g, b) tuples in row-major, top-left-first order."""
    pixels = []
    for y in range(8):
        for x in range(8):
            pixels.append((x * 32, y * 32, 255 - (x + y) * 16))
    return pixels


def main():
    rclpy.init()
    node = Node('led_pixel_example')
    publisher = node.create_publisher(LedCommand, 'sensehat/led', 10)

    command = LedCommand()
    command.type = LedCommand.PIXELS
    for index, (r, g, b) in enumerate(frame()):
        command.pixels.pixels[index].r = r
        command.pixels.pixels[index].g = g
        command.pixels.pixels[index].b = b

    # Wait briefly for the subscriber so the first message is not lost.
    deadline = time.monotonic() + 2.0
    while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
        time.sleep(0.1)

    for _ in range(3):
        publisher.publish(command)
        time.sleep(0.2)

    node.get_logger().info('Published 64-pixel frame')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
