import json
from pydantic import BaseModel

class GlobalSettings:
    settings = None
    day_minutes = 1440

    @staticmethod
    def load_settings(file_path: str) -> None:
        with open(file_path, 'r') as file:
            settings_dict = json.load(file)
        GlobalSettings.settings = SimulationSettings(**settings_dict)

class SimulationSettings(BaseModel):
    grid_size: int
    win_width: int
    win_height: int
    time_factor: float
    rabbits_per_day: int
    rabbit_radius: int
    rabbit_hunger: int
    base_food_rate: int
    food_lifespan: int