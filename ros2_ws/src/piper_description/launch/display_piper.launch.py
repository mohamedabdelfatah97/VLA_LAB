from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration("use_gui")

    xacro_file = PathJoinSubstitution([
        FindPackageShare("piper_description"),
        "urdf",
        "piper_description.xacro",
    ])

    robot_description = {
        "robot_description": Command([
            "xacro ",
            xacro_file,
        ])
    }

    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        condition=None,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    rviz_config = PathJoinSubstitution([
        FindPackageShare("piper_description"),
        "rviz",
        "piper_ros2_display.rviz",
    ])

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    static_world_to_base_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_world_to_arm_base_tf",
        arguments=[
            "--x", "0",
            "--y", "0",
            "--z", "0",
            "--roll", "0",
            "--pitch", "0",
            "--yaw", "0",
            "--frame-id", "world",
            "--child-frame-id", "arm_base",
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_gui",
            default_value="true",
            description="Use joint_state_publisher_gui",
        ),
        joint_state_publisher_node,
        robot_state_publisher_node,
        static_world_to_base_tf_node,
        rviz_node,
    ])
