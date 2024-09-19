import pandas as pd
import numpy as np
import os

from src.old.GLOBIOM_residue_potential import import_globiom_crop_data, crop_residue_potential_c
from src.other.name_match import (get_country_match_df, get_country_match_df_globiom,
                                  crop_dict, crop_residue_dict, crop_list, crop_globiom_list)
from src.data.agriculture_lci_luc import calculate_soil_organic_carbon


def calculate_single_crop_land_use_intensity():
    df = import_globiom_crop_data()
    df = df[(df.ITEM == 'harvest_area') & (df.YEAR < 2051)].copy()
    df = pd.pivot_table(df, index=['COUNTRY', 'CROP', 'YEAR', 'SCENARIO'],
                        columns='TECH', values='VALUE', aggfunc='sum')
    df = df.fillna(0)
    df.reset_index(inplace=True)
    df['CROP'] = df['CROP'].map(crop_dict)
    return df


def calculate_crop_land_use_intensity_percent():
    intensity_list = ['HI', 'IR', 'LI', 'SS']
    df = calculate_single_crop_land_use_intensity()
    df = df[df.YEAR > 2010].copy()
    df_intensity_percent = df.copy()
    for x in intensity_list:
        df_intensity_percent[x] = df[x] / df[intensity_list].sum(axis=1, numeric_only=True)
    return df_intensity_percent


