#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, Temperature, FluidPressure, MagneticField
from std_msgs.msg import Float32, String, ColorRGBA
# Import the Sense HAT library
from sense_hat import SenseHat

class SenseHatNode(Node):
    """ROS2 node that publishes Sense HAT sensor data and controls the LED matrix."""

    def __init__(self):
        super().__init__('sensehat_node')
        # Publishers for sensors (example topics)
        self.temp_pub = self.create_publisher(Temperature, 'sensehat/temperature', 10)
        self.humidity_pub = self.create_publisher(Float32, 'sensehat/humidity', 10)
        self.pressure_pub = self.create_publisher(FluidPressure, 'sensehat/pressure', 10)
        self.imu_pub = self.create_publisher(Imu, 'sensehat/imu', 10)
        self.mag_pub = self.create_publisher(MagneticField, 'sensehat/magnetometer', 10)
        self.color_pub = self.create_publisher(ColorRGBA, 'sensehat/color', 10)
        self.brightness_pub = self.create_publisher(Float32, 'sensehat/brightness', 10)
        # Subscriber to LED messages (string for simplicity)
        self.led_sub = self.create_subscription(String, 'sensehat/led_display', self.led_callback, 10)

        self.sense = SenseHat()

        # Optionally clear the LED matrix on startup
        self.sense.clear()

        # Declare publish frequency parameter (default 10 Hz)
        self.declare_parameter('publish_frequency', 10.0)
        freq = self.get_parameter('publish_frequency').get_parameter_value().double_value
        timer_period = 1.0 / freq if freq > 0 else 0.1
        self.timer = self.create_timer(timer_period, self.publish_sensor_data)

        self.get_logger().info('SenseHatNode initialized')

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

        # Color (RGB) from Sense HAT
        color_msg = ColorRGBA()
        r, g, b = self.sense.get_pixel(0, 0)  # example: read pixel at (0,0)
        color_msg.r = r / 255.0
        color_msg.g = g / 255.0
        color_msg.b = b / 255.0
        color_msg.a = 1.0
        self.color_pub.publish(color_msg)

        # Brightness (0-1)
        brightness_msg = Float32()
        brightness_msg.data = self.sense.get_pixel_brightness() if hasattr(self.sense, 'get_pixel_brightness') else 1.0
        self.brightness_pub.publish(brightness_msg)

        self.get_logger().debug('Published real sensor data')

    def led_callback(self, msg: String):
        # Use Sense HAT API to display text on the LED matrix
        self.sense.show_message(msg.data)
        self.get_logger().info(f'Displayed message on LED matrix: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = SenseHatNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
