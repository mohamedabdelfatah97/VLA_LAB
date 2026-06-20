import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_piper_urdf(piper_xacro_path):
    # Initial PiPER pose on/near the table.
    # We can tune these after the first spawn test.
    piper_x = "-0.35"
    piper_y = "0.00"
    piper_z = "0.750"

    urdf_text = subprocess.check_output(
        ["xacro", piper_xacro_path],
        text=True,
    )

    root = ET.fromstring(urdf_text)

    # Move PiPER's fixed world -> arm_base joint so RViz TF matches Gazebo.
    for joint in root.findall("joint"):
        if joint.attrib.get("name") == "fixed_world_to_arm_base":
            origin = joint.find("origin")
            if origin is None:
                origin = ET.SubElement(joint, "origin")
            origin.set("xyz", f"{piper_x} {piper_y} {piper_z}")
            origin.set("rpy", "0 0 0")
            break

    # Try to keep the first test static in Gazebo so it does not fall before controllers.
    gazebo_tag = ET.SubElement(root, "gazebo")
    static_tag = ET.SubElement(gazebo_tag, "static")
    static_tag.text = "true"

    generated_dir = Path("/tmp/vla_lab_piper_generated")
    generated_dir.mkdir(parents=True, exist_ok=True)

    generated_urdf_path = generated_dir / "piper_description_sim_positioned.urdf"
    ET.ElementTree(root).write(
        generated_urdf_path,
        encoding="unicode",
        xml_declaration=True,
    )

    return str(generated_urdf_path), generated_urdf_path.read_text()


def generate_launch_description():
    piper_gazebo_share = get_package_share_directory("piper_gazebo")
    vla_lab_share = get_package_share_directory("vla_lab_description")
    piper_description_share = get_package_share_directory("piper_description")

    vla_lab_share_parent = os.path.dirname(vla_lab_share)
    piper_description_share_parent = os.path.dirname(piper_description_share)

    world_path = os.path.join(
        piper_gazebo_share,
        "worlds",
        "empty_piper_world.sdf",
    )

    vla_lab_urdf_path = os.path.join(
        vla_lab_share,
        "urdf",
        "vla_lab_description.urdf",
    )

    piper_xacro_path = os.path.join(
        piper_description_share,
        "urdf",
        "piper_description_sim.xacro",
    )

    with open(vla_lab_urdf_path, "r") as urdf_file:
        vla_lab_robot_description_content = urdf_file.read()

    piper_urdf_path, piper_robot_description_content = generate_piper_urdf(
        piper_xacro_path
    )

    vla_lab_robot_description = ParameterValue(
        vla_lab_robot_description_content,
        value_type=str,
    )

    piper_robot_description = ParameterValue(
        piper_robot_description_content,
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
                vla_lab_share_parent,
                ":",
                piper_description_share_parent,
                ":",
                EnvironmentVariable("GZ_SIM_RESOURCE_PATH", default_value=""),
            ],
        ),

        ExecuteProcess(
            cmd=["gz", "sim", "-v", "4", world_path],
            output="screen",
        ),

        # VLA lab TF and robot_state_publisher
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
                {"robot_description": vla_lab_robot_description},
                {"use_sim_time": True},
            ],
            remappings=[
                ("robot_description", "/vla_lab/robot_description"),
            ],
        ),

        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-name", "vla_lab_environment",
                "-file", vla_lab_urdf_path,
                "-x", "0",
                "-y", "0",
                "-z", "0.715",
            ],
            output="screen",
        ),

        # PiPER joint states and robot_state_publisher
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            name="piper_joint_state_publisher",
            output="screen",
            parameters=[
                {"robot_description": piper_robot_description},
                {"use_sim_time": False},
                {"rate": 30},
            ],
        ),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="piper_robot_state_publisher",
            output="screen",
            parameters=[
                {"robot_description": piper_robot_description},
                {"use_sim_time": False},
            ],
        ),

        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-name", "piper_x",
                "-file", piper_urdf_path,
                "-x", "0",
                "-y", "0",
                "-z", "0",
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
