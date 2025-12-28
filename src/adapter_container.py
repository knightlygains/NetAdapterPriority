import flet as ft
import os
import subprocess
import re
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


class AdapterContainer(ft.Container):
    def __init__(self):
        super().__init__(
            content=ft.Column(scroll="AUTO", expand=True),
            expand=True,
            bgcolor=ft.Colors.GREY_900,
        )
        # Track last changed adapter
        self.last_changed = None

        # Track changed adapters
        self.changed_adapters = []

        # Store adapter data
        self.adapters = []

        # Load adapters from PowerShell script
        self._load_adapters()

        # Populate the adapter list UI
        self.update_adapter_list()

    def sort_adapters_by_metric(self):
        """Sort adapters by their metric value."""
        self.adapters.sort(
            key=lambda x: x["metric"] if x["metric"] is not None else float("inf")
        )

    def update_adapter_list(self):
        self.sort_adapters_by_metric()
        adapter_controls = []
        for adapter in self.adapters:
            adapter_index_in_list = self.adapters.index(adapter)
            if self.last_changed == f"{adapter['index']}":
                bgcolor = ft.Colors.BLUE
                metric_text = f"*Metric:"
            else:
                bgcolor = ft.Colors.BLACK
                metric_text = f"Metric:"

            connected_color = ft.Colors.GREEN

            if adapter["connection_state"] != "Connected":
                connected_color = ft.Colors.RED

            if adapter["connection_state"] == "Unknown":
                connected_color = ft.Colors.GREY

            adapter_control = ft.Container(
                content=ft.Row(
                    [
                        # Info Column
                        ft.Column(
                            [
                                ft.Text(
                                    spans=[
                                        ft.TextSpan(
                                            text=f"{adapter['alias']}",
                                            style=ft.TextStyle(
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ),
                                        ft.TextSpan(
                                            text=f" ({adapter['connection_state']})",
                                            style=ft.TextStyle(
                                                color=connected_color,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ),
                                    ],
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    spans=[
                                        ft.TextSpan(
                                            text=f"Index: ",
                                            style=ft.TextStyle(
                                                weight=ft.FontWeight.BOLD
                                            ),
                                        ),
                                        ft.TextSpan(text=f"{adapter['index']}"),
                                    ],
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    spans=[
                                        ft.TextSpan(
                                            text="Description: ",
                                            style=ft.TextStyle(
                                                weight=ft.FontWeight.BOLD
                                            ),
                                        ),
                                        ft.TextSpan(text=f"{adapter['description']}"),
                                    ],
                                    color=ft.Colors.WHITE,
                                    width=300,
                                ),
                            ],
                        ),
                        # Metric in the Middle
                        ft.Column(
                            [
                                ft.Text(
                                    metric_text,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.TextField(
                                    value=str(adapter["metric"]),
                                    width=60,
                                    on_submit=self.on_metric_field_change,
                                    on_blur=self.on_metric_field_change,
                                    data=adapter_index_in_list,
                                    text_align=ft.TextAlign.CENTER,
                                    color=ft.Colors.WHITE,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color=ft.Colors.GREY,
                                ),
                            ]
                        ),
                        # Adjust Priority Control Column
                        ft.Column(
                            [
                                ft.Text("Priority", color=ft.Colors.WHITE),
                                ft.Button(
                                    icon=ft.Icons.ARROW_UPWARD,
                                    content=" -5",
                                    on_click=self._on_increase_priority,
                                    data=adapter_index_in_list,
                                    color=ft.Colors.BLUE,
                                    icon_color=ft.Colors.BLUE,
                                    bgcolor=ft.Colors.BLACK,
                                ),
                                ft.Button(
                                    icon=ft.Icons.ARROW_DOWNWARD,
                                    content="+5",
                                    on_click=self._on_decrease_priority,
                                    data=adapter_index_in_list,
                                    color=ft.Colors.GREY,
                                    icon_color=ft.Colors.GREY,
                                    bgcolor=ft.Colors.BLACK,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                padding=ft.Padding.only(top=10, bottom=10, left=30, right=30),
                border=ft.Border.all(1, ft.Colors.BLACK),
                border_radius=ft.BorderRadius.all(5),
                bgcolor=bgcolor,
                data=adapter,
                width=800000000,
                margin=ft.Margin.only(left=20, right=20, top=10, bottom=10),
            )

            # Apply bottom margin if last adapter in list
            # Makes space for floating buttons
            if adapter_index_in_list == len(self.adapters) - 1:
                adapter_control.margin = ft.Margin.only(
                    top=10, bottom=60, left=20, right=20
                )

            adapter_controls.append(adapter_control)

            logger.debug(
                f"Loaded adapter: {adapter['description']} with Index {adapter['index']} and Metric {adapter['metric']}"
            )

        # Try to update control
        try:
            self.content.controls = adapter_controls
            self.update()
            logger.info("Adapter list updated on page.")
        except Exception as e:
            # Not added to page yet
            pass

    def _load_adapters(self):
        """Load network adapters using the PowerShell script."""
        try:
            # Get the path to the PowerShell script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, "assets", "SetAdapterPriority.ps1")

            # Execute PowerShell script with -Adapters parameter
            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    script_path,
                    "-Adapters",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                # Parse the output to extract adapter information
                self._parse_adapter_output(result.stdout)
                logger.info(f"Successfully loaded {len(self.adapters)} adapters")
            else:
                logger.error(f"Error loading adapters: {result.stderr}")

        except Exception as e:
            logger.error(f"Exception while loading adapters: {e}", exc_info=True)

    def _parse_adapter_output(self, output: str):
        """Parse PowerShell output and extract adapter information."""
        self.adapters = []
        lines = output.splitlines()
        indices_processed = []  # Track processed indices to avoid duplicates
        for line in lines:
            if line.startswith("[Adapter]"):
                adapter_info = {}
                try:
                    # Use regex to extract fields
                    description_match = re.search(
                        r"\[Description\](.*?)\[Description\]", line
                    )
                    index_match = re.search(r"\[Index\](.*?)\[Index\]", line)
                    metric_match = re.search(r"\[Metric\](.*?)\[Metric\]", line)
                    alias_match = re.search(r"\[Alias\](.*?)\[Alias\]", line)
                    connection_state_match = re.search(
                        r"\[CONNECTION_STATE\](.*?)\[CONNECTION_STATE\]", line
                    )
                    if alias_match:
                        adapter_info["alias"] = alias_match.group(1)
                    else:
                        adapter_info["alias"] = "No Alias"
                    if description_match:
                        adapter_info["description"] = description_match.group(1)
                    else:
                        adapter_info["description"] = "No Description"
                    if index_match:
                        adapter_info["index"] = int(index_match.group(1))
                    else:
                        adapter_info["index"] = None
                    if metric_match:
                        adapter_info["metric"] = int(metric_match.group(1))
                    else:
                        adapter_info["metric"] = None
                    if connection_state_match:
                        adapter_info["connection_state"] = connection_state_match.group(
                            1
                        )
                    else:
                        adapter_info["connection_state"] = "Unknown"
                    if adapter_info["index"] not in indices_processed:
                        self.adapters.append(adapter_info)
                        indices_processed.append(adapter_info["index"])
                    logger.debug(f"Parsed adapter: {adapter_info}")
                except Exception as e:
                    logger.error(f"Error parsing adapter line: {line} with error: {e}")

    def adapter_changed(self, adapter_index: int):
        """Mark an adapter as changed."""
        if adapter_index not in self.changed_adapters:
            self.changed_adapters.append(adapter_index)

    def on_metric_field_change(self, e: ft.ControlEvent):
        """Handle metric field change."""
        adapter_index = e.control.data
        new_metric_value = e.control.value
        if self.adapters[adapter_index]["metric"] == int(new_metric_value):
            return  # No change
        try:
            new_metric_int = int(new_metric_value)
            if new_metric_int < 10 or not int(new_metric_value):
                new_metric_int = 10
            self.adapters[adapter_index]["metric"] = new_metric_int
            self.last_changed = f"{self.adapters[adapter_index]['index']}"
            self.adapter_changed(self.adapters[adapter_index]["index"])
            logger.info(
                f"Metric changed for adapter: {self.adapters[adapter_index]['alias']}: New Metric: {new_metric_int}"
            )
            self.update_adapter_list()
        except ValueError:
            logger.error(
                f"Invalid metric value entered: {new_metric_value} for adapter: {self.adapters[adapter_index]['alias']}"
            )

    def _on_increase_priority(self, e: ft.ControlEvent):
        """Handle increase priority button click."""
        adapter_index = e.control.data
        # Increase priority by decreasing metric value, clamp at 10
        self.adapters[adapter_index]["metric"] -= 5
        # Update last changed value
        self.last_changed = f"{self.adapters[adapter_index]['index']}"
        if self.adapters[adapter_index]["metric"] < 10:
            self.adapters[adapter_index]["metric"] = 10
        self.adapter_changed(self.adapters[adapter_index]["index"])
        logger.info(
            f"Increasing priority for adapter: {self.adapters[adapter_index]['alias']}: New Metric: {self.adapters[adapter_index]['metric']}"
        )
        self.update_adapter_list()

    def _on_decrease_priority(self, e: ft.ControlEvent):
        """Handle decrease priority button click."""
        adapter_index = e.control.data
        # Decrease priority by increasing metric value
        self.adapters[adapter_index]["metric"] += 5
        self.last_changed = f"{self.adapters[adapter_index]['index']}"
        if self.adapters[adapter_index]["metric"] < 10:
            self.adapters[adapter_index]["metric"] = 10
        self.adapter_changed(self.adapters[adapter_index]["index"])
        logger.info(
            f"Decreasing priority for adapter: {self.adapters[adapter_index]['alias']}: New Metric: {self.adapters[adapter_index]['metric']}"
        )
        self.update_adapter_list()

    def apply_priority_changes(self):
        """Apply the priority changes using the PowerShell script."""
        try:
            if len(self.changed_adapters) == 0:
                logger.info("No adapter changes to apply.")
                return

            logger.info(
                f"Applying priority changes to {len(self.changed_adapters)} adapters"
            )

            # Get the path to the PowerShell script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, "assets", "SetAdapterPriority.ps1")

            # Prepare priority list
            priority_list = []
            for adapter in self.adapters:
                if adapter["index"] in self.changed_adapters:
                    priority_list.append(f"{adapter['index']} {adapter['metric']}")

            # Execute PowerShell script with -Priority parameter
            for change in priority_list:
                change_index, change_metric = change.split()
                logger.info(f"Setting adapter {change_index} metric to {change_metric}")
                result = subprocess.run(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        script_path,
                        "-Priority",
                        f"{change_index} {change_metric}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                logger.debug(f"PowerShell output: {result.stdout}")

                if result.returncode == 0:
                    logger.info(
                        f"Successfully applied priority change for adapter {change_index}"
                    )
                else:
                    logger.error(f"Error applying priority changes: {result.stderr}")

            self._load_adapters()
            self.update_adapter_list()
            self.changed_adapters = []
            logger.info("All priority changes applied successfully")

        except Exception as e:
            logger.error(
                f"Exception while applying priority changes: {e}", exc_info=True
            )

    def reset_changes(self):
        """Reset any uncommitted changes."""
        logger.info("Resetting uncommitted changes")
        self.changed_adapters = []
        self.last_changed = None
        self._load_adapters()
        self.update_adapter_list()
        logger.info("Changes reset successfully")
