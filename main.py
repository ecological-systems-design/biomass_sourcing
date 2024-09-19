# local import

from src.data.final_results_output import (data_output_potential_grid_level,
                                           data_output_potential_impacts_country_level,
                                           data_output_ghg_contribution,
                                           get_df_combined_potential_impacts_all_scenarios)
from src.data.forest_lci import calculate_forest_occupation_and_transformation
from src.data.agriculture_lci import add_price
from src.bw.bw_base_set_up import bw_set_up, import_ecoinvent_310
from src.bw.bw_scenario_set_up import bw_scenario_set_up

from src.bw.bw_lcia import lcia_crop_contribution, lcia_crop_add_price, lcia_crop_residue_per_kg
from src.visualization.visualization_potential import (stack_plot_by_biomass_type, map_potential,
                                                       bar_plot_methanol_demand,
                                                       bar_plot_potential_top_countries
                                                       )
from src.visualization.visualization_lcia import (impact_distribution_box_log, impact_distribution_box,
                                                  joint_plot, combine_potential_and_impact,
                                                  ghg_contribution_bar_plot_2_cats_4_countries,
                                                  impact_heat_map, impact_trade_off, merit_order_curve_single_country
                                                  )
from src.visualization.visualization_chemical import chemical_climate_change_impact_scenario_bar, biomass_to_chemical_sankey
from src.visualization.visualization_others import plot_carbon_price_and_bioenergy_demand, plot_country_land_use, plot_globiom_region_map, plot_image_region_map
from src.visualization.visualization_lcia_all_scenarios import (bar_plot_ghg_by_year, bar_plot_bdv_by_year,
                                                                bar_plot_ghg_by_year_scenario)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # plot_image_region_map()
    #get_df_combined_potential_impacts_all_scenarios()
    # Data output
    # get_df_combined_potential_impacts_all_scenarios()
    # data_output_potential_impacts_country_level()
    # data_output_potential_grid_level()
    # data_output_ghg_contribution()
    # plot_country_land_use('BR')
    # plot_globiom_region_map()
    '''
    for country in ['CN', 'BR', 'US', 'IN']:
        plot_country_land_use(country)
    '''
    # bw_set_up()
    price = 'normal'  # price = 'normal' / 'min'
    year = 2050  # year = 2020 / 2030 / 2040 / 2050
    scenario = 'scenRCP1p9'# scenario = 'scenRCP1p9' / 'scenRCPref'
    #calculate_forest_occupation_and_transformation(year, scenario)
    bw_scenario_set_up(year, scenario)
    #lcia_crop_add_price(year, scenario, price)
    # df1 = combine_potential_and_impact(year, scenario, price)
    '''
    bar_plot_ghg_by_year_scenario('IN', price)
    bar_plot_ghg_by_year_scenario('IN', 'min')

    for country in ['CN', 'BR', 'US', 'IN']:
        for scenario in ['scenRCPref', 'scenRCP1p9']:
            bw_scenario_set_up(year, scenario)
            plot_country_land_use(country)
            bar_plot_bdv_by_year(scenario, country, price)
            bar_plot_ghg_by_year(scenario, country, price, 0.42)

    # sensitivity, price = 'normal' / 'min'
    for price in ['normal', 'min']:
        for country in ['CN', 'BR', 'US', 'IN']:
            bar_plot_ghg_by_year_scenario(country, price)
    '''
    # Fig. 1, Ex. Fig. 2
    #stack_plot_by_biomass_type()
    #map_potential(year, 'AVAI_MIN')
    #map_potential(year, 'AVAI_MAX')
    #bar_plot_potential_top_countries(year)

    # Fig. 2-3, Ex. Fig. 4-6
    for scenario in ['scenRCP1p9', 'scenRCPref']:
        bw_scenario_set_up(year, scenario)
        #impact_distribution_box_log(year, scenario, 'BDV', price)
        impact_heat_map(year, scenario, 'BDV', price)
        #ghg_contribution_bar_plot_2_cats_4_countries(year, scenario, price)
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
            # plot_country_land_use(country)
            bar_plot_bdv_by_year(scenario, country, price)
            bar_plot_ghg_by_year(scenario, country, price, 0.42)

    # Fig. 6
    # chemical_climate_change_impact_scenario_bar(year, scenario, price)

    # Others (Extended Figures and Supplementary Figures)
    # bar_plot_methanol_demand()
    # joint_plot(year, scenario, price)
    # plot_carbon_price_and_bioenergy_demand()
    # data_output_ghg_contribution()
