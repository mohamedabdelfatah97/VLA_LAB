import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    piper_gazebo_share = get_package_share_directory("piper_gazebo")
    vla_lab_share = get_package_share_directory("vla_lab_description")

    ros_share_parent = os.path.dirname(vla_lab_share)

    world_path = os.path.join(
        piper_gazebo_share,
        "worlds",
        "empty_piper_world.sdf",
    )

    urdf_path = os.path.join(
        vla_lab_share,
        "urdf",
        "vla_lab_description.urdf",
    )

    with open(urdf_path, "r") as urdf_file:
        robot_description_content = urdf_file.read()

    robot_description = ParameterValue(
        robot_description_content,
        value_type=str,
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

        ExecuteProcess(
            cmd=["gz", "sim", "-v", "4", world_path],
            output="screen",
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="world_to_vla_lab_base_link",
            arguments=[
                "--x", "0",
                "--y", "0",
                "--z", "0.715",
                "--roll", "0",
                "--pitch", "0",
                "--yaw", "0",
                "--frame-id", "world",
                "--child-frame-id", "vla_lab_base_link",
            ],
            output="screen",
        ),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="vla_lab_robot_state_publisher",
            output="screen",
            parameters=[
                {"robot_description": robot_description},
                {"use_sim_time": True},
            ],
        ),

        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-name", "vla_lab_environment",
                "-file", urdf_path,
                "-x", "0",
                "-y", "0",
                "-z", "0.715",
            ],
            output="screen",
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            parameters=[
                {"use_sim_time": False},
            ],
        ),
    ])
