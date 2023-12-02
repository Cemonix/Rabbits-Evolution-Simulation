from settings_manager import GlobalSettings
from sim_essentials import Environment, RabbitFactory, FoodFactory
from visualization import SimulationVisualization

if __name__ == "__main__":
    GlobalSettings.load_settings("simulation_settings.json")
    settings = GlobalSettings.settings

    grid_size = settings.grid_size
    sim_width = settings.win_width
    sim_height = settings.win_height

    env = Environment(grid_size)
    visualization = SimulationVisualization(env)
    RabbitFactory(env)
    FoodFactory(env)

    visualization.run(GlobalSettings.day_minutes * settings.time_factor)