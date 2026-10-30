from setuptools import setup
import os

package_name = 'sensehat_ros2'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    package_dir={'': '.'},
    py_modules=[],
    data_files=[('share/ament_index/resource_index/packages', ['resource/' + package_name]),
                ('share/' + package_name, ['package.xml'])],
    install_requires=[
        'rclpy',
        'sensor_msgs',
        'std_msgs',
    ],
    entry_points={
        'console_scripts': [
            'sensehat_node = sensehat_ros2.sensehat_node:main',
        ],
    },
)
