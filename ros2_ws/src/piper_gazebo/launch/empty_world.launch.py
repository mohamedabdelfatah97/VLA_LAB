import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    world_file = PathJoinSubstitution([
        FindPackageShare("piper_gazebo"),
        "worlds",
        "empty_piper_world.sdf",
    ])

    gazebo = ExecuteProcess(
        cmd=["/usr/bin/gz", "sim", "-v", "4", world_file],
        output="screen",
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            name="GZ_CONFIG_PATH",
            value=[
                "/usr/share/gz:",
                EnvironmentVariable("GZ_CONFIG_PATH", default_value=""),
            ],
        ),
        gazebo,
    ])