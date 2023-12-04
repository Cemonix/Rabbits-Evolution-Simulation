from abc import ABC, abstractmethod
import random
import simpy

from settings_manager import GlobalSettings
from sim_statistics import Logger, Collector

from typing import List, Tuple

class Entity(ABC):
    """
    Abstract base class representing a generic entity in the simulation.

    Attributes:
        env (Environment): The simulation environment instance.
        id (int): Unique identifier for the entity.
    """
    count = 0

    def __init__(self, env: 'Environment'):
        """
        Initialize a new instance of Entity.

        Args:
            env (Environment): The simulation environment this entity belongs to.
        """
        self.env = env
        self.id = Entity.count
        Entity.count += 1
        self.env.simpy_env.process(self.lifetime())

    def __str__(self):
        """
        Provide a string representation of the entity, showing its class name and ID.
        """
        return f"{self.__class__.__name__} : {self.id}"

    @abstractmethod
    def lifetime(self):
        """
        Abstract method to define the entity's behavior over its lifetime.
        """
        raise NotImplemented("Lifetime method is not implemented!")
    
    def manhattan_distance_between(
        self, first: Tuple[int, int], second: Tuple[int, int]
    ) -> int:
        """
        Calculate the Manhattan distance between two points in the simulation grid.

        Args:
            first (Tuple[int, int]): The first point as a (x, y) tuple.
            second (Tuple[int, int]): The second point as a (x, y) tuple.

        Returns:
            int: The Manhattan distance between the two points.
        """
        return abs(first[0] - second[0]) + abs(first[1] - second[1])

class Environment:
    """
    Represents the environment of the simulation, including entities like rabbits and food.

    Attributes:
        env_settings (EnvironmentSettings): General settings for the environment.
        rabbit_settings (RabbitSettings): Settings related to rabbit entities.
        food_settings (FoodSettings): Settings related to food entities.
        time_factor (float): A factor determining the speed of the simulation.
        collector (Collector): The data collector for gathering simulation statistics.
        logger (Logger): Logger for logging simulation events.
        simpy_env (simpy.Environment): The simulation environment from simpy.
        grid_size (int): The size of the grid representing the simulation area.
        rabbits (List[Rabbit]): A list of rabbits currently in the environment.
        food (List[Food]): A list of food sources currently in the environment.
        removed_rabbits (int): Counter for rabbits removed from the environment.
        eaten_food (int): Counter for food consumed by rabbits.
        decayed_food (int): Counter for food that decayed over time.
    """
    def __init__(
        self, grid_size: int, collector: Collector, realtime: bool = True
    ):
        """
        Initialize the simulation environment.

        Args:
            grid_size (int): The size of the grid for the simulation environment.
            collector (Collector): The data collector for the simulation.
            realtime (bool): Whether to run the simulation in real-time mode.
        """
        self.env_settings = GlobalSettings.settings.environment
        self.rabbit_settings = GlobalSettings.settings.rabbit
        self.food_settings = GlobalSettings.settings.food
        
        self.time_factor = self.env_settings.time_factor
        self.collector = collector
        self.logger = Logger(self)
        self.simpy_env = simpy.RealtimeEnvironment(
            self.time_factor, strict=False
        ) if realtime else simpy.Environment()
        self.grid_size: int = grid_size
        self.rabbits: List[Rabbit] = []
        self.food: List[Food] = []
        self.removed_rabbits = 0
        self.eaten_food = 0
        self.decayed_food = 0

    def add_rabbit(self, rabbit: 'Rabbit') -> None:
        """
        Add a rabbit to the simulation environment.

        Args:
            rabbit (Rabbit): The rabbit to be added.
        """
        self.rabbits.append(rabbit)

    def add_food(self, food: 'Food') -> None:
        """
        Add a food source to the simulation environment.

        Args:
            food (Food): The food to be added.
        """
        self.food.append(food)

    def run_simulation(self, sim_duration: int | float) -> None:
        """
        Run the simulation for a specified duration.

        Args:
            sim_duration (int | float): The duration for which to run the simulation.
        """
        self.simpy_env.run(until=sim_duration)

    def is_cell_occupied(self, x: int, y: int) -> bool:
        """
        Check if a cell in the grid is occupied by a rabbit or food.

        Args:
            x (int): The x-coordinate of the cell.
            y (int): The y-coordinate of the cell.

        Returns:
            bool: True if the cell is occupied, False otherwise.
        """
        for entity in self.rabbits + self.food:
            if entity.x == x and entity.y == y:
                return True
        return False

