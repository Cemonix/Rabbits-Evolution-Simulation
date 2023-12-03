import tkinter as tk
from PIL import Image, ImageTk

from sim_essentials import Environment
from settings_manager import GlobalSettings

from typing import Tuple

class SimulationVisualization:
    def __init__(self, env: Environment):
        self.env = env
        self.settings = GlobalSettings.settings
        self.width = self.settings.environment.win_width
        self.height = self.settings.environment.win_height
        self.cell_width = self.width // self.env.grid_size
        self.cell_height = self.height // self.env.grid_size

        self.window = tk.Tk()
        self.window.title("Simulation Visualization")

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
        self.is_simulation_running = False

    def run(self, sim_duration: float) -> None:
        self.is_simulation_running = True
        self.window.bind('q', self.end_simulation)

        while self.env.simpy_env.now < sim_duration and self.is_simulation_running:
            self.update()
            self.env.collector.environment_collector.collect(
                self.env.simpy_env.now, len(self.env.rabbits), len(self.env.food),
                self.env.removed_rabbits, self.env.eaten_food, self.env.decayed_food
            )
            self.env.simpy_env.step()

        self.canvas.destroy()
        self.window.destroy()

    def load_image(self, path_to_image: str) -> ImageTk.PhotoImage:
        image = Image.open(path_to_image)
        return ImageTk.PhotoImage(image)

    def load_image_and_resize(
        self, path_to_image: str, resolution: Tuple[int, int]
    ) -> ImageTk.PhotoImage:
        image = Image.open(path_to_image)
        resized_image = image.resize(resolution, Image.NEAREST)
        return ImageTk.PhotoImage(resized_image)

