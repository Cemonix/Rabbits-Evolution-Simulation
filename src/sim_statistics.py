from pydantic import BaseModel
import matplotlib.pyplot as plt
import pandas as pd

from typing import List, Tuple, TYPE_CHECKING

from settings_manager import GlobalSettings

if TYPE_CHECKING:
    from sim_essentials import Entity, Environment, Rabbit

class EnvironmentStats(BaseModel):
    time_steps: List[float] = []
    rabbit_counts: List[int] = []
    food_counts: List[int] = []
    removed_rabbits: List[int] = []
    eaten_food: List[int] = []
    decayed_food: List[int] = []

class RabbitBestStats(BaseModel):
    lowest_hunger_rabbit_id: int
    lowest_hunger: float
    longest_life_rabbit_id: int
    longest_life: float
    max_breeding_count_rabbit_id: int
    max_breeding_count: int

class CurrentStepRabbitStats(BaseModel):
    scan_radius: float
    base_hunger: float
    base_hunger_factor: float
    hunger_to_breed: float
    hunger_fatigue: float
    base_breed_timeout: float
    breeding_reset_speed: float
    speed: float

class RabbitAttributeStats(BaseModel):
    scan_radius: List[float] = []
    base_hunger: List[float] = []
    base_hunger_factor: List[float] = []
    hunger_to_breed: List[float] = []
    hunger_fatigue: List[float] = []
    base_breed_timeout: List[float] = []
    breeding_reset_speed: List[float] = []
    speed: List[float] = []

class Collector:
    """
    A class responsible for holding other collector used in simulation.

    Attributes:
        environment_collector (EnvironmentDataCollector): An instance of the
            EnvironmentDataCollector for collecting environment-related data.
        rabbit_collector (RabbitStatsCollector): An instance of the RabbitStatsCollector
            for collecting statistics related to rabbits.
    """
    def __init__(self):
        self.environment_collector = EnvironmentDataCollector()
        self.rabbit_collector = RabbitStatsCollector()
    
class EnvironmentDataCollector:
    """
    A class responsible for collecting and managing data related to the simulation environment.

    Attributes:
        environment_data (EnvironmentStats): An instance of the EnvironmentStats class
            that stores collected data.
    """
    def __init__(self):
        self.environment_data = EnvironmentStats()

    def collect(
        self, current_time: float, rabbit_count: int, food_count: int, 
        removed_rabbits_count: int, eaten_food: int, decayed_food: int
    ) -> None:
        """
        Collect and store environment-related data at the current time step.

        Args:
            current_time (float): The current time step in the simulation.
            rabbit_count (int): The number of rabbits in the environment.
            food_count (int): The number of food items in the environment.
            removed_rabbits_count (int): The count of rabbits removed from the environment.
            eaten_food (int): The count of food items consumed by rabbits.
            decayed_food (int): The count of food items that have decayed.
        """
        self.environment_data.time_steps.append(current_time)
        self.environment_data.rabbit_counts.append(rabbit_count)
        self.environment_data.food_counts.append(food_count)
        self.environment_data.removed_rabbits.append(removed_rabbits_count)
        self.environment_data.eaten_food.append(eaten_food)
        self.environment_data.decayed_food.append(decayed_food)

