#!/usr/bin/env python3
"""Print Sense HAT joystick events.

Usage:
    ros2 run sensehat_ros2 sensehat_node      # in another terminal
    python3 examples/stick_listener.py        # after sourcing the workspace
"""

import rclpy
from rclpy.node import Node

from sensehat_ros2.msg import StickEvent

DIRECTION_NAMES = {
    StickEvent.UP: 'UP',
    StickEvent.DOWN: 'DOWN',
    StickEvent.LEFT: 'LEFT',
    StickEvent.RIGHT: 'RIGHT',
    StickEvent.MIDDLE: 'MIDDLE',
}
ACTION_NAMES = {
    StickEvent.PRESSED: 'pressed',
    StickEvent.RELEASED: 'released',
    StickEvent.HELD: 'held',
}


class StickListener(Node):
    """Log every event published on sensehat/stick."""

    def __init__(self):
        super().__init__('stick_listener_example')
        self.subscription = self.create_subscription(
            StickEvent, 'sensehat/stick', self.stick_callback, 10)

    def stick_callback(self, msg):
        direction = DIRECTION_NAMES.get(
            msg.direction, f'unknown({msg.direction})')
        action = ACTION_NAMES.get(msg.action, f'unknown({msg.action})')
        self.get_logger().info(f'{direction} {action}')


def main():
    rclpy.init()
    node = StickListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
