from abc import ABC, abstractmethod
import random
import simpy

from settings_manager import GlobalSettings

from typing import List, Tuple

class Entity(ABC):
    count = 0

    def __init__(self, env: 'Environment'):
        self.env = env
        self.id = Entity.count
        Entity.count += 1
        self.env.simpy_env.process(self.lifetime())

    def __str__(self):
        return f"{self.__class__.__name__} : {self.id}"

    @abstractmethod
    def lifetime(self):
        raise NotImplemented("Lifetime method is not implemented!")
    
    def manhattan_distance_between(
        self, first: Tuple[int, int], second: Tuple[int, int]
    ) -> int:
        return abs(first[0] - second[0]) + abs(first[1] - second[1])

class Collector(Entity):
    def __init__(self, env: 'Environment', timeout_interval: float):
        super().__init__(env)
        self.env = env
        self.timeout_interval = timeout_interval
        self.time_records = []

    def lifetime(self) -> None:
        while True:
            self.time_records.append(self.env.simpy_env.now)
            self.collect()
            yield self.env.simpy_env.timeout(self.timeout_interval * self.env.time_factor)

    @abstractmethod
    def collect(self) -> None:
        raise NotImplemented("Collect method is not implemented!")

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

class Environment:
    def __init__(
        self, grid_size: int, realtime: bool = True
    ):
        self.time_factor = GlobalSettings.settings.time_factor
        self.simpy_env = simpy.RealtimeEnvironment(
            self.time_factor, strict=False
        ) if realtime else simpy.Environment()
        self.rabbits: List[Rabbit] = []
        self.food: List[Food] = []
        self.grid_size: int = grid_size
        self.logger = Logger(self)

    def add_rabbit(self, rabbit: 'Rabbit') -> None:
        self.rabbits.append(rabbit)

    def add_food(self, food: 'Food') -> None:
        self.food.append(food)

    def run_simulation(self, sim_duration: int | float) -> None:
        self.simpy_env.run(until=sim_duration)

class Rabbit(Entity):
    def __init__(
        self, env: Environment, x: int, y: int
    ):
        super().__init__(env)
        self.x: int = x
        self.y: int = y
        self.scan_radius = GlobalSettings.settings.rabbit_radius
        self.hunger = GlobalSettings.settings.rabbit_hunger
        self.move_locations: List[Tuple[int, int]] = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (-1, -1), (1, -1), (-1, 1)
        ]

    def lifetime(self) -> None:
        while True:
            nearby_food = self.scan_for_food(self.scan_radius)
            if nearby_food:
                # Find nearest food based on manhatten distance
                nearest_food: Food = min(
                    nearby_food,
                    key=lambda food: self.manhattan_distance_between(
                        (self.x, self.y), (food.x, food.y)
                    )
                )

                move_dx, move_dy = self.move_towards(nearest_food)
                self.env.logger.log(
                    f"Moving towards food at ({nearest_food.x}, {nearest_food.y})", entity=self
                )
            else:
                move_dx, move_dy = random.choice(self.move_locations)

            move_dx, move_dy = self.adjust_move_if_outside_grid(
                self.x + move_dx, self.y + move_dy, move_dx, move_dy
            )
            self.x += move_dx
            self.y += move_dy
            # self.env.logger.log(f"Moved randomly to ({self.x}, {self.y})", entity=self)

            for food in self.env.food:
                if (self.x, self.y) == (food.x, food.y):
                    self.consume_food(food)

            yield self.env.simpy_env.timeout(1 * self.env.time_factor)

            self.hunger += 0.1

            if self.hunger > 5:
                self.remove_rabbit()
                break

    def adjust_move_if_outside_grid(
        self, new_x: int, new_y: int, move_dx: int, move_dy: int
    ) -> Tuple[int, int]:
        """
        If position after movement is outside of the grid, move direction will be reversed.

        Args:
            new_x (int): New coordination of x after move
            new_y (int): New coordination of y after move
            move_dx (int): Move direction of x coordination 
            move_dy (int): Move direction of y coordination 

        Returns:
            Tuple[int, int]: Returns adjusted x, y positions
        """
        if new_x < 0 or new_x >= self.env.grid_size:
            move_dx *= -1
        if new_y < 0 or new_y >= self.env.grid_size:
            move_dy *= -1
        return move_dx, move_dy
    
    def scan_for_food(self, radius: int) -> List['Food']:
        nearby_food: List['Food'] = []
        for food in self.env.food:
            if abs(self.x - food.x) <= radius and abs(self.y - food.y) <= radius:
                nearby_food.append(food)
        return nearby_food
    
    def consume_food(self, food: 'Food'):
        self.hunger -= 5
        self.env.logger.log(
            f"Consumed food at ({food.x}, {food.y}) and has {self.hunger} hunger",
            entity=self
        )
        self.env.food.remove(food)

    def move_towards(self, food: 'Food') -> Tuple[int, int]:
        # Determine the best move to get closer to the food
        best_move = (0, 0)
        min_distance = self.manhattan_distance_between((self.x, self.y), (food.x, food.y))

        for move in self.move_locations:
            new_x = self.x + move[0]
            new_y = self.y + move[1]
            new_distance = self.manhattan_distance_between((new_x, new_y), (food.x, food.y))

            if new_distance < min_distance:
                min_distance = new_distance
                best_move = move

        return best_move
    
    def remove_rabbit(self) -> None:
        # Remove this rabbit entity from the environment
        if self in self.env.rabbits:
            self.env.rabbits.remove(self)
            self.env.logger.log(f"Rabbit at ({self.x}, {self.y}) died", entity=self)
    
