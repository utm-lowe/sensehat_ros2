from setuptools import setup

package_name = 'sensehat_ros2'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    package_dir={'': '.'},
    py_modules=[],
    install_requires=[
        'rclpy',
        'sensor_msgs',
        'std_msgs',
    ],
)
