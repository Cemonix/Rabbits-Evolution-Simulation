from settings_manager import GlobalSettings
from sim_essentials import Environment, RabbitFactory, FoodFactory
from sim_statistics import Collector, StatisticsVisualization
from visualization import SimulationVisualization

if __name__ == "__main__":
    GlobalSettings.load_settings("simulation_settings.json")
    settings = GlobalSettings.settings

    grid_size = settings.environment.grid_size
    sim_width = settings.environment.win_width
    sim_height = settings.environment.win_height

    collector = Collector()
    env = Environment(grid_size, collector)
    visualization = SimulationVisualization(env)
    RabbitFactory(env)
    FoodFactory(env)

    visualization.run(GlobalSettings.day_minutes * settings.environment.time_factor)

    stats_visualization = StatisticsVisualization(collector)
    stats_visualization.plot_environment_data(save_path="statistics/env_stats.png")
    stats_visualization.display_rabbit_stats()