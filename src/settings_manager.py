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
    hunger_fatique: float
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