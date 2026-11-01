cmake_minimum_required(VERSION 3.10)
project(sensehat_ros2)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RGB.msg"
  "msg/CharacterData.msg"
  "msg/MessageData.msg"
  "msg/PixelsData.msg"
  "msg/LedCommand.msg"
)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  scripts/sensehat_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
