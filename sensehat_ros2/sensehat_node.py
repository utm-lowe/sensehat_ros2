#!/usr/bin/env python3

import queue
import threading

import rclpy
from rclpy.node import Node
from sense_hat import SenseHat
from sensor_msgs.msg import FluidPressure, Imu, MagneticField, Temperature
from std_msgs.msg import Float32, String

from sensehat_ros2.msg import LedCommand

LED_TOPIC = 'sensehat/led'
LEGACY_LED_TOPIC = 'sensehat/led_display'
VALID_ROTATIONS = (0, 90, 180, 270)


class SenseHatNode(Node):
    """ROS2 node that publishes Sense HAT sensor data and controls the LED matrix."""

    def __init__(self):
        super().__init__('sensehat_node')

        # Parameters -------------------------------------------------------
        self.declare_parameter('publish_frequency', 10.0)
        self.declare_parameter('default_text_color', [255, 255, 255])
        self.declare_parameter('default_background_color', [0, 0, 0])
        self.declare_parameter('scroll_speed', 0.1)
        self.declare_parameter('rotation', 0)
        self.declare_parameter('led_queue_size', 8)
        self.declare_parameter('legacy_string_topic', True)

        self._default_text_color = self._read_color_parameter('default_text_color')
        self._default_background_color = self._read_color_parameter('default_background_color')
        self._scroll_speed = self.get_parameter('scroll_speed').value
        if self._scroll_speed <= 0.0:
            self.get_logger().warning(
                f'scroll_speed parameter must be > 0.0, got {self._scroll_speed}; using 0.1')
            self._scroll_speed = 0.1
        queue_size = max(1, int(self.get_parameter('led_queue_size').value))
        rotation = int(self.get_parameter('rotation').value)
        if rotation not in VALID_ROTATIONS:
            self.get_logger().warning(
                f'rotation parameter must be one of {VALID_ROTATIONS}, got {rotation}; using 0')
            rotation = 0

        # Publishers for sensors (example topics)
        self.temp_pub = self.create_publisher(Temperature, 'sensehat/temperature', 10)
        self.humidity_pub = self.create_publisher(Float32, 'sensehat/humidity', 10)
        self.pressure_pub = self.create_publisher(FluidPressure, 'sensehat/pressure', 10)
        self.imu_pub = self.create_publisher(Imu, 'sensehat/imu', 10)
        self.mag_pub = self.create_publisher(MagneticField, 'sensehat/magnetometer', 10)

        # LED command queue consumed by a dedicated worker thread so that a
        # long blocking show_message() scroll never stalls the sensor timer.
        self._led_queue = queue.Queue(maxsize=queue_size)
        self._led_stop = threading.Event()
        self._led_thread = None

        self.sense = SenseHat()
        self.sense.set_rotation(rotation)
        self.sense.clear()

        # Subscribers ------------------------------------------------------
        self.led_sub = self.create_subscription(
            LedCommand, LED_TOPIC, self.led_callback, 10)
        self.legacy_led_sub = None
        if self.get_parameter('legacy_string_topic').value:
            self.legacy_led_sub = self.create_subscription(
                String, LEGACY_LED_TOPIC, self.legacy_led_callback, 10)

        # Declare publish frequency parameter (default 10 Hz)
        freq = self.get_parameter('publish_frequency').get_parameter_value().double_value
        timer_period = 1.0 / freq if freq > 0 else 0.1
        self.timer = self.create_timer(timer_period, self.publish_sensor_data)

        self._led_thread = threading.Thread(
            target=self._led_worker, name='sensehat_led', daemon=True)
        self._led_thread.start()

        self.get_logger().info(
            f'SenseHatNode initialized (LED commands on {LED_TOPIC})')

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------
    def _read_color_parameter(self, name):
        value = list(self.get_parameter(name).value)
        if len(value) != 3 or any(not 0 <= int(c) <= 255 for c in value):
            self.get_logger().warning(
                f'{name} must be a list of 3 integers in 0..255, got {value}; using defaults')
            return [255, 255, 255] if name == 'default_text_color' else [0, 0, 0]
        return [int(c) for c in value]

    # ------------------------------------------------------------------
    # Sensors
    # ------------------------------------------------------------------
    def publish_sensor_data(self):
        # In a real implementation, read from the Sense HAT library.
        temp_msg = Temperature()
        temp_msg.temperature = self.sense.get_temperature()
        self.temp_pub.publish(temp_msg)

        humidity_msg = Float32()
        humidity_msg.data = self.sense.get_humidity()
        self.humidity_pub.publish(humidity_msg)

        pressure_msg = FluidPressure()
        pressure_msg.fluid_pressure = self.sense.get_pressure()
        self.pressure_pub.publish(pressure_msg)

        # IMU
        imu_msg = Imu()
        accel = self.sense.get_accelerometer_raw()
        gyro = self.sense.get_gyroscope_raw()
        imu_msg.linear_acceleration.x = accel['x']
        imu_msg.linear_acceleration.y = accel['y']
        imu_msg.linear_acceleration.z = accel['z']
        imu_msg.angular_velocity.x = gyro['x']
        imu_msg.angular_velocity.y = gyro['y']
        imu_msg.angular_velocity.z = gyro['z']
        # Orientation not provided directly
        self.imu_pub.publish(imu_msg)

        # Magnetometer
        mag_msg = MagneticField()
        mag = self.sense.get_compass_raw()
        mag_msg.magnetic_field.x = mag['x']
        mag_msg.magnetic_field.y = mag['y']
        mag_msg.magnetic_field.z = mag['z']
        self.mag_pub.publish(mag_msg)

        self.get_logger().debug('Published real sensor data')

    # ------------------------------------------------------------------
    # LED commands
    # ------------------------------------------------------------------
    def _resolve_color(self, color, default):
        """An all-zero colour means 'not specified'; use the node default."""
        if color.r == 0 and color.g == 0 and color.b == 0:
            return list(default)
        return [int(color.r), int(color.g), int(color.b)]

    def _build_job(self, msg):
        """Validate a LedCommand and turn it into a display job, or None."""
        if msg.type == LedCommand.CHARACTER:
            character = msg.character.character
            if len(character) != 1:
                self.get_logger().warning(
                    f"CHARACTER command needs exactly one character, got '{character}'")
                return None
            text_color = self._resolve_color(
                msg.character.text_color, self._default_text_color)
            back_color = self._resolve_color(
                msg.character.background_color, self._default_background_color)
            return ('character', (character, text_color, back_color))

        if msg.type == LedCommand.MESSAGE:
            text = msg.message.message
            if not text:
                self.get_logger().warning('MESSAGE command needs a non-empty string')
                return None
            scroll_speed = msg.message.scroll_speed
            if scroll_speed <= 0.0:
                scroll_speed = self._scroll_speed
            text_color = self._resolve_color(
                msg.message.text_color, self._default_text_color)
            back_color = self._resolve_color(
                msg.message.background_color, self._default_background_color)
            return ('message', (text, scroll_speed, text_color, back_color))

        if msg.type == LedCommand.PIXELS:
            pixels = [[int(p.r), int(p.g), int(p.b)] for p in msg.pixels.pixels]
            return ('pixels', (pixels,))

        self.get_logger().warning(
            f'Unknown LedCommand type {msg.type}; expected '
            f'{LedCommand.CHARACTER}, {LedCommand.MESSAGE} or {LedCommand.PIXELS}')
        return None

    def _enqueue_job(self, job):
        try:
            self._led_queue.put_nowait(job)
        except queue.Full:
            # Drop the oldest pending command so the newest one always wins.
            try:
                dropped = self._led_queue.get_nowait()
                self.get_logger().debug(f'LED queue full, dropped {dropped[0]} command')
            except queue.Empty:
                pass
            try:
                self._led_queue.put_nowait(job)
            except queue.Full:
                self.get_logger().warning('LED queue full, dropping command')

    def led_callback(self, msg: LedCommand):
        job = self._build_job(msg)
        if job is not None:
            self._enqueue_job(job)

    def legacy_led_callback(self, msg: String):
        if not msg.data:
            self.get_logger().warning('Empty string on the legacy LED topic ignored')
            return
        self.get_logger().debug(
            f"'{LEGACY_LED_TOPIC}' is deprecated, publish a LedCommand on '{LED_TOPIC}'")
        self._enqueue_job(('message', (
            msg.data, self._scroll_speed,
            list(self._default_text_color), list(self._default_background_color))))

    def _led_worker(self):
        while not self._led_stop.is_set():
            try:
                kind, args = self._led_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                if kind == 'character':
                    self.sense.show_letter(*args)
                elif kind == 'message':
                    self.sense.show_message(*args)
                elif kind == 'pixels':
                    self.sense.set_pixels(*args)
                self.get_logger().debug(f'Displayed {kind} on LED matrix')
            except Exception as exc:  # noqa: B902 - keep the worker alive
                self.get_logger().error(f'Failed to update LED matrix ({kind}): {exc}')

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def destroy_node(self):
        self._led_stop.set()
        if self._led_thread is not None:
            self._led_thread.join(timeout=2.0)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SenseHatNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
