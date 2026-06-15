import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch.substitutions import Command, EnvironmentVariable
from launch_ros.actions import Node


def generate_launch_description():
    piper_gazebo_share = get_package_share_directory("piper_gazebo")
    piper_description_share = get_package_share_directory("piper_description")

    # Gazebo needs the parent folder of piper_description because meshes are resolved as:
    # model://piper_description/meshes/...
    ros_share_parent = os.path.dirname(piper_description_share)

    world_file = os.path.join(
        piper_gazebo_share,
        "worlds",
        "empty_piper_world.sdf",
    )

    xacro_file = os.path.join(
        piper_description_share,
        "urdf",
        "piper_description_sim.xacro",
    )

    robot_description = {
        "robot_description": Command([
            "xacro ",
            xacro_file,
        ])
    }

    gazebo = ExecuteProcess(
        cmd=["/usr/bin/gz", "sim", "-v", "4", world_file],
        output="screen",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    spawn_piper = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-world", "empty_piper_world",
            "-topic", "/robot_description",
            "-name", "piper",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.0",
        ],
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

        SetEnvironmentVariable(
            name="GZ_SIM_RESOURCE_PATH",
            value=[
                ros_share_parent,
                ":",
                EnvironmentVariable("GZ_SIM_RESOURCE_PATH", default_value=""),
            ],
        ),

        gazebo,
        robot_state_publisher,

        TimerAction(
            period=3.0,
            actions=[spawn_piper],
        ),
    ])