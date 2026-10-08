"""Compatibility entry point for the feature-oriented desktop client."""

from client_features.core import *
from client_features.core import main


def run_client():
    """Run the desktop client through the extracted implementation."""
    main()


def start_keyboard_listener():
    """Start the keyboard listener through the extracted implementation."""
    from client_features.core import start_keyboard_listener as start_listener

    start_listener()


if __name__ == "__main__":
    run_client()
