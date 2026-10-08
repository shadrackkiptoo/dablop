"""Self-update and startup install helpers for the client."""

from .core import (
    check_for_updates,
    cleanup_old_update_versions,
    cleanup_update_artifacts,
    create_versioned_update_directory,
    download_update,
    get_startup_command,
    github_ssl_context,
    install_and_relaunch,
    install_self_to_startup_location,
    register_startup_launch,
    running_from_local_project,
    running_from_temp_bundle,
    schedule_update,
    send_successful_update_notice,
    update_checker,
    version_tuple,
)

__all__ = [
    "check_for_updates",
    "cleanup_old_update_versions",
    "cleanup_update_artifacts",
    "create_versioned_update_directory",
    "download_update",
    "get_startup_command",
    "github_ssl_context",
    "install_and_relaunch",
    "install_self_to_startup_location",
    "register_startup_launch",
    "running_from_local_project",
    "running_from_temp_bundle",
    "schedule_update",
    "send_successful_update_notice",
    "update_checker",
    "version_tuple",
]
