import tkinter as tk

from sim_essentials import Environment
from settings_manager import GlobalSettings

class SimulationVisualization:
    def __init__(self, env: Environment):
        self.env = env
        self.width = GlobalSettings.settings.win_width
        self.height = GlobalSettings.settings.win_height
        self.cell_width = self.width // self.env.grid_size
        self.cell_height = self.height // self.env.grid_size

        self.window = tk.Tk()
        self.window.title("Simulation Visualization")

        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height, bg="white")
        self.canvas.pack()

        # Bind the 'q' key to quit the visualization
        self.window.bind('q', self.quit)

    def quit(self) -> None:
        self.window.quit()
        self.window.destroy()

    def update(self) -> None:
        self.canvas.delete("all")

        # Draw the grid
        for x in range(0, self.width, self.cell_width):
            self.canvas.create_line(x, 0, x, self.height, fill="gray")
        for y in range(0, self.height, self.cell_height):
            self.canvas.create_line(0, y, self.width, y, fill="gray")

        # Draw the rabbits
        for rabbit in self.env.rabbits:
            x1 = rabbit.x * self.cell_width
            y1 = rabbit.y * self.cell_height
            x2 = x1 + self.cell_width
            y2 = y1 + self.cell_height
            self.canvas.create_oval(x1, y1, x2, y2, fill="blue")

        # Draw the food
        for food in self.env.food:
            x1 = food.x * self.cell_width
            y1 = food.y * self.cell_height
            x2 = x1 + self.cell_width
            y2 = y1 + self.cell_height
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="green")

        # Update the visualization
        self.window.update()

    def run(self, sim_duration: float) -> None:
        while self.env.simpy_env.now < sim_duration:
            self.update()
            self.env.simpy_env.step()
