import pandas as pd
import os

from src.other.read_globiom_data import (read_globiom_price_data,
                                         read_globiom_forest_data)
from src.other.name_match import wood_harvest_list, get_country_match_df_globiom
from src.data.land_use_change import mf_luc_all


def get_harvest_wood_price():
    df_price = read_globiom_price_data()
    df = df_price[df_price.PRODUCT.isin(wood_harvest_list)].copy()
    df = pd.pivot_table(df, index=['REGION', 'SCENARIO', 'YEAR'],
                        columns='PRODUCT', values='VALUE', aggfunc='sum')
    df.reset_index(inplace=True)
    df = df.fillna(0)
    return df


def read_mf_luc_all():
    if os.path.exists(r'data/interim/forest_luc_with_intensity.csv'):
        df = pd.read_csv(r'data/interim/forest_luc_with_intensity.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = mf_luc_all()
    return df


def calculate_forest_occupation_and_transformation(focus_year, scenario):
    df_forest_o = read_globiom_forest_data()
    df_forest = df_forest_o[df_forest_o.ITEM != 'YIELD'].copy()
    df = pd.pivot_table(df_forest, index=['COUNTRY', 'SCENARIO', 'YEAR'],
                        columns='PRODUCT',
                        values='VALUE', aggfunc='sum')
    df = df.rename(columns={'allproduct': 'harvest_area_1000ha'})
    df = df.fillna(0)
    df.reset_index(inplace=True)
    df_country = get_country_match_df_globiom()
    df['REGION'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['GLOBIOM_region'])
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_price = get_harvest_wood_price()
    df = pd.merge(df, df_price, on=['REGION', 'SCENARIO', 'YEAR'])
    df['Production_x_Price'] = (df['LoggingResidues_x'] * df['LoggingResidues_y'] +
                                df['FW_Biomass_x'] * df['FW_Biomass_y'] +
                                df['OW_Biomass_x'] * df['OW_Biomass_y'] +
                                df['PW_Biomass_x'] * df['PW_Biomass_y'] +
                                df['SW_Biomass_x'] * df['SW_Biomass_y'])
    df['Occupation_logging_residue_m2_year_per_m3'] = (df['harvest_area_1000ha'] * 10000 * df['LoggingResidues_y'] /
                                                       df['Production_x_Price'])
    df['Occupation_sw_m2_year_per_m3'] = (df['harvest_area_1000ha'] * 10000 * df['SW_Biomass_y'] /
                                          df['Production_x_Price'])
    df['Occupation_pw_m2_year_per_m3'] = (df['harvest_area_1000ha'] * 10000 * df['PW_Biomass_y'] /
                                          df['Production_x_Price'])
    df = df[df.YEAR == focus_year].copy()
    df = df[df.SCENARIO == scenario].copy()
    df = df[['Country', 'REGION', 'SCENARIO', 'YEAR', 'Occupation_logging_residue_m2_year_per_m3',
             'Occupation_sw_m2_year_per_m3', 'Occupation_pw_m2_year_per_m3']].copy()
    df_forest_lu = read_mf_luc_all()
    df_forest_lu['ALUC_from_MF_Minimal'] = df_forest_lu['ALUC_from_MF_Minimal'] + df_forest_lu['ALUC_from_SF']
    df_forest_lu = df_forest_lu.drop('ALUC_from_SF', axis=1)
    df_forest_lu['ALUC_from_GrsLnd'] = df_forest_lu['ALUC_from_GrsLnd'] #+ df_forest_lu['ALUC_from_NatLnd']
    df_forest_lu = df_forest_lu.drop('ALUC_from_NatLnd', axis=1)
    df_forest_lu = df_forest_lu.loc[(df_forest_lu.YEAR == focus_year) & (df_forest_lu.SCENARIO == scenario)].copy()
    df_output = pd.DataFrame()
    aluc_list = [x for x in list(df_forest_lu.columns) if 'ALUC' in x]
    occ_name_dict = {'MF_Intense': 'Occupation, forest, intensive',
                     'MF_Light': 'Occupation, forest, extensive',
                     'MF_Minimal': 'Occupation, shrub land, sclerophyllous'}
    tra_to_name_dict = {'MF_Intense': 'Transformation, to forest, intensive',
                        'MF_Light': 'Transformation, to forest, extensive',
                        'MF_Minimal': 'Transformation, to shrub land, sclerophyllous'}
    tra_from_name_dict = {'ALUC_from_CR_Intense': 'Transformation, from annual crop, intensive',
                          'ALUC_from_CR_Light': 'Transformation, from annual crop, extensive',
                          'ALUC_from_CR_Minimal': 'Transformation, from annual crop, minimal',
                          'ALUC_from_MF_Intense': 'Transformation, from forest, intensive',
                          'ALUC_from_MF_Light': 'Transformation, from forest, extensive',
                          'ALUC_from_MF_Minimal': 'Transformation, from shrub land, sclerophyllous',
                          'ALUC_from_SF': 'Transformation, from forest, minimal',
                          'ALUC_from_GrsLnd': 'Transformation, from grassland, natural, for livestock grazing',
                          # 'ALUC_from_NatLnd': 'Transformation, from grassland, natural, for livestock grazing'
                          }

    for aluc in aluc_list:
        df_forest_lu[aluc] = df_forest_lu['SHARE'] * df_forest_lu[aluc]
    for country in list(df.Country.unique()):
        for product in ['logging_residue', 'sw']:
            colname = f'Occupation_{product}_m2_year_per_m3'
            occ_area = df.loc[df.Country == country, colname].iloc[0]
            df_temp = df.loc[df.Country == country, ['Country', 'REGION', 'SCENARIO', 'YEAR']].copy()
            df_temp['PRODUCT'] = product
            df_lu_temp = df_forest_lu.loc[df_forest_lu.Country == country].copy()
            df_lu_temp[aluc_list] *= occ_area
            for lu in list(df_lu_temp.LAND_USE.unique()):
                df_temp[occ_name_dict[lu]] = occ_area * df_lu_temp.loc[df_lu_temp.LAND_USE == lu, 'SHARE'].iloc[0]
                df_temp[tra_to_name_dict[lu]] = df_lu_temp.loc[df_lu_temp.LAND_USE == lu, 'ALUC_to'].iloc[0]
            for lu in aluc_list:
                if "from" in lu and "PriFor" not in lu:
                    df_temp[tra_from_name_dict[lu]] = df_lu_temp[lu].sum()
            df_output = pd.concat([df_output, df_temp], ignore_index=True)
    df_output = df_output.fillna(0)
    df_country = get_country_match_df_globiom()
    df_output['Region'] = df_output['Country'].map(df_country.set_index('ISO2')['IMAGE_region'])
    return df_output


