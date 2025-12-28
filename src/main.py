import flet as ft
from adapter_container import AdapterContainer
import asyncio
import logging
import os
from datetime import datetime
import ctypes

app_data_path = os.getenv("FLET_APP_STORAGE_DATA")


# Configure logging
def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = f"{app_data_path}/logs"
    os.makedirs(log_dir, exist_ok=True)

    print("Log directory:", app_data_path)

    # Create log filename with timestamp
    log_filename = os.path.join(
        log_dir, f"netadapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),  # Also output to console
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    return logger


# Initialize logging
logger = setup_logging()


def main(page: ft.Page):
    logger.info("Application started")
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "Network Adapter Priority Manager"
    page.padding = 0

    adapter_container = AdapterContainer()

    def show_banner(msg="This is a banner", icon=ft.Icons.INFO, type="info"):
        color = ft.Colors.BLUE
        if type == "success":
            color = ft.Colors.GREEN
        if type == "error":
            color = ft.Colors.RED

        banner = ft.Banner(
            bgcolor=ft.Colors.with_opacity(0.2, color),
            leading=ft.Icon(icon, color=color),
            content=ft.Text(msg, color=ft.Colors.WHITE),
            actions=[ft.TextButton("Dismiss", on_click=page.pop_dialog)],
        )
        page.show_dialog(banner)
        page.update()

    def help_click(e=None):
        show_banner(
            "The lower the metric, the higher the priority. Increments by 5",
            ft.Icons.HELP,
            type="info",
        )

    def admin_check(e=None):
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.error(f"Admin check failed: {e}", exc_info=True)
            is_admin = False
        if not is_admin:
            show_banner(
                "Warning: Not running with administrative privileges. Changes will not be applied.",
                ft.Icons.WARNING,
                type="error",
            )
        else:
            logger.info("Application is running with administrative privileges.")

    async def save_changes(e=None):
        logger.info("Save changes initiated")
        # Disable the UI
        page.controls[0].disabled = True
        show_banner(
            "Applying changes, please wait...", ft.Icons.HOURGLASS_TOP, type="info"
        )

        # Update the page to show disabled state
        page.update()

        # Allow the event loop to process the update and render the UI
        await asyncio.sleep(0.1)

        try:
            # Now run the long-running operation
            adapter_container.apply_priority_changes()
            logger.info("Adapter priority changes applied successfully")

            # Show success message
            show_banner(
                "Adapter priorities have been updated.",
                ft.Icons.SAVE,
                type="success",
            )
        except Exception as ex:
            logger.error(f"Error applying priority changes: {ex}", exc_info=True)
            show_banner(
                f"Error applying changes: {str(ex)}",
                ft.Icons.ERROR,
                type="error",
            )

        # Re-enable the UI
        page.controls[0].disabled = False
        page.update()

    async def reset_changes(e=None):
        logger.info("Reset changes initiated")
        # Disable the UI
        page.controls[0].disabled = True
        show_banner(
            "Undoing changes...",
            type="info",
        )
        # Update the page to show disabled state
        page.update()

        # Allow the event loop to process the update and render the UI
        await asyncio.sleep(0.1)

        try:
            # Now run the long-running operation
            adapter_container.reset_changes()
            logger.info("Changes reset successfully")

            # Show success message
            show_banner(
                "Uncommitted changes have been reset.",
                ft.Icons.RESTORE,
                type="success",
            )
        except Exception as ex:
            logger.error(f"Error resetting changes: {ex}", exc_info=True)
            show_banner(
                f"Error resetting changes: {str(ex)}",
                ft.Icons.ERROR,
                type="error",
            )

        # Re-enable the UI
        page.controls[0].disabled = False
        page.update()

    # Floating Action buttons
    floating_help = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.HELP,
            icon_color=ft.Colors.BLUE,
            on_click=help_click,
            tooltip="Show help",
        ),
        bottom=10,
        right=20,
        width=50,
        bgcolor=ft.Colors.GREY_800,
        border_radius=ft.BorderRadius(
            top_left=20, bottom_left=20, top_right=20, bottom_right=20
        ),
    )
    floating_reset = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.RESTORE,
            on_click=reset_changes,
            icon_color=ft.Colors.YELLOW,
            tooltip="Reset uncommitted changes",
        ),
        bottom=10,
        right=70,
        width=50,
        bgcolor=ft.Colors.GREY_800,
        border_radius=ft.BorderRadius(
            top_left=20, bottom_left=20, top_right=20, bottom_right=20
        ),
    )
    floating_save = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.SAVE,
            on_click=save_changes,
            icon_color=ft.Colors.GREEN,
            tooltip="Apply changes",
        ),
        bottom=10,
        right=120,
        width=50,
        bgcolor=ft.Colors.GREY_800,
        border_radius=ft.BorderRadius(
            top_left=20, bottom_left=20, top_right=20, bottom_right=20
        ),
    )

    help_click()
    admin_check()

    page.add(
        ft.Stack(
            [
                adapter_container,
                floating_save,
                floating_reset,
                floating_help,
            ],
            expand=True,
        )
    )


ft.run(main)