class Rabbit(Entity):
    """
    Represents a rabbit entity in the simulation environment.

    Attributes:
        env (Environment): The simulation environment in which the rabbit exists.
        x (int): The x-coordinate of the rabbit's position.
        y (int): The y-coordinate of the rabbit's position.
        scan_radius (float): The radius within which the rabbit can detect other entities.
        base_hunger (float): The initial hunger level of the rabbit.
        hunger (float): The current hunger level of the rabbit.
        base_hunger_factor (float): The factor that influences the rate at which hunger increases.
        hunger_to_breed (float): The hunger level required for breeding.
        hunger_fatigue (float): The rate at which hunger affects the rabbit's fatigue.
        base_breed_timeout (float): The initial timeout for breeding.
        breeding_reset_speed (float): The speed at which the breeding timeout resets.
        move_locations (List[Tuple[int, int]]): List of possible movement directions.
        breeding_timeout (float): The remaining time until the rabbit can breed again.
        speed (float): The speed at which the rabbit moves.
        age (float): The age of the rabbit in the simulation.
        breeding_count (int): The number of times the rabbit has successfully bred.
        is_alive (bool): Flag indicating if the rabbit is alive.
        moving_towards (bool): Flag indicating if the rabbit is moving towards a target.
        chosen_partner (None or Rabbit): The selected partner for breeding, if any.
        nearest_food (None or Food): The nearest available food source, if any.
    """
    def __init__(
        self, env: Environment, x: int, y: int, 
        scan_radius: float, base_hunger: float, base_hunger_factor: float,
        hunger_fatigue: float, hunger_to_breed: float, base_breed_timeout: float,
        breeding_reset_speed: float, speed: float
    ):
        """
        Initialize a new instance of the Rabbit class.

        Args:
            env (Environment): The simulation environment in which the rabbit exists.
            x (int): The initial x-coordinate of the rabbit's start position.
            y (int): The initial y-coordinate of the rabbit's start position.
            scan_radius (float): The radius within which the rabbit can detect other entities.
            base_hunger (float): The initial hunger level of the rabbit.
            base_hunger_factor (float): The factor that influences the rate at which hunger increases.
            hunger_fatigue (float): The rate at which hunger affects the rabbit's fatigue.
            hunger_to_breed (float): The hunger level required for breeding.
            base_breed_timeout (float): The initial timeout for breeding.
            breeding_reset_speed (float): The speed at which the breeding timeout resets.
            speed (float): The speed at which the rabbit moves within the environment.
        """
        super().__init__(env)
        self.x = x
        self.y = y
        self.scan_radius = scan_radius
        self.base_hunger = base_hunger
        self.hunger = self.base_hunger
        self.base_hunger_factor = base_hunger_factor
        self.hunger_to_breed = hunger_to_breed
        self.hunger_fatigue = hunger_fatigue
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
        """
        Define the behavior of the rabbit over its lifetime in the simulation.
        Includes moving, interacting, updating hunger, and aging.
        """
        while self.is_alive:
            self.x, self.y = self.handle_movement()
            self.handle_interaction()
            self.update_hunger()
            self.age += self.env.simpy_env.now

            yield self.env.simpy_env.timeout(1 * self.env.time_factor)

            self.env.collector.rabbit_collector.update_best_rabbit_stats(self)
            self.env.collector.rabbit_collector.update_current_step_rabbit_stats(self)

    def handle_movement(self) -> Tuple[int, int]:
        """
        Handle the movement of the rabbit based on its current state and conditions.

        If the rabbit is well-fed and not in the middle of breeding, it tries to move towards
        a potential partner to breed. Otherwise, it moves towards the nearest food source.

        If no specific movement is determined, the rabbit makes a random move.

        Returns:
            Tuple[int, int]: A tuple containing the change in x and y coordinates after movement.
        """
        if self.is_fed() and self.breeding_timeout <= 0:
            move_dx, move_dy = self.move_to_breed()
        else:
            if self.breeding_timeout > 0:
                self.breeding_timeout -= self.breeding_reset_speed
            move_dx, move_dy = self.move_towards_food()

        if move_dx == 0 and move_dy == 0:
            move_dx, move_dy = random.choice(self.move_locations)

        move_dx, move_dy = self.adjust_move_if_outside_grid(
            self.x + move_dx, self.y + move_dy, move_dx, move_dy
        )

        return self.x + move_dx, self.y + move_dy

    def move_to_breed(self) -> Tuple[int, int]:
        """
        Determine the movement direction to approach a potential partner for breeding.

        This method checks for potential breeding partners within the rabbit's scan radius,
        chooses a partner if one is available and suitable for breeding, and calculates
        the movement direction to get closer to the chosen partner.

        Returns:
            Tuple[int, int]: A tuple containing the change in x and y coordinates for movement.
        """
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
        """
        Determine the movement direction to approach the nearest food source.

        This method checks for nearby food sources within the rabbit's scan radius,
        selects the nearest one, and calculates the movement direction to get closer to it.
        It also logs the rabbit's intent to move towards the food source if not already moving.

        Returns:
            Tuple[int, int]: A tuple containing the change in x and y coordinates for movement.
        """
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
        """
        Handle interactions between the rabbit and its surroundings.

        If the rabbit is currently moving towards a potential partner or food source,
        this method checks whether the rabbit has reached the partner or food. If it has,
        it initiates the corresponding action: starting the breeding process or consuming food.
        Additionally, it updates the `moving_towards` flag to indicate whether the rabbit
        is still in the process of moving towards its target.
        """
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
        """
        Check if the rabbit has reached a specific entity's position.

        Args:
            entity_x (int): The x-coordinate of the target entity's position.
            entity_y (int): The y-coordinate of the target entity's position.

        Returns:
            bool: True if the rabbit's current position matches the target entity's position,
                  indicating that the rabbit has reached the entity; False otherwise.
        """
        return (self.x, self.y) == (entity_x, entity_y)
        
    def start_breeding_process(self):
        """
        Initiate the breeding process for the rabbit.

        This method logs the event of the rabbit starting to breed at its current position.
        It then calls the `breed` method to perform the actual breeding process with the chosen partner.
        After breeding, it resets the `chosen_partner` attribute to None.
        """
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
        """
        Find the best move to get closer to a target position.

        This method calculates the best move (direction) for the rabbit to take in order to get closer
        to the specified target position (other_x, other_y). It considers the current position
        of the rabbit, the speed at which it can move, and the available move directions.

        Args:
            other_x (int): The x-coordinate of the target position.
            other_y (int): The y-coordinate of the target position.

        Returns:
            Tuple[int, int]: A tuple representing the best move direction as (move_dx, move_dy).
                The rabbit will move in this direction to get closer to the target position.
        """
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
        """
        Find nearby food sources within the rabbit's scan radius.

        This method scans the environment for food sources and returns a list of food sources
        that are within the rabbit's scan radius. It checks the distance between the rabbit's
        current position and the positions of food sources to determine if they are within range.

        Returns:
            List['Food']: A list of nearby food sources that
                the rabbit can see within its scan radius.
        """
        nearby_food: List['Food'] = []
        for food in self.env.food:
            if (
                abs(self.x - food.x) <= self.scan_radius and
                abs(self.y - food.y) <= self.scan_radius
            ):
                nearby_food.append(food)
        return nearby_food
    
    def choose_food(self, nearby_food: List['Food']) -> 'Food':
        """
        Choose the nearest food source from a list of nearby food sources.

        This method takes a list of nearby food sources and selects the nearest one based on
        Manhattan distance from the rabbit's current position. The nearest food source is
        returned as the chosen food source.

        Args:
            nearby_food (List['Food']): A list of nearby food sources.

        Returns:
            'Food': The nearest food source from the list.
        """
        nearest_food: Food = min(
            nearby_food,
            key=lambda food: self.manhattan_distance_between(
                (self.x, self.y), (food.x, food.y)
            )
        )
        return nearest_food

    def consume_food(self, food: 'Food'):
        """
        Consume a food source, reduce hunger, and remove it from the environment.

        Args:
            food ('Food'): The food source to be consumed.
        """
        self.hunger -= food.nutrition
        self.env.food.remove(food)
        self.nearest_food = None
        self.env.eaten_food += 1 
        self.env.logger.log(
            f"Consumed food at ({food.x}, {food.y}) and has {self.hunger} hunger",
            entity=self
        )

    def update_hunger(self) -> None:
        """
        Update the rabbit's hunger level and remove it if it reaches fatigue.
        """
        self.hunger += self.base_hunger_factor
        if self.hunger >= self.hunger_fatigue:
            self.remove_rabbit()
    
    def remove_rabbit(self) -> None:
        """
        Remove the rabbit from the environment if it reaches starvation.

        This method removes the rabbit instance from the list of rabbits in the environment
        when its hunger level exceeds or equals the hunger fatigue threshold. It also updates
        the counters for removed rabbits and logs the event of the rabbit's death.

        Note:
            This method sets the `is_alive` attribute to False to mark the rabbit as deceased.

        """
        if self in self.env.rabbits:
            self.env.rabbits.remove(self)
            self.is_alive = False
            self.env.removed_rabbits += 1
            self.env.logger.log(f"Rabbit at ({self.x}, {self.y}) died", entity=self)
    
    def find_potential_partners(self) -> List['Rabbit']:
        """
        Find potential breeding partners for the rabbit within its scan radius.

        Returns:
            List['Rabbit']: A list of potential breeding partners for the rabbit.
        """
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
        """
        Choose a suitable breeding partner from a list of potential partners.

        This method iterates through the list of potential breeding partners and selects
        the first rabbit that satisfies the conditions for breeding, as determined by the
        `can_breed_with` method. If no suitable partner is found, it returns None.

        Args:
            potential_partners (List['Rabbit']): A list of potential breeding partners.

        Returns:
            'Rabbit' | None: The selected breeding partner or None if no suitable partner
            is found.
        """
        # TODO: Choose rabbit with best stats
        for rabbit in potential_partners:
            if self.can_breed_with(rabbit):
                return rabbit
        return None

    def can_breed_with(self, partner: 'Rabbit') -> bool:
        """
        Check if the rabbit can breed with a potential partner.

        This method checks if the rabbit can breed with a given partner based on specific
        conditions, including whether the partner is sufficiently fed and whether its
        breeding timeout has expired.

        Args:
            partner ('Rabbit'): The potential breeding partner.

        Returns:
            bool: True if the rabbit can breed with the partner, False otherwise.
        """
        if partner.is_fed() and partner.breeding_timeout <= 0:
            return True
        return False

    def is_fed(self) -> bool:
        """
        Determine whether the rabbit is sufficiently fed to breed.

        Returns:
            bool: True if the rabbit's hunger is below the threshold to breed, False
            otherwise.
        """
        return self.hunger <= self.hunger_to_breed
    
    def breed(self, partner: 'Rabbit') -> None:
        """
        Initiate the breeding process between two rabbits.

        This method represents the breeding process between two rabbits. It calculates
        breeding timeouts for both the current rabbit and its partner, and then creates
        a new rabbit offspring with inherited and possibly mutated traits. The new rabbit
        is added to the environment.

        Args:
            partner ('Rabbit'): The breeding partner rabbit.
        """
        self.breeding_timeout = self.calculate_breeding_timeout()  
        partner.breeding_timeout = partner.calculate_breeding_timeout()

        self.env.add_rabbit(
            Rabbit(
                self.env, self.x, self.y,
                self.inherit_with_mutation(
                    self.scan_radius, partner.scan_radius
                ),
                self.inherit_with_mutation(
                    self.base_hunger, partner.base_hunger
                ),
                self.inherit_with_mutation(
                    self.base_hunger_factor, partner.base_hunger_factor
                ),
                self.inherit_with_mutation(
                    self.hunger_fatigue, partner.hunger_fatigue
                ),
                self.inherit_with_mutation(
                    self.hunger_to_breed, partner.hunger_to_breed
                ),
                self.inherit_with_mutation(
                    self.base_breed_timeout, partner.base_breed_timeout
                ),
                self.inherit_with_mutation(
                    self.breeding_reset_speed, partner.breeding_reset_speed
                ),
                GlobalSettings.settings.rabbit.base_speed
            )
        )
    
        self.breeding_count += 1

    def calculate_breeding_timeout(self) -> int:
        """
        Calculate the breeding timeout for a rabbit.

        The breeding timeout is determined by the rabbit's hunger level, where a well-fed
        rabbit has a shorter timeout. This method calculates the breeding timeout based on
        the rabbit's current hunger.

        Returns:
            int: The calculated breeding timeout.
        """
        # Convert hunger to a positive number
        hunger_bonus = max(0, -self.hunger)

        # Reduce the timeout based on how well the rabbit is fed.
        # More negative hunger (well-fed) means a smaller timeout.
        timeout_reduction = max(0, hunger_bonus // 2)

        return self.base_breed_timeout - timeout_reduction
    
    def inherit_with_mutation(self, first_trait: float, second_trait: float) -> float:
        """
        Inherit a trait from two parent rabbits with possible mutation.

        This method calculates the inherited trait value from two parent rabbits
        and introduces a random mutation. The mutation can be positive or negative
        and is based on a percentage of the inherited trait.

        Args:
            first_trait (float): The trait value from the first parent.
            second_trait (float): The trait value from the second parent.

        Returns:
            float: The inherited trait value with mutation.
        """
        inherited_trait = (first_trait + second_trait) / 2

        mutation = random.uniform(-0.1 * inherited_trait, 0.1 * inherited_trait)
        return inherited_trait + mutation

class RabbitFactory(Entity):
    """
    A class representing a Rabbit Factory responsible for generating and managing rabbits.

    Attributes:
        rabbits_per_day (float): The rate of rabbit generation per day.
        generate_new (bool): A flag indicating whether to continue generating new rabbits.
    """
    def __init__(self, env: Environment):
        """
        Initializes the RabbitFactory instance with the provided environment.
        It also generates an initial population of rabbits based on the specified settings.

        Args:
            env (Environment): The environment in which the RabbitFactory operates.
        """
        super().__init__(env)
        self.rabbits_per_day = self.env.rabbit_settings.rate
        self.generate_new = self.env.rabbit_settings.generate_new
        for _ in range(self.env.rabbit_settings.start_rabbits_count):
            self.generate_rabbit()

    def lifetime(self) -> None:
        """
        Generate rabbits over the lifetime of the RabbitFactory.

        This method runs in an infinite loop and generates new rabbits based on the specified
        generation rate. It uses a Poisson distribution to calculate the time until the next rabbit
        is generated and yields a timeout event to simulate the passage of time. After the timeout,
        a new rabbit is generated.

        Yields:
            simpy.events.Timeout: A timeout event representing the time until the next rabbit
            generation.

        Continues to generate rabbits as long as the `generate_new` flag is set to True.
        """
        while self.generate_new:
            time_until_next_rabbit = random.expovariate(
                self.rabbits_per_day / GlobalSettings.day_minutes
            )

            yield self.env.simpy_env.timeout(
                time_until_next_rabbit * self.env.time_factor
            )

            self.generate_rabbit()

    def generate_rabbit(self) -> None:
        """
        This method generates a new rabbit entity and places it in a random unoccupied grid cell
        within the environment. It ensures that the chosen grid cell is not already occupied by
        another rabbit.

        The attributes of the new rabbit are initialized based on the settings specified in the
        environment's rabbit configuration.
        """
        while True:
            x = random.randint(0, self.env.grid_size - 1)
            y = random.randint(0, self.env.grid_size - 1)

            if not self.env.is_cell_occupied(x, y):
                break

        self.env.add_rabbit(
            Rabbit(
                self.env, x, y, 
                self.env.rabbit_settings.scan_radius, 
                self.env.rabbit_settings.base_hunger,
                self.env.rabbit_settings.base_hunger_factor,
                self.env.rabbit_settings.hunger_fatigue,
                self.env.rabbit_settings.hunger_to_breed,
                self.env.rabbit_settings.base_breed_timeout,
                self.env.rabbit_settings.breeding_reset_speed,
                self.env.rabbit_settings.base_speed
            )
        )

class Food(Entity):
    """
    Represents a source of food within the environment that can be consumed by entities.

    Attributes:
        x (int): The x-coordinate of the Food's position in the grid.
        y (int): The y-coordinate of the Food's position in the grid.
        nutrition (float): The nutritional value of the Food.
        lifespan (int): The lifespan of the Food, representing how long it remains
            available for consumption.
        current_lifespan (int): The remaining lifespan of the Food.
        decayed (bool): A flag indicating whether the Food has decayed or not.
    """
    def __init__(
        self, env: Environment, x: int, y: int, nutrition: float, lifespan: int
    ):
        """
        Initialize a Food entity.

        Args:
            env (Environment): The environment in which the Food entity exists.
            x (int): The x-coordinate of the Food's position in the grid.
            y (int): The y-coordinate of the Food's position in the grid.
            nutrition (float): The nutritional value of the Food.
            lifespan (int): The lifespan of the Food, representing how long it remains
                available for consumption.
        """
        super().__init__(env)
        self.x = x
        self.y = y
        self.nutrition = nutrition
        self.lifespan = lifespan
        self.current_lifespan = self.lifespan
        self.decayed = False

    def lifetime(self) -> None:
        """
        Simulates the lifespan of the Food entity, during which it can be consumed.

        This method uses SimPy's timeout mechanism to decrement the current lifespan of the Food
        over time. It also checks for a midpoint in the lifespan to decrease the nutrition value
        if it has not decayed already.

        When the current lifespan reaches zero, the Food entity is removed from the environment
        by calling the `remove_decayed_food` method.

        Yields:
            simpy.events.Timeout: Yields control back to the simulation environment when
            the Food's lifespan expires or it is consumed.
        """
        while self.current_lifespan > 0:
            try:
                yield self.env.simpy_env.timeout(1 * self.env.time_factor)
                # Decrease the nutrition when on half lifespan
                if self.current_lifespan <= self.lifespan / 2 and not self.decayed:
                    self.decayed = True
                    self.nutrition /= 2

                self.current_lifespan -= 1
            except simpy.Interrupt:
                # If the food is eaten before the timeout, it gets interrupted
                break

        if self.current_lifespan <= 0:
            self.remove_decayed_food()

    def remove_decayed_food(self) -> None:
        """
        Removes a decayed Food entity from the environment.

        The method also logs a message indicating that the Food has decayed.
        """
        if self in self.env.food:
            self.env.food.remove(self)
            self.env.decayed_food += 1
            self.env.logger.log(f"Food at ({self.x}, {self.y}) decayed", entity=self)

class FoodFactory(Entity):
    """
    A class representing a Food Factory responsible for generating and managing food.

    Args:
        env (Environment): The environment in which the food item exists.
        x (int): The x-coordinate of the food's position in the grid.
        y (int): The y-coordinate of the food's position in the grid.
        nutrition (float): The initial nutrition value of the food item.
        lifespan (int): The total lifespan of the food item in time units.
    """
    def __init__(self, env: Environment):
        super().__init__(env)
        # TODO: Modify the rate based on external factors
        self.food_generation_rate = self.env.food_settings.rate
        self.generate_new = self.env.food_settings.generate_new
        for _ in range(self.env.food_settings.start_food_count):
            self.generate_food()

    def lifetime(self) -> None:
        """
        Generate food at random intervals within the environment.

        This method uses an exponential distribution to calculate the time
        until the next food item is generated. It yields a timeout event
        for generating food, and when that timeout expires, it generates
        a new food item in an unoccupied cell within the environment.

        Yields:
            simpy.events.Timeout: Yields indefinitely as long as `generate_new` is True.
        """
        while self.generate_new:
            interval = random.expovariate(self.food_generation_rate / GlobalSettings.day_minutes)

            yield self.env.simpy_env.timeout(interval * self.env.time_factor)

            self.generate_food()

    def generate_food(self) -> None:
        """
        Generate a new food item and add it to the environment.

        This method generates a new food item at a random location within
        the environment grid, ensuring that the chosen cell is unoccupied.
        The nutrition value of the food item is randomly determined within
        the range defined by `min_nutrition` and `max_nutrition` in the
        environment's food settings.

        After generating the food item, it is added to the environment's
        list of food items, and a log entry is created to record the
        generation event.
        """
        while True:
            x = random.randint(0, self.env.grid_size - 1)
            y = random.randint(0, self.env.grid_size - 1)

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