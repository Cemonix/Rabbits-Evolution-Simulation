from abc import ABC, abstractmethod
import random
import simpy

from settings_manager import GlobalSettings
from sim_statistics import Logger, Collector

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

class Environment:
    def __init__(
        self, grid_size: int, realtime: bool = True
    ):
        self.rabbit_settings = GlobalSettings.settings.rabbit
        self.food_settings = GlobalSettings.settings.food
        self.env_settings = GlobalSettings.settings.environment
        
        self.time_factor = self.env_settings.time_factor
        self.simpy_env = simpy.RealtimeEnvironment(
            self.time_factor, strict=False
        ) if realtime else simpy.Environment()
        self.grid_size: int = grid_size
        self.logger = Logger(self)
        self.collector = Collector()
        self.rabbits: List[Rabbit] = []
        self.food: List[Food] = []
        self.removed_rabbits = 0
        self.removed_food = 0

    def add_rabbit(self, rabbit: 'Rabbit') -> None:
        self.rabbits.append(rabbit)

    def add_food(self, food: 'Food') -> None:
        self.food.append(food)

    def run_simulation(self, sim_duration: int | float) -> None:
        self.simpy_env.run(until=sim_duration)

    def is_cell_occupied(self, x: int, y: int) -> bool:
        # Determine if the cell at (x, y) is occupied by any entity
        for entity in self.rabbits + self.food:
            if entity.x == x and entity.y == y:
                return True
        return False

