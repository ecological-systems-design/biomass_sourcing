import pandas as pd


from src.other.name_match import get_country_match_df_globiom


def read_globiom_price_data():
    df_price_o = pd.read_csv(r'data/globiom/GLOBIOM_regional_price.csv', header=None)
    df_price_o.columns = ['PRODUCT', 'UNIT', 'REGION', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_price_o = df_price_o[df_price_o['VALUE'] != 'EPS'].copy()
    df_price_o['VALUE'] = df_price_o['VALUE'].astype(float)
    df_price = df_price_o[df_price_o.REGION != 'World'].copy()
    return df_price


def read_globiom_forest_rotation_data():
    df = pd.read_csv(r'data/globiom/GLOBIOM_forest_rotation_period.csv')
    df_country = get_country_match_df_globiom()
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    return df


def read_globiom_forest_land_use_data():
    df = pd.read_csv(r'data/globiom/GLOBIOMfor_forest_land_use.csv', header=None)
    df.columns = ['REGION', 'UNIT', 'LAND_USE', 'SSP', 'SCENARIO', 'YEAR', 'VALUE']
    df_country = get_country_match_df_globiom()
    df['Country'] = df['REGION'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df['SCENARIO'] = 'scen' + df['SCENARIO']
    return df


def read_globiom_forest_data():
    df_forest = pd.read_csv(r'data/globiom/GLOBIOM_forest_data_grid.csv', header=None)
    df_forest.columns = ['PRODUCT', 'ITEM', 'UNIT', 'LU_GRID', 'COUNTRY', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_forest = df_forest.drop(['SSP', 'SPA'], axis=1)
    return df_forest


def read_globiom_land_use_data():
    df = pd.read_csv(r'data/globiom/GLOBIOM_land_use_sensitivity.csv', header=None)
    df.columns = ['COUNTRY', 'LU_GRID', 'UNIT', 'LAND_USE', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_country = get_country_match_df_globiom()
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    return df


def read_globiom_crop_data_g():
    df_crop_o = pd.read_csv(r'data/globiom/GLOBIOM_crop_by_tech_grid.csv', header=None)
    df_crop_o.columns = ['CROP', 'ITEM', 'UNIT', 'TECH', 'LU_GRID',
                         'COUNTRY', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_crop = df_crop_o.drop(['SSP', 'SPA'], axis=1)
    # Correction for soya in Switzerland
    df_crop.loc[
        (df_crop.CROP == 'Soya') & (df_crop.COUNTRY == 'Switzerland') & (df_crop.ITEM == 'YIELD'), 'VALUE'] /= 10
    df_crop.loc[
        (df_crop.CROP == 'Soya') & (df_crop.COUNTRY == 'Switzerland') & (df_crop.ITEM == 'production'), 'VALUE'] /= 10
    return df_crop


def read_globiom_forest_total_production_r_data():
    df = pd.read_csv(r'data/globiom/GLOBIOM_forest_total_production_region.csv', header=None)
    df.columns = ['REGION', 'SSP', 'SPA', 'SCENARIO', 'PRODUCT', 'YEAR', 'VALUE_TP']
    df = df.drop(['SSP', 'SPA'], axis=1)
    df = df.set_index(['REGION', 'SCENARIO', 'PRODUCT', 'YEAR'])
    return df


def read_globiom_forest_total_material_consumption_r_data():
    df = pd.read_csv(r'data/globiom/GLOBIOM_forest_material_consumption_region.csv', header=None)
    df.columns = ['REGION', 'SSP', 'SPA', 'SCENARIO', 'PRODUCT', 'YEAR', 'VALUE_MC']
    df = df.drop(['SSP', 'SPA'], axis=1)
    df = df.set_index(['REGION', 'SCENARIO', 'PRODUCT', 'YEAR'])
    return df


def read_globiom_forest_energy_consumption_r_data():
    df = pd.read_csv(r'data/globiom/GLOBIOM_forest_energy_consumption_region.csv', header=None)
    df.columns = ['REGION', 'SSP', 'SPA', 'SCENARIO', 'PRODUCT', 'YEAR', 'VALUE_EC']
    df = df.drop(['SSP', 'SPA'], axis=1)
    df = df.set_index(['REGION', 'SCENARIO', 'PRODUCT', 'YEAR'])
    return df


def read_globiom_forest_net_export_r_data():
    df = pd.read_csv(r'data/globiom/GLOBIOM_forest_net_export_region.csv', header=None)
    df.columns = ['REGION', 'SSP', 'SPA', 'SCENARIO', 'PRODUCT', 'YEAR', 'VALUE_NE']
    df = df.drop(['SSP', 'SPA'], axis=1)
    df = df.set_index(['REGION', 'SCENARIO', 'PRODUCT', 'YEAR'])
    return df


def read_globiomfor_forest_production_c_data():
    df = pd.read_csv(r'data/globiom/GLOBIOMfor_forest_production.csv', header=None)
    df.columns = ['COUNTRY', 'UNIT', 'TYPE', 'PRODUCT', 'BASELINE', 'SCENARIO', 'YEAR', 'VALUE']
    df = df.drop(['BASELINE'], axis=1)
    df.loc[df.SCENARIO == "RCPref", "SCENARIO"] = "scenRCPref"
    df.loc[df.SCENARIO == "RCP1p9", "SCENARIO"] = "scenRCP1p9"
    return df


def read_globiom_forest_data_g():
    df = pd.read_csv(r'data/globiom/GLOBIOM_forest_data_grid.csv', header=None)
    df.columns = ['PRODUCT', 'ITEM', 'UNIT', 'LU_GRID', 'COUNTRY', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df = df.drop(['SSP', 'SPA'], axis=1)
    df_country = get_country_match_df_globiom()
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df['REGION'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['GLOBIOM_region'])
    return df


def read_globiom_land_use_sensitivity_data_g():
    df = pd.read_csv(r'data/globiom/GLOBIOM_land_use_sensitivity.csv', header=None)
    df.columns = ['COUNTRY', 'LU_GRID', 'UNIT', 'LAND_USE', 'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_country = get_country_match_df_globiom()
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    return df