class RabbitFactory(Entity):
    def __init__(self, env: Environment):
        super().__init__(env)
        self.rabbits_per_day = GlobalSettings.settings.rabbits_per_day

    def lifetime(self):
        while True:
            # Calculate the time until the next rabbit is generated using a Poisson distribution
            time_until_next_rabbit = random.expovariate(
                self.rabbits_per_day / GlobalSettings.day_minutes
            )

            yield self.env.simpy_env.timeout(
                time_until_next_rabbit * self.env.time_factor
            )

            x = random.randint(0, self.env.grid_size - 1)
            y = random.randint(0, self.env.grid_size - 1)
            rabbit = Rabbit(self.env, x=x, y=y)
            self.env.add_rabbit(rabbit)

class Food(Entity):
    def __init__(self, env: Environment, x: int, y: int):
        super().__init__(env)
        self.x = x
        self.y = y
        self.lifespan: int = GlobalSettings.settings.food_lifespan
        self.current_lifespan = self.lifespan

    def lifetime(self) -> None:
        while self.current_lifespan > 0:
            try:
                yield self.env.simpy_env.timeout(1 * self.env.time_factor)
                self.current_lifespan -= 1  # Decrease the lifespan after each step
            except simpy.Interrupt:
                # If the food is eaten before the timeout, it gets interrupted
                break  # Exit the loop if food is consumed

        if self.current_lifespan <= 0:
            self.remove_food()  # Call the removal function if lifespan is depleted


    def remove_food(self) -> None:
        # Remove this food entity from the environment
        if self in self.env.food:
            self.env.food.remove(self)
            self.env.logger.log(f"Food at ({self.x}, {self.y}) decayed", entity=self)

class FoodFactory(Entity):
    def __init__(self, env: Environment):
        super().__init__(env)
        # TODO: Modify the rate based on external factors
        self.food_generation_rate = GlobalSettings.settings.base_food_rate

    def lifetime(self) -> None:
        while True:
            # Calculate interval for next food generation
            interval = random.expovariate(self.food_generation_rate / GlobalSettings.day_minutes)

            yield self.env.simpy_env.timeout(interval * self.env.time_factor)

            self.generate_food()

    # TODO: Generate food on empty cells only
    def generate_food(self) -> None:
        # Randomly select a grid cell for food placement
        # empty_cells = [
        #     (x, y) for x in range(self.env.grid_size) for y in range(self.env.grid_size)
        #     if not any(r.x == x and r.y == y for r in self.env.rabbits)
        # ]

        # if empty_cells:
            # x, y = random.choice(empty_cells)
        x = random.randint(0, self.env.grid_size - 1)
        y = random.randint(0, self.env.grid_size - 1)
        self.env.add_food(Food(self.env, x, y))

        self.env.logger.log(f"Generated food at ({x}, {y})", entity=self)