class Rabbit(Entity):
    def __init__(
        self, env: Environment, x: int, y: int, 
        scan_radius: float, hunger: float, base_hunger_factor: float,
        hunger_fatique: float, hunger_to_breed: float, base_breed_timeout: float,
        breeding_reset_speed: float, speed: float
    ):
        super().__init__(env)
        self.x = x
        self.y = y
        self.scan_radius = scan_radius
        self.hunger = hunger
        self.base_hunger_factor = base_hunger_factor
        self.hunger_to_breed = hunger_to_breed
        self.hunger_fatique = hunger_fatique
        self.base_breed_timeout = base_breed_timeout
        self.breeding_reset_speed = breeding_reset_speed
        self.move_locations: List[Tuple[int, int]] = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (-1, -1), (1, -1), (-1, 1)
        ]
        self.breeding_timeout = 0
        self.speed = speed
        self.age = self.env.simpy_env.now
        self.breeding_count = 0
        self.is_alive = True
        self.moving_towards = False
        self.chosen_partner = None
        self.nearest_food = None

    def lifetime(self) -> None:
        while self.is_alive:
            self.x, self.y = self.handle_movement()
            self.handle_interaction()
            self.update_hunger()
            self.age += self.env.simpy_env.now

            yield self.env.simpy_env.timeout(1 * self.env.time_factor)

            self.env.collector.rabbit_collector.collect(self)

    def handle_movement(self) -> Tuple[int, int]:
        if self.is_fed() and self.breeding_timeout <= 0:
            move_dx, move_dy = self.move_to_breed()
        else:
            if self.breeding_timeout > 0:
                self.base_breed_timeout -= self.breeding_reset_speed
            move_dx, move_dy = self.move_towards_food()

        if move_dx == 0 and move_dy == 0:
            move_dx, move_dy = random.choice(self.move_locations)

        move_dx, move_dy = self.adjust_move_if_outside_grid(
            self.x + move_dx, self.y + move_dy, move_dx, move_dy
        )

        return self.x + move_dx, self.y + move_dy
        # self.env.logger.log(f"Moved randomly to ({self.x}, {self.y})", entity=self)

    def move_to_breed(self) -> Tuple[int, int]:
        move_dx, move_dy = (0, 0)
        if potential_partners := self.find_potential_partners():
            chosen_partner = self.choose_partner(potential_partners)
            if chosen_partner and self.can_breed_with(chosen_partner):
                self.chosen_partner = chosen_partner
                move_dx, move_dy = self.find_best_move_towards(
                    self.chosen_partner.x, self.chosen_partner.y
                )

        return move_dx, move_dy

    def move_towards_food(self) -> Tuple[int, int]:
        move_dx, move_dy = (0, 0)
        self.nearest_food = None
        if nearby_food := self.find_food():
            # Find nearest food based on manhatten distance
            self.nearest_food = self.choose_food(nearby_food)

            if not self.moving_towards:
                self.env.logger.log(
                    f"Moving towards food at ({self.nearest_food.x}, {self.nearest_food.y})",
                    entity=self
                )
            move_dx, move_dy = self.find_best_move_towards(
                self.nearest_food.x, self.nearest_food.y
            )
        return move_dx, move_dy
    
    def handle_interaction(self):
        if self.moving_towards:
            if (
                self.chosen_partner and
                self.reached_entity(self.chosen_partner.x, self.chosen_partner.y)
            ):
                self.start_breeding_process()
                self.moving_towards = False
            elif ( 
                self.nearest_food and
                self.reached_entity(self.nearest_food.x, self.nearest_food.y)
            ):
                self.consume_food(self.nearest_food)
                self.moving_towards = False

    def reached_entity(self, entity_x: int, entity_y: int) -> bool:
        # Check if the rabbit has reached entity
        return (self.x, self.y) == (entity_x, entity_y)
        
    def start_breeding_process(self):
        self.env.logger.log(
            f"Rabbit starts breeding at ({self.x}, {self.y})", entity=self
        )

        self.breed(self.chosen_partner)
        self.chosen_partner = None

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
    
    def find_best_move_towards(self, other_x: int, other_y: int) -> Tuple[int, int]:
        # Determine the best move to get closer to the food
        self.moving_towards = True
        best_move = (0, 0)
        min_distance = self.manhattan_distance_between(
            (self.x, self.y), (other_x, other_y)
        )

        for move in self.move_locations:
            new_x = self.x + move[0] * self.speed
            new_y = self.y + move[1] * self.speed
            new_distance = self.manhattan_distance_between(
                (new_x, new_y), (other_x, other_y)
            )

            if new_distance < min_distance:
                min_distance = new_distance
                best_move = move

        return best_move
    
    def find_food(self) -> List['Food']:
        nearby_food: List['Food'] = []
        for food in self.env.food:
            if (
                abs(self.x - food.x) <= self.scan_radius and
                abs(self.y - food.y) <= self.scan_radius
            ):
                nearby_food.append(food)
        return nearby_food
    
    def choose_food(self, nearby_food: List['Food']) -> 'Food':
        nearest_food: Food = min(
            nearby_food,
            key=lambda food: self.manhattan_distance_between(
                (self.x, self.y), (food.x, food.y)
            )
        )
        return nearest_food

    def consume_food(self, food: 'Food'):
        self.hunger -= food.nutrition
        self.env.food.remove(food)
        self.nearest_food = None
        self.env.removed_food += 1 
        self.env.logger.log(
            f"Consumed food at ({food.x}, {food.y}) and has {self.hunger} hunger",
            entity=self
        )

    def update_hunger(self) -> None:
        self.hunger += self.base_hunger_factor
        if self.hunger >= self.hunger_fatique:
            self.remove_rabbit()
    
    def remove_rabbit(self) -> None:
        # Remove this rabbit from the environment
        if self in self.env.rabbits:
            self.env.rabbits.remove(self)
            self.is_alive = False
            self.env.removed_rabbits += 1
            self.env.logger.log(f"Rabbit at ({self.x}, {self.y}) died", entity=self)
    
    def find_potential_partners(self) -> List['Rabbit']:
        potential_partners: List['Rabbit'] = []
        for potential_partner in self.env.rabbits:
            if (
                self is not potential_partner and
                abs(self.x - potential_partner.x) <= self.scan_radius and
                abs(self.y - potential_partner.y) <= self.scan_radius
            ):
                potential_partners.append(potential_partner)
        return potential_partners

    def choose_partner(self, potential_partners: List['Rabbit']) -> 'Rabbit':
        # TODO: Choose rabbit with best stats
        for rabbit in potential_partners:
            if self.can_breed_with(rabbit):
                return rabbit
        return None  # Return None if no suitable partner is found

    def can_breed_with(self, partner: 'Rabbit') -> bool:
        # Check conditions for breeding
        if partner.is_fed() and partner.breeding_timeout <= 0:
            return True
        return False

    def is_fed(self) -> bool:
        return self.hunger <= self.hunger_to_breed
    
    def breed(self, partner: 'Rabbit'):
        # Set a timeout before the rabbit can move/breed again
        self.breeding_timeout = self.calculate_breeding_timeout()  
        partner.breeding_timeout = partner.calculate_breeding_timeout()

        # Spawn a new rabbit at the parents' location
        self.env.add_rabbit(
            Rabbit(
                self.env, self.x, self.y, 
                self.env.rabbit_settings.scan_radius, 
                self.env.rabbit_settings.base_hunger,
                self.env.rabbit_settings.base_hunger_factor,
                self.env.rabbit_settings.hunger_fatique,
                self.env.rabbit_settings.hunger_to_breed,
                self.env.rabbit_settings.base_breed_timeout,
                self.env.rabbit_settings.breeding_reset_speed,
                self.env.rabbit_settings.base_speed
            )
        )

        self.breeding_count += 1

    def calculate_breeding_timeout(self) -> int:
        # Convert hunger to a positive number
        hunger_bonus = max(0, -self.hunger)

        # Reduce the timeout based on how well the rabbit is fed.
        # More negative hunger (well-fed) means a smaller timeout.
        timeout_reduction = max(0, hunger_bonus // 2)

        return self.base_breed_timeout - timeout_reduction
    
class RabbitFactory(Entity):
    def __init__(self, env: Environment):
        super().__init__(env)
        self.rabbits_per_day = self.env.rabbit_settings.rate
        self.generate_new = self.env.rabbit_settings.generate_new
        for _ in range(self.env.rabbit_settings.start_rabbits_count):
            self.generate_rabbit()

    def lifetime(self):
        while True and self.generate_new:
            # Calculate the time until the next rabbit is generated using a Poisson distribution
            time_until_next_rabbit = random.expovariate(
                self.rabbits_per_day / GlobalSettings.day_minutes
            )

            yield self.env.simpy_env.timeout(
                time_until_next_rabbit * self.env.time_factor
            )

            self.generate_rabbit()

    def generate_rabbit(self) -> None:
        while True:
            # Randomly select a grid cell for rabbit placement
            x = random.randint(0, self.env.grid_size - 1)
            y = random.randint(0, self.env.grid_size - 1)

            # Check if the cell is empty
            if not self.env.is_cell_occupied(x, y):
                break

        self.env.add_rabbit(
            Rabbit(
                self.env, x, y, 
                self.env.rabbit_settings.scan_radius, 
                self.env.rabbit_settings.base_hunger,
                self.env.rabbit_settings.base_hunger_factor,
                self.env.rabbit_settings.hunger_fatique,
                self.env.rabbit_settings.hunger_to_breed,
                self.env.rabbit_settings.base_breed_timeout,
                self.env.rabbit_settings.breeding_reset_speed,
                self.env.rabbit_settings.base_speed
            )
        )

class Food(Entity):
    def __init__(
        self, env: Environment, x: int, y: int, nutrition: float, lifespan: int
    ):
        super().__init__(env)
        self.x = x
        self.y = y
        self.nutrition = nutrition
        self.lifespan = lifespan
        self.current_lifespan = self.lifespan
        self.decayed = False

    def lifetime(self) -> None:
        while self.current_lifespan > 0:
            try:
                yield self.env.simpy_env.timeout(1 * self.env.time_factor)
                # Decrease the nutrition when on half lifespan
                if self.current_lifespan <= self.lifespan / 2 and not self.decayed:
                    self.decayed = True
                    self.nutrition /= 2
                # Decrease the lifespan after each step
                self.current_lifespan -= 1
            except simpy.Interrupt:
                # If the food is eaten before the timeout, it gets interrupted
                break  # Exit the loop if food is consumed

        if self.current_lifespan <= 0:
            self.remove_decayed_food()  # Call the removal function if lifespan is depleted

    def remove_decayed_food(self) -> None:
        # Remove this food from the environment
        if self in self.env.food:
            self.env.food.remove(self)
            self.env.removed_food += 1
            self.env.logger.log(f"Food at ({self.x}, {self.y}) decayed", entity=self)

class FoodFactory(Entity):
    def __init__(self, env: Environment):
        super().__init__(env)
        # TODO: Modify the rate based on external factors
        self.food_generation_rate = self.env.food_settings.rate
        self.generate_new = self.env.food_settings.generate_new
        for _ in range(self.env.food_settings.start_food_count):
            self.generate_food()

    def lifetime(self) -> None:
        while True and self.generate_new:
            # Calculate interval for next food generation
            interval = random.expovariate(self.food_generation_rate / GlobalSettings.day_minutes)

            yield self.env.simpy_env.timeout(interval * self.env.time_factor)

            self.generate_food()

    # TODO: Generate food on empty cells only
    def generate_food(self) -> None:
        while True:
            # Randomly select a grid cell for food placement
            x = random.randint(0, self.env.grid_size - 1)
            y = random.randint(0, self.env.grid_size - 1)

            # Check if the cell is empty
            if not self.env.is_cell_occupied(x, y):
                break
        
        nutrition = random.uniform(
            self.env.food_settings.min_nutrition,
            self.env.food_settings.max_nutrition
        )
        self.env.add_food(
            Food(
                self.env, x, y, nutrition,
                self.env.food_settings.lifespan
            )
        )

        self.env.logger.log(
            f"Generated food at ({x}, {y}) with {nutrition} nutrition", entity=self
        )
 