class RabbitStatsCollector:
    def __init__(self):
        """
        Initialize a RabbitStatsCollector instance.

        Attributes:
            best_stats (RabbitBestStats): Stores the best statistics among all rabbits.
            current_step_rabbit_stats (CurrentStepRabbitStats): Stores statistics 
                of the current step's best rabbit.
            rabbit_attribute_stats (RabbitAttributeStats): Stores attributes statistics of rabbits.
        """
        self.best_stats = RabbitBestStats(
            lowest_hunger=float('inf'),
            longest_life=0,
            max_breeding_count=0,
            lowest_hunger_rabbit_id=-1,
            longest_life_rabbit_id=-1,
            max_breeding_count_rabbit_id=-1
        )

        self.current_step_rabbit_stats = CurrentStepRabbitStats(
            scan_radius = GlobalSettings.settings.rabbit.scan_radius,
            base_hunger = GlobalSettings.settings.rabbit.base_hunger,
            base_hunger_factor = GlobalSettings.settings.rabbit.base_hunger_factor,
            hunger_to_breed = GlobalSettings.settings.rabbit.hunger_to_breed,
            hunger_fatigue = GlobalSettings.settings.rabbit.hunger_fatigue,
            base_breed_timeout = GlobalSettings.settings.rabbit.base_breed_timeout,
            breeding_reset_speed = GlobalSettings.settings.rabbit.breeding_reset_speed,
            speed = GlobalSettings.settings.rabbit.base_speed
        )

        self.rabbit_attribute_stats = RabbitAttributeStats()

    def collect_rabbit_attribute_stats(self) -> None:
        """
        Collects and stores statistics of a best rabbit from current simulation step.
        """
        self.rabbit_attribute_stats.scan_radius.append(
            self.current_step_rabbit_stats.scan_radius
        )
        self.rabbit_attribute_stats.base_hunger.append(
            self.current_step_rabbit_stats.base_hunger
        )
        self.rabbit_attribute_stats.base_hunger_factor.append(
            self.current_step_rabbit_stats.base_hunger_factor
        )
        self.rabbit_attribute_stats.hunger_to_breed.append(
            self.current_step_rabbit_stats.hunger_to_breed
        )
        self.rabbit_attribute_stats.hunger_fatigue.append(
            self.current_step_rabbit_stats.hunger_fatigue
        )
        self.rabbit_attribute_stats.base_breed_timeout.append(
            self.current_step_rabbit_stats.base_breed_timeout
        )
        self.rabbit_attribute_stats.breeding_reset_speed.append(
            self.current_step_rabbit_stats.breeding_reset_speed
        )
        self.rabbit_attribute_stats.speed.append(
            self.current_step_rabbit_stats.speed
        )

    def update_best_rabbit_stats(self, rabbit: 'Rabbit') -> None:
        """
        Update the best rabbit statistics based on the provided rabbit's attributes.

        Args:
            rabbit (Rabbit): The rabbit whose attributes are used for updating the statistics.
        """
        if rabbit.hunger < self.best_stats.lowest_hunger:
            self.best_stats.lowest_hunger = rabbit.hunger
            self.best_stats.lowest_hunger_rabbit_id = rabbit.id
        
        if rabbit.age > self.best_stats.longest_life:
            self.best_stats.longest_life = rabbit.age
            self.best_stats.longest_life_rabbit_id = rabbit.id
        
        if rabbit.breeding_count > self.best_stats.max_breeding_count:
            self.best_stats.max_breeding_count = rabbit.breeding_count
            self.best_stats.max_breeding_count_rabbit_id = rabbit.id

    def update_current_step_rabbit_stats(self, rabbit: 'Rabbit') -> None:
        """
        Update the statistics of the best rabbit from the current simulation step based
        on the provided rabbit's attributes.

        Args:
            rabbit (Rabbit): The rabbit whose attributes are used for updating the statistics.
        """
        if rabbit.hunger < self.current_step_rabbit_stats.base_hunger:
            self.current_step_rabbit_stats.base_hunger = rabbit.hunger
        
        if rabbit.scan_radius > self.current_step_rabbit_stats.scan_radius:
            self.current_step_rabbit_stats.scan_radius = rabbit.scan_radius

        if rabbit.base_hunger_factor < self.current_step_rabbit_stats.base_hunger_factor:
            self.current_step_rabbit_stats.base_hunger_factor = rabbit.base_hunger_factor

        if rabbit.hunger_to_breed < self.current_step_rabbit_stats.hunger_to_breed:
            self.current_step_rabbit_stats.hunger_to_breed = rabbit.hunger_to_breed

        if rabbit.hunger_fatigue > self.current_step_rabbit_stats.hunger_fatigue:
            self.current_step_rabbit_stats.hunger_fatigue = rabbit.hunger_fatigue

        if rabbit.base_breed_timeout < self.current_step_rabbit_stats.base_breed_timeout:
            self.current_step_rabbit_stats.base_breed_timeout = rabbit.base_breed_timeout

        if rabbit.breeding_reset_speed > self.current_step_rabbit_stats.breeding_reset_speed:
            self.current_step_rabbit_stats.breeding_reset_speed = rabbit.breeding_reset_speed

        if rabbit.speed > self.current_step_rabbit_stats.speed:
            self.current_step_rabbit_stats.speed = rabbit.speed

class Logger:
    def __init__(self, env: 'Environment', log_enabled: bool = True):
        """
        Initialize a Logger instance.

        Args:
            env (Environment): The simulation environment.
            log_enabled (bool, optional): Whether logging is initially enabled. Defaults to True.
        """
        self.env = env
        self.log_enabled = log_enabled

    def log_off(self) -> None:
        self.log_enabled = False

    def log_on(self) -> None:
        self.log_enabled = True

    def log(self, msg: str, entity: 'Entity' = None) -> None:
        """
        Log a message with an optional associated entity.

        Args:
            msg (str): The message to log.
            entity (Entity, optional): The entity associated with the message. Defaults to None.
        """
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
        self.rabbit_attribute_stats = collector.rabbit_collector.rabbit_attribute_stats
        self.rabbit_stats = collector.rabbit_collector.best_stats
      
    def save_environment_stats_fig(
        self, save_path: str, figsize: Tuple[int, int] = (10, 6)
    ) -> None:
        """
        Save a figure displaying environment statistics over time.

        Args:
            save_path (str): The file path to save the figure.
            figsize (Tuple[int, int], optional): The figure's width and height in inches.
                Defaults to (10, 6).
        """
        fig, ax = plt.subplots(figsize=figsize)

        for attr_name, values in vars(self.environment_data).items():
            if attr_name != "time_steps" and isinstance(values, list):
                ax.plot(
                    self.environment_data.time_steps, values,
                    label=f'{attr_name.replace("_", " ").title()}'
                )

        ax.set_xlabel('Time')
        ax.set_ylabel('Count')
        ax.set_title('Environment Statistics Over Time')
        ax.legend()
        ax.grid(True)

        fig.savefig(save_path)
    
    def save_rabbit_stats_fig(
        self, save_path: str, figsize: Tuple[int, int] = (10, 6)
    ) -> None:
        """
        Save a figure displaying rabbit attribute statistics over time.

        Args:
            save_path (str): The file path to save the figure.
            figsize (Tuple[int, int], optional): The figure's width and height in inches.
                Defaults to (10, 6).
        """
        fig, ax = plt.subplots(figsize=figsize)

        for attr_name, values in vars(self.rabbit_attribute_stats).items():
            if isinstance(values, list):
               ax.plot(
                    values, label=f'{attr_name.replace("_", " ").title()}'
                )
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Attribute value')
        ax.set_title('Rabbit attribute statistics over time')
        ax.legend()
        ax.grid(True)

        fig.savefig(save_path)

    def display_rabbit_stats(self, current_env_time: float) -> None:
        """
        Display the best rabbit statistics.

        Args:
            current_env_time (float): The current time in the simulation environment.
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

        df = pd.DataFrame(stats_data)
        
        print("Best Rabbit Statistics:\n")
        print(f"Current environment time: {current_env_time}\n")
        print(df.to_string(index=False))