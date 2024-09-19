from src.data.globiom_residue_potential import all_residue_potential_g, all_residue_available_potential_g_no_scenario
from src.other.name_match import get_country_match_df_globiom
from src.visualization.visualization_lcia import lcia_crop_add_price, combine_potential_and_impact, ghg_contribution_df
from src.bw.bw_scenario_set_up import bw_scenario_set_up

import pandas as pd
import os


def data_output_potential_grid_level():
    df = all_residue_available_potential_g_no_scenario()
    df = df[df.YEAR <= 2050].copy()
    # df = all_residue_potential_g()
    df.loc[df.CAT1 == 'Forestry', 'CAT1'] = 'Forest'
    df.loc[df.CAT2.str.contains('harvest'), 'CAT2'] = 'Harvest'
    df.loc[df.CAT2.str.contains('process'), 'CAT2'] = 'Process'
    df['UNIT'] = 'kt/year'
    df['COUNTRY_ISO3'] = df['COUNTRY'].map(get_country_match_df_globiom().set_index('GLOBIOM')['ISO3'])
    df = df[['YEAR', 'CAT1', 'CAT2', 'RESIDUE', 'UNIT', 'COUNTRY_ISO3', 'LU_GRID',
             'THEO_MIN', 'THEO_MAX', 'SUST_MIN', 'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX']].copy()
    df.to_csv('data/processed/lignocellulose_residue_grid_all_years_scenarios.csv')
    return df


def data_output_potential_impacts_country_level():
    df = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCP1p9', 'scenRCPref']:
            print(year, scenario)
            bw_scenario_set_up(year, scenario)
            for price in ['normal', 'min']:
                df_temp = combine_potential_and_impact(year, scenario, price)
                df_temp['Price'] = price
                df_temp['SCENARIO'] = scenario
                df = pd.concat([df, df_temp], ignore_index=True)
    df.loc[df.COUNTRY == 'FrPolynesia', 'Country'] = 'PF'
    df.loc[df.COUNTRY == 'Palestin', 'Country'] = 'PS'
    df.loc[df.COUNTRY == 'Samoa', 'Country'] = 'WS'
    df['COUNTRY_ISO3'] = df['Country'].map(get_country_match_df_globiom().set_index('ISO2')['ISO3'])
    df = df[df.SUST > 0].copy()
    df.rename(columns={'Product': 'RESIDUE',
                       'GHG': 'CLIMATE_CHANGE_GWP100_kg_CO2eq_per_kg_residue',
                       'GTP': 'CLIMATE_CHANGE_GTP100_kg_CO2eq_per_kg_residue',
                       'BDV': 'BIODIVERSITY_LOSS_PDF_per_kg_residue',
                       'WATER': 'WATER_STRESS_m3_per_kg_residue',
                       'Price': 'RESIDUE_PRICE_SENSITIVITY_CASE',
                       'THEO_MIN': 'THEO_MIN_kt_per_year',
                       'THEO_MAX': 'THEO_MAX_kt_per_year',
                       'SUST_MIN': 'SUST_MIN_kt_per_year',
                       'SUST_MAX': 'SUST_MAX_kt_per_year',
                       'AVAI_MIN': 'AVAI_MIN_kt_per_year',
                       'AVAI_MAX': 'AVAI_MAX_kt_per_year'
                       }, inplace=True)
    df = df[['YEAR', 'SCENARIO', 'CAT1', 'CAT2', 'RESIDUE', 'COUNTRY_ISO3', 'RESIDUE_PRICE_SENSITIVITY_CASE',
             'CLIMATE_CHANGE_GWP100_kg_CO2eq_per_kg_residue',
             'CLIMATE_CHANGE_GTP100_kg_CO2eq_per_kg_residue',
             'BIODIVERSITY_LOSS_PDF_per_kg_residue',
             'WATER_STRESS_m3_per_kg_residue',
             'THEO_MIN_kt_per_year',
             'THEO_MAX_kt_per_year',
             'SUST_MIN_kt_per_year',
             'SUST_MAX_kt_per_year',
             'AVAI_MIN_kt_per_year',
             'AVAI_MAX_kt_per_year']].copy()
    df.loc[df.CAT1 == 'Forestry', 'CAT1'] = 'Forest'
    df.loc[df.CAT2.str.contains('harvest'), 'CAT2'] = 'Harvest'
    df.loc[df.CAT2.str.contains('process'), 'CAT2'] = 'Process'
    df.to_csv('data/processed/lignocellulose_feedstock_potential_impacts_country_level_all_scenarios.csv')
    return df