def merge_globiom_crop_tech():
    df_country = get_country_match_df_globiom()
    df_tech = pd.read_csv(r'data/external/GLOBIOM_crop_tech.csv', header=None)
    df_tech.columns = ['COUNTRY', 'CROP', 'ITEM', 'UNIT', 'TECH', 'LU_GRID',
                       'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_crop = import_globiom_crop_data()
    df_crop = pd.pivot_table(df_crop, index=['CROP', 'TECH', 'LU_GRID', 'COUNTRY', 'SCENARIO', 'YEAR'],
                             columns='ITEM', values='VALUE', aggfunc='sum')
    df_tech = pd.pivot_table(df_tech, index=['CROP', 'TECH', 'LU_GRID', 'COUNTRY', 'SCENARIO', 'YEAR'],
                             columns='ITEM', values='VALUE', aggfunc='sum')
    df_crop = pd.concat([df_crop, df_tech], axis=1)
    df_crop = df_crop.dropna(subset=['production'])
    df_crop.reset_index(inplace=True)

    df_crop['N_total'] = df_crop['harvest_area'] * df_crop['N_fertilization']
    df_crop['P_total'] = df_crop['harvest_area'] * df_crop['P_fertilization']
    df_crop = df_crop.fillna(0)
    # aggregate to country level
    df_crop = pd.pivot_table(df_crop,
                             index=['CROP', 'COUNTRY', 'SCENARIO', 'YEAR'],
                             values=['harvest_area', 'production', 'N_total', 'P_total'],
                             aggfunc='sum')
    # re-calculate inputs per ha
    df_crop.reset_index(inplace=True)
    df_crop['Yield_kg_per_ha'] = df_crop['production'] / df_crop['harvest_area'] * 1000  # kg/ha
    df_crop['N_kg_per_ha'] = df_crop['N_total'] / df_crop['harvest_area']
    df_crop['P_kg_per_ha'] = df_crop['P_total'] / df_crop['harvest_area'] / 64 * 144  # from P to P2O5

    # match country and crop names
    df_crop['Country'] = df_crop['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_crop['Crop'] = df_crop['CROP'].map(crop_dict)
    df = df_crop[['Crop', 'Country', 'SCENARIO', 'YEAR',
                  'harvest_area', 'production', 'Yield_kg_per_ha',
                  'N_kg_per_ha', 'P_kg_per_ha']].copy()
    df = df[(df.YEAR < 2051) & (df.YEAR > 2019)].copy()
    return df


def add_k_input():
    df = merge_globiom_crop_tech()
    df_country = get_country_match_df()
    df_fubc = pd.read_excel(r'data/external/FUBC_1_to_9_data.xlsx', engine='openpyxl', sheet_name='Sheet2')
    df_fubc['Country'] = df_fubc['ISO3_code'].map(df_country.set_index('ISO3')['ISO2'])
    df_fubc = df_fubc.replace(-999, np.nan)
    df_fubc_glo_average = df_fubc.groupby(by=['Crop']).mean(numeric_only=True)
    df_fubc_glo_average['GLO_aver_K2O_rate_kg_ha'] = (df_fubc_glo_average['K2O_k_t'] /
                                                      df_fubc_glo_average['Crop_area_k_ha'] * 1000)
    df_fubc_glo_average = df_fubc_glo_average[['GLO_aver_K2O_rate_kg_ha']].copy()
    df_fubc_glo_average.reset_index(inplace=True)
    df_temp = pd.merge(df, df_fubc_glo_average, on=['Crop'], how='left')
    df_fubc.rename(columns={'Aver_K2O_rate_kg_ha': 'K2O_2020'}, inplace=True)
    df_fubc = df_fubc[['Crop', 'Country', 'K2O_2020']]
    df_temp = pd.merge(df_temp, df_fubc, on=['Crop', 'Country'], how='left')
    df_2020 = df.loc[df.YEAR == 2020, ['Crop', 'Country', 'SCENARIO', 'N_kg_per_ha']].copy()
    df_2020.rename(columns={'N_kg_per_ha': 'N_2020'}, inplace=True)
    df_temp = pd.merge(df_temp, df_2020, on=['Crop', 'Country', 'SCENARIO'], how='left')
    df_temp['K2O_2020'].fillna(df_temp['GLO_aver_K2O_rate_kg_ha'], inplace=True)
    df_temp['K2O_kg_per_ha'] = df_temp['N_kg_per_ha'] / df_temp['N_2020'] * df_temp['K2O_2020']
    k2o_max = (df_fubc['K2O_2020'] * 1000).quantile(q=0.95)
    df_temp.loc[df_temp.K2O_kg_per_ha > k2o_max, 'K2O_kg_per_ha'] = k2o_max
    df_temp.fillna(0, inplace=True)
    df_temp = df_temp[['Crop', 'Country', 'SCENARIO', 'YEAR', 'K2O_kg_per_ha']].copy()
    df = pd.merge(df, df_temp, on=['Crop', 'Country', 'SCENARIO', 'YEAR'], how='left')
    return df


def read_fertilizer_products():
    df = pd.read_csv(r'data/external/FAOSTAT_fertilizer_product.csv')
    df_map = pd.read_excel(r'data/raw_data/Fertilizer_map.xlsx', engine='openpyxl', sheet_name='Fertilizer_map')
    df_country = get_country_match_df()
    # mean value of 2018-2020 for each fertilizer products
    df = pd.pivot_table(df, index=['Area', 'Item'], values='Value', aggfunc='mean')
    df.reset_index(inplace=True)
    df = df.loc[df.Item.isin(list(df_map.Fertilizer_FAO.unique()))]
    df['Country'] = df['Area'].map(df_country.set_index('FAOSTAT_name')['ISO2'])
    return df


df_fer_map = pd.read_excel(r'data/raw_data/Fertilizer_map.xlsx', engine='openpyxl', sheet_name='Fertilizer_map')
df_fao = read_fertilizer_products()
df_fao_glo = pd.pivot_table(df_fao, index=['Item'], values='Value', aggfunc='sum')


def calculate_fertilizer_products_row(row):
    country = row['Country']
    df_temp = df_fer_map.copy()
    if country in list(df_fao.Country.unique()):
        df_temp['Application'] = df_temp['Fertilizer_FAO'].map(
            df_fao[df_fao.Country == country].set_index('Item')['Value'])
    else:
        df_temp['Application'] = df_temp['Fertilizer_FAO'].map(df_fao_glo['Value'])
    df_temp = df_temp.fillna(0)
    npk_rank_dict = {'N': row['N_kg_per_ha'],
                     'P': row['P_kg_per_ha'],
                     'K': row['K2O_kg_per_ha']}
    npk_index_1 = min(npk_rank_dict, key=npk_rank_dict.get)
    npk_dose_1 = npk_rank_dict[npk_index_1]
    df_temp['temp'] = df_temp['Application'] * df_temp[npk_index_1]
    df_temp['dose1'] = df_temp['temp'] / df_temp['temp'].sum() * npk_dose_1 / df_temp[npk_index_1]
    npk_rank_dict.pop(npk_index_1)
    npk_index_2 = min(npk_rank_dict, key=npk_rank_dict.get)
    npk_dose_2 = npk_rank_dict[npk_index_2]
    applied_2 = (df_temp['dose1'] * df_temp[npk_index_2]).sum()
    npk_dose_2 -= applied_2
    if npk_dose_2 < 0:
        npk_dose_2 = 0
    df_temp['temp'] = df_temp['Application'] * df_temp[npk_index_2]
    df_temp.loc[df_temp.dose1 >= 0, 'temp'] = 0
    df_temp['dose2'] = df_temp['temp'] / df_temp['temp'].sum() * npk_dose_2 / df_temp[npk_index_2]
    npk_index_3 = max(npk_rank_dict, key=npk_rank_dict.get)
    npk_dose_3 = npk_rank_dict[npk_index_3]
    applied_3 = (df_temp['dose1'] * df_temp[npk_index_3]).sum() + (df_temp['dose2'] * df_temp[npk_index_3]).sum()
    npk_dose_3 -= applied_3
    if npk_dose_3 < 0:
        npk_dose_3 = 0
    df_temp['temp'] = df_temp['Application'] * df_temp[npk_index_3]
    df_temp.loc[((df_temp.dose1 >= 0) | (df_temp.dose2 >= 0)), 'temp'] = 0
    df_temp['dose3'] = df_temp['temp'] / df_temp['temp'].sum() * npk_dose_3 / df_temp[npk_index_3]
    df_temp = df_temp.fillna(0)
    df_temp['dose'] = df_temp['dose1'] + df_temp['dose2'] + df_temp['dose3']
    for fertilizer in list(df_temp.Fertilizer_AGDB.unique()):
        dose = df_temp.loc[df_temp.Fertilizer_AGDB == fertilizer, 'dose'].iloc[0]
        row[fertilizer] = dose
    return row


def calculate_fertilizer_products():
    df_0 = add_k_input()
    df = df_0.apply(calculate_fertilizer_products_row, axis=1)
    df.to_csv(r'data/interim/crop_lci_fertilizer_dose.csv')
    return df


def calculate_fertilizer_emissions():
    """
    Air
    * N2O direct: 0.01, 0.004 for rice, times total N input
    * N2O indirect: FracGASF = 0.11, EF4 = 0.01, EF5 = 0.011, FracLEACH=0.24
    * CO2: urea * 0.2 * 44/12+urea ammonium nitrate solution*0.366*0.2*44/12
    * NO = N2O*0.04
    * NH3 to calculate from EFs

    Water emissions:
    * phosphorus: =0.1 * P-fertilizer*64/144
    * Nitrate: dbdata, 0.24*Frac_wet
    """
    if os.path.exists(r'data/interim/crop_lci_fertilizer_dose.csv'):
        df = pd.read_csv(r'data/interim/crop_lci_fertilizer_dose.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = calculate_fertilizer_products()
    df_soc = calculate_soil_organic_carbon()
    df_soc['wet_P'] = df_soc['Temp_cold_moi_P'] + df_soc['Temp_warm_moi_P'] + df_soc['Trop_moi_P'] + df_soc[
        'Trop_wet_P'] + df_soc['Boreal_P']
    df_soc = df_soc.drop_duplicates(subset='ISO', keep='first')
    df['wet_P'] = df['Country'].map(df_soc.set_index('ISO')['wet_P'])
    df['CO2'] = (df['Urea,  as 100% CO(NH2)2 (NPK 46.6-0-0)'] * 0.2 * 44 / 12 +
                 df['Liquid urea-ammonium nitrate solution (NPK 30-0-0),  market mix'] * 0.366 * 0.2 * 44 / 12)
    df.loc[df['Crop'] == 'Rice', 'N2O direct'] = df.loc[df['Crop'] == 'Rice', 'N_kg_per_ha'] * 0.004 * 44 / 28
    df.loc[df['Crop'] != 'Rice', 'N2O direct'] = df.loc[df['Crop'] != 'Rice', 'N_kg_per_ha'] * 0.01 * 44 / 28
    df['N2O indirect'] = (df['N_kg_per_ha'] * 0.11 * 0.01 + df['N_kg_per_ha'] * 0.24 * 0.011) * 44 / 28
    df['NH3'] = df['N_kg_per_ha'] * 0.11 * 17 / 14
    df['NO'] = df['N_kg_per_ha'] * 0.04
    df['P emission'] = df['P_kg_per_ha'] * 0.1 * 64 / 144
    df['NO3'] = df['N_kg_per_ha'] * 0.24 * df['wet_P'] * 62 / 14

    return df


def add_crop_residues():
    df = calculate_fertilizer_emissions()
    if os.path.exists(r'data/interim/GLOBIOM_agricultural_residue_c.csv'):
        df_residue = pd.read_csv(r'data/interim/GLOBIOM_agricultural_residue_c.csv', index_col=0)
    else:
        df_residue = crop_residue_potential_c()
    df_country = get_country_match_df_globiom()
    df_residue['Country'] = df_residue['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_residue['Crop'] = df_residue['RESIDUE'].map(crop_residue_dict)
    df_residue = df_residue[['YEAR', 'SCENARIO', 'Country', 'Crop',
                             "THEO_MIN", "THEO_MAX", "SUST_MIN", "SUST_MAX", "AVAI_MIN", "AVAI_MAX"]].copy()
    df_temp = pd.merge(df, df_residue, on=['Crop', 'Country', 'SCENARIO', 'YEAR'], how='left')
    df_temp['Residue_min_kg_per_ha'] = df_temp['SUST_MIN'] / df_temp['harvest_area'] * 1000
    df_temp['Residue_max_kg_per_ha'] = df_temp['SUST_MAX'] / df_temp['harvest_area'] * 1000
    df_temp['Residue_total_kg_per_ha'] = ((df_temp['THEO_MAX'] + df_temp['THEO_MIN']) / 2
                                          / df_temp['harvest_area'] * 1000)
    df_temp['Residue_removal_kg_per_ha'] = ((df_temp['SUST_MAX'] + df_temp['SUST_MIN']) / 2
                                            / df_temp['harvest_area'] * 1000)
    df_temp = df_temp[['Crop', 'Country', 'SCENARIO', 'YEAR',
                       'Residue_min_kg_per_ha', 'Residue_max_kg_per_ha',
                       'Residue_total_kg_per_ha', 'Residue_removal_kg_per_ha']].copy()
    df = pd.merge(df, df_temp, on=['Crop', 'Country', 'SCENARIO', 'YEAR'], how='left')
    return df


def calculate_crop_residues_emissions():
    """
    parameters from IPCC https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch11_Soils_N2O_CO2.pdf table 11.1a
    * EF1=0.01
    * FCR=((AGRtot-AGRremoval) * NAG)+(YIELD+AGRtot) * R * NBG
    * N2O=FCR * 0.01 * 44/28
    * Fracleach = 0.24
    * EF5=0.011
    * N2O_indirect = FCR * Fracleach * EF5 * 44/28
    """
    df = add_crop_residues()
    nag_list = [0.007, 0.006, 0.008, 0.007, 0.007, 0.008, 0.008, 0.006]
    nbg_list = [0.014, 0.007, 0.009, 0.009, 0.006, 0.008, 0.009, 0.009]
    r_list = [0.22, 0.22, 0.22, 0.16, 0.22, 0.19, 0.22, 0.23]
    nag_dict = {crop_list[i]: nag_list[i] for i in range(len(crop_list))}
    nbg_dict = {crop_list[i]: nbg_list[i] for i in range(len(crop_list))}
    r_dict = {crop_list[i]: r_list[i] for i in range(len(crop_list))}
    df["NAG"] = df['Crop'].map(nag_dict)
    df["NBG"] = df['Crop'].map(nbg_dict)
    df["R"] = df['Crop'].map(r_dict)
    df['FCR'] = ((df['Residue_total_kg_per_ha'] - df['Residue_removal_kg_per_ha']) * df["NAG"] +
                 (df['Yield_kg_per_ha'] + df['Residue_total_kg_per_ha']) * df["R"] * df["NBG"])
    df['N2O direct CR'] = df['FCR'] * 0.01 * 44 / 28
    df['N2O indirect CR'] = df['FCR'] * 0.24 * 0.011 * 44 / 28
    df['NO3 CR'] = df['FCR'] * 0.24 * df['wet_P'] * 62 / 14
    df = df.drop(['NAG', 'NBG', 'R', 'FCR'], axis=1)
    return df


def add_blue_water():
    """
    Pfister 2011
    """
    df_irri = pd.read_excel(r'data/external/Pfister_blue_water_by_crop_country.xlsx',
                            engine='openpyxl', sheet_name='Sheet1')
    df_irri.loc[df_irri.Country.isna(), "Country"] = "NA"
    df_irri = df_irri.fillna(0)
    df0 = calculate_crop_residues_emissions()
    df = pd.merge(df0, df_irri, on=['Crop', 'Country'], how='left')
    df['Blue_water_m3_per_ha'] = df['Yield_kg_per_ha'] * df['Blue_water_m3_per_t'] / 1000
    df = df.drop(['Blue_water_m3_per_t'], axis=1)
    df = df.dropna()
    return df


def add_price():
    """
    assume price of straws is the same as logging residues.
    sawdust density: 0.583*440+(1-0.583)*640=523.4 kg/m3 = 0.5234 tonne/m3
    wood density: hardwood - 640, softwood - 440
    (source: http://www.dflca.ch/inventories/Hintergrund/Werner_2017-report_wood_KBOB_2016.pdf)
    """
    df_price_o = pd.read_csv(r'data/external/GLOBIOM_regional_price.csv', header=None)
    df_price_o.columns = ['PRODUCT', 'UNIT', 'Region', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_price_o.loc[df_price_o.VALUE == 'EPS', 'VALUE'] = np.nan
    df_price_o = df_price_o[['PRODUCT', 'Region', 'SCENARIO', 'YEAR', 'VALUE']].copy()
    df_price_crop = df_price_o[df_price_o.PRODUCT.isin(crop_globiom_list)].copy()
    df_price_crop['VALUE'] = df_price_crop['VALUE'].astype(float)
    df_price_crop["Crop"] = df_price_crop['PRODUCT'].map(crop_dict)
    df_price_crop.rename(columns={'VALUE': "Price_crop_USD_per_t"}, inplace=True)
    df_price_crop = df_price_crop.drop(['PRODUCT'], axis=1)
    df_price_residue = df_price_o[df_price_o.PRODUCT == 'LoggingResidues'].copy()
    df_price_residue['VALUE'] = df_price_residue['VALUE'].astype(float)
    df_price_residue['VALUE'] = df_price_residue['VALUE'] / 0.5234
    df_price_residue.rename(columns={'VALUE': "Price_residue_USD_per_t"}, inplace=True)
    df_price_residue = df_price_residue.drop(['PRODUCT'], axis=1)
    for region in list(df_price_residue.Region.unique()):
        for year in list(df_price_residue[df_price_residue.Region == region]['YEAR'].unique()):
            price_min = df_price_residue.loc[(df_price_residue.Region == region) &
                                             (df_price_residue.YEAR == year), "Price_residue_USD_per_t"].min()
            price_max = df_price_residue.loc[(df_price_residue.Region == region) &
                                             (df_price_residue.YEAR == year), "Price_residue_USD_per_t"].max()
            df_price_residue.loc[(df_price_residue.Region == region) &
                                 (df_price_residue.YEAR == year), "Price_residue_min_USD_per_t"] = price_min
            df_price_residue.loc[(df_price_residue.Region == region) &
                                 (df_price_residue.YEAR == year), "Price_residue_max_USD_per_t"] = price_max
    df_country = get_country_match_df()
    df = add_blue_water()
    df['Region'] = df['Country'].map(df_country.set_index('ISO2')['GLOBIOM_region'])
    df = pd.merge(df, df_price_crop, on=['Crop', 'Region', 'SCENARIO', 'YEAR'])
    df = pd.merge(df, df_price_residue, on=['Region', 'SCENARIO', 'YEAR'])
    return df


def add_land_use_change():
    df = add_price()
    if os.path.exists(r'data/interim/crop_lci_luc.csv'):
        df_luc = pd.read_csv(r'data/interim/crop_lci_luc.csv', index_col=0)
        df_luc['Country'] = df_luc['Country'].fillna('NA')
    else:
        from src.data.agriculture_lci_luc import calculate_crop_luc_ghg_all_years
        df_luc = calculate_crop_luc_ghg_all_years()
    df = pd.merge(df, df_luc, how='left', on=['SCENARIO', 'YEAR', 'Country', 'Crop'])
    return df


def add_land_use_intensity():
    df = add_land_use_change()
    df_intensity = calculate_crop_land_use_intensity_percent()
    df_country = get_country_match_df_globiom()
    df_intensity['Country'] = df_intensity['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_intensity['Occupation, annual crop, intensive'] = 10000 * (df_intensity['HI'] + df_intensity['IR'])
    df_intensity['Occupation, annual crop, extensive'] = 10000 * df_intensity['LI']
    df_intensity['Occupation, annual crop, minimal'] = 10000 * df_intensity['SS']
    df_intensity.rename(columns={'CROP': 'Crop'}, inplace=True)
    df_intensity = df_intensity[['Crop', 'SCENARIO', 'YEAR',
                                 'Occupation, annual crop, intensive',
                                 'Occupation, annual crop, extensive',
                                 'Occupation, annual crop, minimal', 'Country']].copy()
    df = pd.merge(df, df_intensity, how='left', on=['SCENARIO', 'YEAR', 'Country', 'Crop'])
    df['Transformation, from annual crop, intensive'] = (df['Transformation, from annual crop'] *
                                                         df['Occupation, annual crop, intensive'] / 10000)
    df['Transformation, from annual crop, extensive'] = (df['Transformation, from annual crop'] *
                                                         df['Occupation, annual crop, extensive'] / 10000)
    df['Transformation, from annual crop, minimal'] = (df['Transformation, from annual crop'] *
                                                       df['Occupation, annual crop, minimal'] / 10000)
    df['Transformation, to annual crop, intensive'] = (df['Transformation, to annual crop'] *
                                                       df['Occupation, annual crop, intensive'] / 10000)
    df['Transformation, to annual crop, extensive'] = (df['Transformation, to annual crop'] *
                                                       df['Occupation, annual crop, extensive'] / 10000)
    df['Transformation, to annual crop, minimal'] = (df['Transformation, to annual crop'] *
                                                     df['Occupation, annual crop, minimal'] / 10000)
    df.to_csv(r'data/interim/crop_lci.csv')
    return df
