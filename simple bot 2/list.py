import logging
import ast
import time
from multiprocessing import Process, Lock, Manager
from adb_module import ADBModule
from navigation_tool import NavigationTool


class Workflow:
    def __init__(self, coordinates_file, adb=None, navigation_tool=None):
        self.coordinates_file = coordinates_file
        self.adb = adb or ADBModule()
        self.navigation_tool = navigation_tool or NavigationTool(adb=self.adb)
        self.logger = logging.getLogger("Workflow")
        self._setup_logging()
        self.lock = Lock()  # To ensure safe logging in multiprocessing

    def _setup_logging(self):
        """Set up logging for Workflow."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def load_coordinates(self):
        """Load coordinates from the file."""
        try:
            with open(self.coordinates_file, 'r') as file:
                data = file.read()
                coordinates = ast.literal_eval(data)  # Safely parse the list of tuples
                self.logger.info(f"Loaded {len(coordinates)} coordinates successfully.")
                return coordinates
        except Exception as e:
            self.logger.error(f"Failed to load coordinates: {e}")
            raise

    def process_coordinates(self, device_id, coordinates, delay, shared_log):
        """Process coordinates for a specific device."""
        last_coordinates = {"kingdom": None, "x": None, "y": None}  # Keep track of last processed coordinates

        for index, (kingdom, x, y) in enumerate(coordinates, start=1):
            try:
                self.logger.info(f"[{device_id}] Processing coordinate {index}/{len(coordinates)}: Kingdom={kingdom}, X={x}, Y={y}")

                # Navigate to coordinates only if they differ from the last processed
                self.navigation_tool.navigate_to_coordinates(
                    device_id,
                    kingdom,
                    x,
                    y,
                    last_kingdom=last_coordinates["kingdom"],
                    last_x=last_coordinates["x"],
                    last_y=last_coordinates["y"]
                )

                # Update last processed coordinates
                last_coordinates.update({"kingdom": kingdom, "x": x, "y": y})

                # Wait for stabilization
                time.sleep(delay)
                self.logger.info(f"[{device_id}] Waiting for location to stabilize before capturing screenshot.")

                # Capture screenshot
                screenshot_path = f"screenshots/{device_id}_kingdom_{kingdom}_x_{x}_y_{y}.png"
                self.adb.capture_screenshot(device_id, screenshot_path)
                self.logger.info(f"[{device_id}] Captured screenshot: {screenshot_path}")

                # Update shared log
                shared_log[device_id] = f"Processed Kingdom={kingdom}, X={x}, Y={y}"
            except Exception as e:
                self.logger.error(f"[{device_id}] Failed to process coordinate: {e}")

    def execute_workflow(self, devices, coordinates_per_device, delay=0.2):
        """Execute the workflow for multiple devices in parallel."""
        processes = []
        manager = Manager()
        shared_log = manager.dict()

        # Create a process for each device
        for device_id, coordinates in zip(devices, coordinates_per_device):
            process = Process(target=self.process_coordinates, args=(device_id, coordinates, delay, shared_log))
            processes.append(process)
            with self.lock:
                self.logger.info(f"Process created for device: {device_id}")

        # Start all processes
        for process in processes:
            process.start()
            with self.lock:
                self.logger.info(f"Process {process.name} started.")

        # Wait for all processes to complete
        for process in processes:
            process.join()
            with self.lock:
                self.logger.info(f"Process {process.name} finished.")


# Example usage
if __name__ == "__main__":
    coordinates_file = "centerpoints.txt"  # Path to the uploaded coordinates file
    workflow = Workflow(coordinates_file)

    # Detect connected devices
    devices = workflow.adb.get_connected_devices()
    if devices:
        # Load coordinates
        coordinates = workflow.load_coordinates()

        # Split coordinates among devices
        chunk_size = len(coordinates) // len(devices)
        coordinates_per_device = [coordinates[i:i + chunk_size] for i in range(0, len(coordinates), chunk_size)]

        # Distribute any remainder coordinates to the last device
        while len(coordinates_per_device) > len(devices):
            coordinates_per_device[-2].extend(coordinates_per_device.pop())

        # Execute workflow across devices
        workflow.execute_workflow(devices, coordinates_per_device, delay=0.2)
