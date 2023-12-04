import json
from pydantic import BaseModel

class GlobalSettings:
    """
    A class to manage global simulation settings and configuration.

    This class provides a mechanism to load and access global simulation
    settings from an external JSON file. It includes a static method
    `load_settings` to load settings from a specified file path and store
    them as an instance of the `SimulationSettings` class.

    Attributes:
        settings: An instance of the `SimulationSettings` class containing
            the loaded simulation settings.
        day_minutes (int): The number of minutes in a simulated day. 

    Example Usage:
        GlobalSettings.load_settings('simulation_config.json')
        print(GlobalSettings.settings.rabbit.base_speed)  # Access a specific setting.
    """
    settings = None
    day_minutes = 1440

    @staticmethod
    def load_settings(file_path: str) -> None:
        """
        Load simulation settings from a JSON file and store them.

        Args:
            file_path (str): The path to the JSON file containing simulation
                settings.
        """
        with open(file_path, 'r') as file:
            settings_dict = json.load(file)
        GlobalSettings.settings = SimulationSettings(**settings_dict)

class EnvironmentSettings(BaseModel):
    grid_size: int
    win_width: int
    win_height: int
    path_to_sprites: str
    time_factor: float

class RabbitSettings(BaseModel):
    start_rabbits_count: int
    rate: int
    generate_new: bool
    scan_radius: float
    base_hunger: float
    base_hunger_factor: float
    hunger_fatigue: float
    hunger_to_breed: float
    base_speed: float
    base_breed_timeout: float
    breeding_reset_speed: float

class FoodSettings(BaseModel):
    start_food_count: int
    rate: int
    generate_new: bool
    min_nutrition: float
    max_nutrition: float
    lifespan: int

class SimulationSettings(BaseModel):
    environment: EnvironmentSettings
    rabbit: RabbitSettings
    food: FoodSettings