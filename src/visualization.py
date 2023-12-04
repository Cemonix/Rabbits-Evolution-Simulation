import tkinter as tk
from PIL import Image, ImageTk

from sim_essentials import Environment
from settings_manager import GlobalSettings

from typing import Tuple

class SimulationVisualization:
    """
    A class responsible for visualizing the simulation using Tkinter.

    Attributes:
        env (Environment): The environment instance containing simulation data.
        settings (SimulationSettings): The global simulation settings.
        width (int): The width of the visualization window.
        height (int): The height of the visualization window.
        cell_width (int): The width of a single grid cell in the visualization.
        cell_height (int): The height of a single grid cell in the visualization.
        window (tk.Tk): The Tkinter main window for visualization.
        canvas (tk.Canvas): The canvas for drawing simulation elements.
        background_img (ImageTk.PhotoImage): The background image of the simulation.
        rabbit_img (ImageTk.PhotoImage): The image representing rabbits.
        food_img (ImageTk.PhotoImage): The image representing food.
        decayed_food_img (ImageTk.PhotoImage): The image representing decayed food.

    Example Usage:
        visualization = SimulationVisualization(env)
        visualization.run(1000)  # Run the visualization for 1000 simulation steps.
    """
    def __init__(self, env: Environment):
        """
        Initialize the SimulationVisualization instance.

        Args:
            env (Environment): The environment instance containing simulation data.
        """
        self.env = env
        self.settings = GlobalSettings.settings
        self.width = self.settings.environment.win_width
        self.height = self.settings.environment.win_height
        self.cell_width = self.width // self.env.grid_size
        self.cell_height = self.height // self.env.grid_size

        self.window = tk.Tk()
        self.window.title("Simulation Visualization")
        self.window.bind('q', self.end_simulation)

        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height)
        self.canvas.pack()

        self.background_img = self.load_image(
            f"{self.settings.environment.path_to_sprites}/background.png"
        )
        self.rabbit_img = self.load_image_and_resize(
            f"{self.settings.environment.path_to_sprites}/rabbit.png", (32, 32)
        )
        self.food_img = self.load_image_and_resize(
            f"{self.settings.environment.path_to_sprites}/food.png", (32, 32)
        )
        self.decayed_food_img = self.load_image_and_resize(
            f"{self.settings.environment.path_to_sprites}/decayed_food.png", (32, 32)
        )

    def update(self) -> None:
        """
        Update the visualization canvas with the current state of the simulation.
        """
        self.canvas.delete("all")

        # Canvas background
        self.canvas.create_image(0, 0, image=self.background_img, anchor='nw')

        # Draw the rabbits
        for rabbit in self.env.rabbits:
            x1 = rabbit.x * self.cell_width
            y1 = rabbit.y * self.cell_height
            self.canvas.create_image(x1, y1, image=self.rabbit_img, anchor='nw')

        # Draw the food
        for food in self.env.food:
            x1 = food.x * self.cell_width
            y1 = food.y * self.cell_height
            if food.current_lifespan < GlobalSettings.settings.food.lifespan // 2:
                self.canvas.create_image(x1, y1, image=self.decayed_food_img, anchor='nw')
            else:  
                self.canvas.create_image(x1, y1, image=self.food_img, anchor='nw')

        # Update the visualization
        self.window.update()

    def end_simulation(self, _) -> None:
        """
        End the simulation when the 'q' key is pressed.

        Args:
            _ (Event): The event object (not used).
        """
        self.is_simulation_running = False

    def run(self, sim_duration: float) -> None:
        """
        Run the simulation visualization for a specified duration.

        Args:
            sim_duration (float): The duration (in simulation time) to run the visualization.
        """
        self.is_simulation_running = True

        while (
            self.env.simpy_env.now < sim_duration and
            self.is_simulation_running
        ):
            self.update()

            # Collect statistics
            self.env.collector.environment_collector.collect(
                self.env.simpy_env.now, len(self.env.rabbits), len(self.env.food),
                self.env.removed_rabbits, self.env.eaten_food, self.env.decayed_food
            )
            self.env.collector.rabbit_collector.collect_rabbit_attribute_stats()

            if(
                not self.settings.rabbit.generate_new and
                len(self.env.rabbits) == 0
            ):
                break

            self.env.simpy_env.step()

        self.canvas.destroy()
        self.window.destroy()

    def load_image(self, path_to_image: str) -> ImageTk.PhotoImage:
        """
        Load an image from a file and return it as a Tkinter PhotoImage.

        Args:
            path_to_image (str): The path to the image file.

        Returns:
            ImageTk.PhotoImage: The loaded image as a Tkinter PhotoImage.
        """
        image = Image.open(path_to_image)
        return ImageTk.PhotoImage(image)

    def load_image_and_resize(
        self, path_to_image: str, resolution: Tuple[int, int]
    ) -> ImageTk.PhotoImage:
        """
        Load an image, resize it, and return it as a Tkinter PhotoImage.

        Args:
            path_to_image (str): The path to the image file.
            resolution (Tuple[int, int]): The target resolution (width, height).

        Returns:
            ImageTk.PhotoImage: The loaded and resized image as a Tkinter PhotoImage.
        """
        image = Image.open(path_to_image)
        resized_image = image.resize(resolution, Image.NEAREST)
        return ImageTk.PhotoImage(resized_image)