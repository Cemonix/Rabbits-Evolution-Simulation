from pydantic import BaseModel

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from sim_essentials import Entity, Environment, Rabbit

class EnvironmentModel(BaseModel):
    time_steps: List[float]
    rabbit_counts: List[int]
    food_counts: List[int]
    removed_rabbits: List[int]
    removed_food: List[int]

class RabbitStatsModel(BaseModel):
    lowest_hunger_rabbit_id: int
    longest_lived_rabbit_id: int
    max_breeding_rabbit_id: int
    lowest_hunger: float
    longest_life: float
    max_breeding_count: int

class Collector:
    def __init__(self):
        self.environment_collector = EnvironmentDataCollector()
        self.rabbit_collector = RabbitStatsCollector()
    
class EnvironmentDataCollector:
    def __init__(self):
        self.environment_data = EnvironmentModel(
            time_steps=[],
            rabbit_counts=[],
            food_counts=[],
            removed_rabbits=[],
            removed_food=[]
        )

    def collect(
        self, current_time: float, rabbit_count: int, food_count: int, 
        removed_rabbits_count: int, removed_food_count: int
    ) -> None:
        self.environment_data.time_steps.append(current_time)
        self.environment_data.rabbit_counts.append(rabbit_count)
        self.environment_data.food_counts.append(food_count)
        self.environment_data.removed_rabbits.append(removed_rabbits_count)
        self.environment_data.removed_food.append(removed_food_count)

class RabbitStatsCollector:
    def __init__(self):
        # Initialize with default values
        self.stats = RabbitStatsModel(
            lowest_hunger=float('inf'),
            longest_life=0,
            max_breeding_count=0,
            lowest_hunger_rabbit_id=-1,
            longest_lived_rabbit_id=-1,
            max_breeding_rabbit_id=-1
        )

    def collect(self, rabbit: 'Rabbit') -> None:
        if rabbit.hunger < self.stats.lowest_hunger:
            self.stats.lowest_hunger = rabbit.hunger
            self.stats.lowest_hunger_rabbit_id = rabbit.id
        
        if rabbit.age > self.stats.longest_life:
            self.stats.longest_life = rabbit.age
            self.stats.longest_lived_rabbit_id = rabbit.id
        
        if rabbit.breeding_count > self.stats.max_breeding_count:
            self.stats.max_breeding_count = rabbit.breeding_count
            self.stats.max_breeding_rabbit_id = rabbit.id

class Logger:
    def __init__(self, env: 'Environment', log_enabled: bool = True):
        self.env = env
        self.log_enabled = log_enabled

    def log_off(self) -> None:
        self.log_enabled = False

    def log_on(self) -> None:
        self.log_enabled = True

    def log(self, msg: str, entity: 'Entity' = None) -> None:
        if self.log_enabled:
            timestamp = f"{self.env.simpy_env.now:.1f}"
            entity_name = f"{str(entity) if entity is not None else ''}"
            print(f"{timestamp}: {entity_name}\t{msg}")