def data_output_ghg_contribution():
    df = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCP1p9', 'scenRCPref']:
            bw_scenario_set_up(year, scenario)
            for price in ['normal', 'min']:
                df_temp = ghg_contribution_df(year, scenario, price)
                df_temp['RESIDUE_PRICE_SENSITIVITY_CASE'] = price
                df_temp['SCENARIO'] = scenario
                df_temp['YEAR'] = year
                df = pd.concat([df, df_temp], ignore_index=True)
    df['COUNTRY_ISO3'] = df['Country'].map(get_country_match_df_globiom().set_index('ISO2')['ISO3'])
    df = df[(df.SUST_MAX > 0) | (df.SUST_MIN > 0)].copy()
    df['UNIT'] = 'kg CO2eq/kg residue'
    df.rename(columns={'Product': 'RESIDUE', 'Fertilizer production': 'FERTILIZER',
                       'Land use change': 'LAND_USE_CHANGE',
                       'Machinery energy': 'MACHINERY_ENERGY',
                       'Onsite, CH4': 'ONSITE_CH4',
                       'Onsite, CO2': 'ONSITE_CO2',
                       'Onsite, N2O, crop residue': 'ONSITE_N2O_CROP_RESIDUE',
                       'Onsite, N2O, fertilizer': 'ONSITE_N2O_FERTILIZER',
                       'Others': 'OTHERS'}, inplace=True)
    df = df[['YEAR', 'SCENARIO', 'RESIDUE', 'COUNTRY_ISO3', 'RESIDUE_PRICE_SENSITIVITY_CASE', 'UNIT',
             'ONSITE_CH4', 'ONSITE_CO2', 'ONSITE_N2O_CROP_RESIDUE', 'ONSITE_N2O_FERTILIZER',
             'FERTILIZER', 'LAND_USE_CHANGE', 'MACHINERY_ENERGY', 'OTHERS']].copy()
    df['GHG_TOTAL_CRADLE_TO_GATE'] = df['ONSITE_CH4'] + df['ONSITE_CO2'] + df['ONSITE_N2O_CROP_RESIDUE'] + \
                                     df['ONSITE_N2O_FERTILIZER'] + df['FERTILIZER'] + df['LAND_USE_CHANGE'] + \
                                     df['MACHINERY_ENERGY'] + df['OTHERS']
    df.to_csv('data/processed/agricultural_residue_ghg_contribution_all_scenarios.csv')
    return df


def get_df_combined_potential_impacts_all_scenarios():
    df = pd.DataFrame()
    df_crop = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCP1p9', 'scenRCPref']:
            bw_scenario_set_up(year, scenario)
            for price in ['normal', 'min']:
                df_temp = combine_potential_and_impact(year, scenario, price)
                if os.path.exists(f'data/interim/lcia_crop_add_price_{year}_{scenario}_{price}.csv'):
                    df_temp_crop = pd.read_csv(f'data/interim/lcia_crop_add_price_{year}_{scenario}_{price}.csv',
                                               index_col=0)
                else:
                    df_temp_crop = lcia_crop_add_price(year, scenario, price)
                df_temp['Price'] = price
                df_temp['YEAR'] = year
                df_temp['SCENARIO'] = scenario
                df_temp_crop['Price'] = price
                df_temp_crop['YEAR'] = year
                df_temp_crop['SCENARIO'] = scenario
                df = pd.concat([df, df_temp], ignore_index=True)
                df_crop = pd.concat([df_crop, df_temp_crop], ignore_index=True)
    df.loc[df.COUNTRY == 'FrPolynesia', 'Country'] = 'PF'
    df.loc[df.COUNTRY == 'Palestin', 'Country'] = 'PS'
    df.loc[df.COUNTRY == 'Samoa', 'Country'] = 'WS'
    df = df[df.SUST > 0].copy()
    df = df[df.GHG >= 0].copy()
    df = df[['YEAR', 'SCENARIO', 'Price', 'Product', 'Country', 'GHG', 'GHG_EOL', 'GTP', 'BDV', 'BDV_TRA', 'BDV_OCC', 'WATER', 'SUST',
             'THEO_MIN', 'THEO_MAX', 'SUST_MIN', 'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX']].copy()
    df.to_csv(f'data/processed/lignocellulose_feedstock_combined_potential_impacts_all_scenarios.csv')
    df_crop.to_csv(f'data/processed/crop_residue_allocation.csv')
    return df

