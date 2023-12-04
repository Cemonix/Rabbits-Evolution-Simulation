# Rabbits Evolution Simulation

<p align="center">
    <img src="images/Logo.png" />
</p>

## Overview

This project is a simulation of rabbit evolution in a simpy environment. It models the behavior of rabbits as they search for food, breed, and evolve over time. The simulation aims to explore how various attributes of rabbits, such as hunger, scan_radius, and breeding behavior, impact their survival and reproduction rates.

## Features

- **Rabbit Behavior**: The simulation models the behavior of individual rabbits, including movement, feeding, and breeding.

- **Evolution**: Over time, rabbits with favorable attributes (e.g., low hunger) have a better chance of surviving and reproducing, leading to the evolution of the rabbit population.

- **Data Collection**: The simulation collects and displays data on rabbit population dynamics, environmental factors, and individual rabbit statistics.

- **Visualization**: It provides a graphical visualization of the simulated environment, including rabbits, food, and their interactions.

## Getting Started

To run the simulation, follow these steps:

1. Clone the repository: `git clone https://github.com/Cemonix/Rabbits-Evolution-Simulation`

2. Change to the project directory: `cd Rabbits-Evolution-Simulation`

3. Install Poetry (if not already installed): [Poetry Installation Guide](https://python-poetry.org/docs/#installation)

4. Install project dependencies: `poetry install`

5. Configure simulation settings: Modify the configuration file located in the `config` directory to adjust simulation parameters, such as rabbit attributes, food generation rates, and environment size.

6. Run the simulation: Execute the main simulation script using Poetry: `poetry run python main.py`

## Configuration

The simulation can be customized by editing the configuration `simulation_settings` file located in the `config` directory:

- `environment_settings`: Configure environment-related settings such as grid size, window dimensions, path to sprites, and time factor.

- `rabbit_settings`: Configure rabbit attributes such as hunger, speed, and breeding behavior.

- `food_settings`: Adjust food-related settings, including nutrition levels and food generation rates.

## Results

After running the simulation, you can analyze the collected data and visualize the evolution of the rabbit population. Use the provided tools to generate graphs and statistics to better understand the simulation outcomes.
