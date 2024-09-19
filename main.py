# local import

from src.bw.bw_base_set_up import bw_set_up
from src.bw.bw_scenario_set_up import bw_scenario_set_up
from src.data.final_results_output import data_output_ghg_contribution
from src.visualization.visualization_chemical import chemical_climate_change_impact_scenario_bar
from src.visualization.visualization_lcia import (impact_distribution_box_log, impact_distribution_box,
                                                  joint_plot, ghg_contribution_bar_plot_2_cats_4_countries,
                                                  impact_heat_map, impact_trade_off, merit_order_curve_single_country
                                                  )
from src.visualization.visualization_lcia_all_scenarios import (bar_plot_ghg_by_year, bar_plot_bdv_by_year)
from src.visualization.visualization_others import (plot_carbon_price_and_bioenergy_demand, plot_country_land_use, \
                                                    plot_globiom_region_map, plot_image_region_map)
from src.visualization.visualization_potential import (stack_plot_by_biomass_type, map_potential,
                                                       bar_plot_methanol_demand,
                                                       bar_plot_potential_top_countries
                                                       )

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    bw_set_up()
    price = 'normal'  # price = 'normal' / 'min'
    year = 2050  # year = 2020 / 2030 / 2040 / 2050
    scenario = 'scenRCP1p9'# scenario = 'scenRCP1p9' / 'scenRCPref'

    # Fig. 1, Ex. Fig. 2
    stack_plot_by_biomass_type()
    map_potential(year, 'AVAI_MIN')
    map_potential(year, 'AVAI_MAX')
    bar_plot_potential_top_countries(year)

    # Fig. 2, Ex. Fig. 4-6
    for scenario in ['scenRCP1p9', 'scenRCPref']:
        bw_scenario_set_up(year, scenario)
        ghg_contribution_bar_plot_2_cats_4_countries(year, scenario, price)
        for impact in ['WATER', 'GHG', 'BDV', 'GTP']:
            impact_heat_map(year, scenario, impact, price)
        impact_distribution_box(year, scenario, 'GHG', price)
        impact_distribution_box(year, scenario, 'GTP', price)
        impact_distribution_box_log(year, scenario, 'WATER', price)
        impact_distribution_box_log(year, scenario, 'BDV', price)

    # Fig. 5
    for scenario in ['scenRCPref', 'scenRCP1p9']:
        bw_scenario_set_up(year, scenario)
        impact_trade_off(year, scenario, price)
        for country in ['CN', 'BR', 'US', 'IN']:
            for impact in ['WATER', 'GHG', 'BDV']:
                merit_order_curve_single_country(year, scenario, country, impact, price)

    # Fig. 4, Ex. Fig. 6
    for scenario in ['scenRCPref', 'scenRCP1p9']:
        bw_scenario_set_up(year, scenario)
        for country in ['CN', 'BR', 'US', 'IN']:
            plot_country_land_use(country)
            bar_plot_bdv_by_year(scenario, country, price)
            bar_plot_ghg_by_year(scenario, country, price, 0.42)

    # Fig. 6
    chemical_climate_change_impact_scenario_bar(year, scenario, price)

    # Others (Extended Figures and Supplementary Figures)
    bar_plot_methanol_demand()
    joint_plot(year, scenario, price)
    plot_carbon_price_and_bioenergy_demand()
    data_output_ghg_contribution()
    plot_globiom_region_map()
    plot_image_region_map()


