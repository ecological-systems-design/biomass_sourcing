import pandas as pd

from src.other.name_match import wood_harvest_list, get_country_match_df_globiom
from src.other.read_globiom_data import read_globiom_price_data


def read_globiom_forest_data():
    df_forest = pd.read_csv(r'data/external/GLOBIOM_forest_data_grid.csv', header=None)
    df_forest.columns = ['PRODUCT', 'ITEM', 'UNIT', 'LU_GRID', 'COUNTRY', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_forest = df_forest.drop(['SSP', 'SPA'], axis=1)
    return df_forest


def read_globiom_luc_data(focus_year):
    df_luc = pd.read_csv(r'data/external/GLOBIOM_luc_grid.csv', header=None)
    df_luc.columns = ['COUNTRY', 'LU_GRID', 'UNIT', 'LU_FROM', 'LU_TO',
                      'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_luc = df_luc[(df_luc.YEAR == focus_year) | (df_luc.YEAR == (focus_year - 10))].copy()
    df_luc.loc[df_luc.LU_FROM == "NatLnd", 'LU_FROM'] = 'GrsLnd'  # assume to have the same carbon storage
    df_luc = pd.pivot_table(df_luc, values=["VALUE"],
                            index=['COUNTRY', 'UNIT', 'LU_FROM', 'LU_TO', 'SCENARIO'],
                            aggfunc='sum')
    df_luc.reset_index(inplace=True)
    df_luc['UNIT'] = '1000ha/20yr'
    df_luc_1 = df_luc.copy()
    df_luc_1["LAND_USE"] = df_luc_1["LU_FROM"]
    df_luc_1["VALUE"] = -df_luc_1["VALUE"]
    df_luc_2 = df_luc.copy()
    df_luc_2["LAND_USE"] = df_luc_2["LU_TO"]
    df_luc_net_change = pd.concat([df_luc_1, df_luc_2], ignore_index=True)
    df_luc_net_change = pd.pivot_table(df_luc_net_change, values=["VALUE"],
                                       index=['COUNTRY', 'UNIT', 'SCENARIO', 'LAND_USE'],
                                       aggfunc='sum')
    df_luc_net_change.reset_index(inplace=True)
    return df_luc_net_change


def get_harvest_wood_price():
    df_price = read_globiom_price_data()
    df = df_price[df_price.PRODUCT.isin(wood_harvest_list)].copy()
    df = pd.pivot_table(df, index=['REGION', 'SCENARIO', 'YEAR'],
                                columns='PRODUCT', values='VALUE', aggfunc='sum')
    df.reset_index(inplace=True)
    df = df.fillna(0)
    return df


def calculate_occupation(focus_year):
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
    df = df[['COUNTRY', 'REGION', 'SCENARIO', 'YEAR', 'Occupation_logging_residue_m2_year_per_m3',
             'Occupation_sw_m2_year_per_m3', 'Occupation_pw_m2_year_per_m3']].copy()
    return df


def calculate_forest_harvest_area_change(focus_year):
    df_o = read_globiom_forest_data()
    df = df_o[((df_o.YEAR == focus_year) | (df_o.YEAR == focus_year-20)) & (df_o.ITEM == 'harvest_area')].copy()
    df = pd.pivot_table(df, index=["COUNTRY", "SCENARIO"], columns="YEAR", values="VALUE", aggfunc="sum")
    df.reset_index(inplace=True)
    df = df.fillna(0)
    df["REC"] = (df[focus_year] - df[focus_year-20])/df[focus_year]
    df2 = read_globiom_luc_data(focus_year)
    df2 = pd.pivot_table(df2, index=["COUNTRY", "SCENARIO"], columns="LAND_USE", values="VALUE", aggfunc="sum")
    df2.reset_index(inplace=True)
    df2 = df2.fillna(0)
    df2 = df2[["COUNTRY", "SCENARIO", "CrpLnd", "GrsLnd", "PriFor"]].copy()
    df = pd.merge(df, df2, on=["COUNTRY", "SCENARIO"], how="left")
    df.loc[df.REC < 0, "REC"] = 0
    df.loc[df.CrpLnd > 0, "CrpLnd"] = 0
    df.loc[df.GrsLnd > 0, "GrsLnd"] = 0
    df.loc[df.PriFor > 0, "PriFor"] = 0
    df["Total_contracted_area"] = df["CrpLnd"] + df["GrsLnd"] + df["PriFor"]
    df["CrpLnd_P"] = df["CrpLnd"] / df["Total_contracted_area"]
    df["GrsLnd_P"] = df["GrsLnd"] / df["Total_contracted_area"]
    df["PriFor_P"] = df["PriFor"] / df["Total_contracted_area"]
    df = df.fillna(0)
    df = df[["COUNTRY", "SCENARIO", "REC", "CrpLnd_P", "GrsLnd_P", "PriFor_P"]].copy()
    df["YEAR"] = focus_year
    return df


def calculate_cropland_intensity(focus_year):
    df_crop_o = pd.read_csv(r'data/external/GLOBIOM_crop_by_tech_grid.csv', header=None)
    df_crop_o.columns = ['CROP', 'ITEM', 'UNIT', 'TECH', 'LU_GRID',
                         'COUNTRY', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df = df_crop_o.drop(['SSP', 'SPA'], axis=1)

    # Correction for soya in Switzerland
    df.loc[
        (df.CROP == 'Soya') & (df.COUNTRY == 'Switzerland') & (df.ITEM == 'YIELD'), 'VALUE'] /= 10
    df.loc[
        (df.CROP == 'Soya') & (df.COUNTRY == 'Switzerland') & (
                    df.ITEM == 'production'), 'VALUE'] /= 10
    df = df[(df.ITEM == 'harvest_area')].copy()
    df = pd.pivot_table(df, index=['COUNTRY', 'YEAR', 'SCENARIO'],
                        columns='TECH', values='VALUE', aggfunc='sum')
    df = df.fillna(0)
    df.reset_index(inplace=True)
    intensity_list = ['HI', 'IR', 'LI', 'SS']
    df_intensity_percent = df.copy()
    for x in intensity_list:
        df_intensity_percent[x] = df[x] / df[intensity_list].sum(axis=1, numeric_only=True)
    df_intensity_percent = df_intensity_percent[df_intensity_percent.YEAR == focus_year].copy()
    return df_intensity_percent


def calculate_forest_luc(focus_year, product_name):
    df_crop_intensity = calculate_cropland_intensity(focus_year)
    df_forest = calculate_forest_harvest_area_change(focus_year)
    df_occupation = calculate_occupation(focus_year)
    df = pd.merge(df_occupation, df_forest, on=["COUNTRY", "SCENARIO", "YEAR"], how='left')
    df = pd.merge(df, df_crop_intensity, on=["COUNTRY", "SCENARIO", "YEAR"], how='left')
    colname = f"Occupation_{product_name}_m2_year_per_m3"
    df['Transformation, from annual crop, intensive'] = df[colname] * df["REC"] * df["CrpLnd_P"] * (df["HI"] +
                                                                                                    df["IR"]) / 20
    df['Transformation, from annual crop, extensive'] = df[colname] * df["REC"] * df["CrpLnd_P"] * df["LI"] / 20
    df['Transformation, from annual crop, minimal'] = df[colname] * df["REC"] * df["CrpLnd_P"] * df["SS"] / 20
    df['Transformation, from grassland, natural, for livestock grazing'] = df[colname] * df["REC"] * df["GrsLnd_P"] / 20
    df['Transformation, from forest, primary (non-use)'] = df[colname] * df["REC"] * df["PriFor_P"] / 20
    df['Transformation, to forest, extensive'] = df[colname] * df["REC"] / 20
    df['Occupation, forest, extensive'] = df[colname]
    df = df[["COUNTRY", "SCENARIO", "YEAR", 'Occupation, forest, extensive',
             'Transformation, from annual crop, intensive',
             'Transformation, from annual crop, extensive',
             'Transformation, from annual crop, minimal',
             'Transformation, from grassland, natural, for livestock grazing',
             'Transformation, from forest, primary (non-use)', 'Transformation, to forest, extensive']].copy()
    df = df.fillna(0)
    df['PRODUCT'] = product_name
    return df


def forest_luc():
    df = pd.DataFrame()
    for focus_year in range(2020, 2051, 10):
        for product_name in ["logging_residue", "sw", "pw"]:
            df_temp = calculate_forest_luc(focus_year, product_name)
            df = pd.concat([df, df_temp], ignore_index=True)
    df_country = get_country_match_df_globiom()
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df['Region'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['IMAGE_region'])
    df.to_csv(r'data/interim/forest_lci.csv')
    return df


