from pydantic import BaseModel
import matplotlib.pyplot as plt
import pandas as pd

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from sim_essentials import Entity, Environment, Rabbit

class EnvironmentStats(BaseModel):
    time_steps: List[float]
    rabbit_counts: List[int]
    food_counts: List[int]
    removed_rabbits: List[int]
    eaten_food: List[int]
    decayed_food: List[int]

class RabbitStats(BaseModel):
    lowest_hunger_rabbit_id: int
    lowest_hunger: float
    longest_life_rabbit_id: int
    longest_life: float
    max_breeding_count_rabbit_id: int
    max_breeding_count: int

class Collector:
    def __init__(self):
        self.environment_collector = EnvironmentDataCollector()
        self.rabbit_collector = RabbitStatsCollector()
    
class EnvironmentDataCollector:
    def __init__(self):
        self.environment_data = EnvironmentStats(
            time_steps=[],
            rabbit_counts=[],
            food_counts=[],
            removed_rabbits=[],
            eaten_food=[],
            decayed_food=[]
        )

    def collect(
        self, current_time: float, rabbit_count: int, food_count: int, 
        removed_rabbits_count: int, eaten_food: int, decayed_food: int
    ) -> None:
        self.environment_data.time_steps.append(current_time)
        self.environment_data.rabbit_counts.append(rabbit_count)
        self.environment_data.food_counts.append(food_count)
        self.environment_data.removed_rabbits.append(removed_rabbits_count)
        self.environment_data.eaten_food.append(eaten_food)
        self.environment_data.decayed_food.append(decayed_food)

class RabbitStatsCollector:
    def __init__(self):
        # Initialize with default values
        self.stats = RabbitStats(
            lowest_hunger=float('inf'),
            longest_life=0,
            max_breeding_count=0,
            lowest_hunger_rabbit_id=-1,
            longest_life_rabbit_id=-1,
            max_breeding_count_rabbit_id=-1
        )

    def collect(self, rabbit: 'Rabbit') -> None:
        if rabbit.hunger < self.stats.lowest_hunger:
            self.stats.lowest_hunger = rabbit.hunger
            self.stats.lowest_hunger_rabbit_id = rabbit.id
        
        if rabbit.age > self.stats.longest_life:
            self.stats.longest_life = rabbit.age
            self.stats.longest_life_rabbit_id = rabbit.id
        
        if rabbit.breeding_count > self.stats.max_breeding_count:
            self.stats.max_breeding_count = rabbit.breeding_count
            self.stats.max_breeding_count_rabbit_id = rabbit.id

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


class StatisticsVisualization:
    def __init__(self, collector: Collector):
        """
        Initialize the StatisticsVisualization class with collected data.

        Args:
            collector (Collector): Collector object which stores collected statistical data.
        """
        self.environment_data = collector.environment_collector.environment_data
        self.rabbit_stats = collector.rabbit_collector.stats

    def plot_environment_data(
        self, figsize: Tuple[int, int] = (10, 6), save_path: str = ""
    ) -> None:
        """
        Create plots for environment data such as rabbit and food counts over time.
        """
        fig = plt.figure(figsize=figsize)

        for attr_name, values in vars(self.environment_data).items():
            if attr_name != "time_steps" and isinstance(values, list):
                plt.plot(
                    self.environment_data.time_steps, values,
                    label=f'{attr_name.replace("_", " ").title()}'
                )

        plt.xlabel('Time')
        plt.ylabel('Count')
        plt.title('Environment Statistics Over Time')
        plt.legend()
        plt.grid(True)

        fig.savefig(save_path) if save_path else fig.show()
      
    def display_rabbit_stats(self) -> None:
        """
        Display the best rabbit statistics in a table format using pandas.
        """
        # Dynamically creating a list of dictionaries from rabbit_stats attributes
        stats_data = {
            'statistic': [], 'rabbit_id': [], 'value': []
        }
        for stat_name, stat_value in vars(self.rabbit_stats).items():
            if stat_name.endswith('_rabbit_id'):
                corresponding_value_name = stat_name.replace('_rabbit_id', '')
                corresponding_value = getattr(self.rabbit_stats, corresponding_value_name)
                stats_data['statistic'].append(corresponding_value_name)
                stats_data['rabbit_id'].append(stat_value)
                stats_data['value'].append(corresponding_value)

        # Converting the list to a DataFrame
        df = pd.DataFrame(stats_data)
        
        print("Best Rabbit Statistics:\n")
        print(df.to_string(index=False))