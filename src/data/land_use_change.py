import pandas as pd

from src.other.read_globiom_data import (read_globiom_land_use_data,
                                         read_globiom_forest_land_use_data,
                                         )
from src.other.name_match import get_country_match_df_globiom, crop_dict, crop_globiom_list
from src.other.read_globiom_data import read_globiom_crop_data_g


def calculate_all_crop_land_use_intensity():
    df = read_globiom_crop_data_g()
    df = df[(df.ITEM == 'harvest_area') & (df.YEAR < 2051)].copy()
    df = pd.pivot_table(df, index=['COUNTRY', 'YEAR', 'SCENARIO'],
                        columns='TECH', values='VALUE', aggfunc='sum')
    df = df.fillna(0)
    df.reset_index(inplace=True)
    df['CR_Intense'] = df['HI'] + df['IR']
    df.rename(columns={'LI': 'CR_Light', 'SS': 'CR_Minimal'}, inplace=True)
    df = df[['COUNTRY', 'YEAR', 'SCENARIO', 'CR_Intense', 'CR_Light', 'CR_Minimal']].copy()
    return df


def calculate_crop_land_use_intensity_percent():
    intensity_list = ['CR_Intense', 'CR_Light', 'CR_Minimal']
    df = calculate_all_crop_land_use_intensity()
    df_intensity_percent = df.copy()
    for x in intensity_list:
        df_intensity_percent[x] = df[x] / df[intensity_list].sum(axis=1, numeric_only=True)
    df_country = get_country_match_df_globiom()
    df_intensity_percent['Country'] = df_intensity_percent['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    return df_intensity_percent


def harmonize_land_use_from_two_globiom_models(year, scenario):
    df0 = read_globiom_land_use_data()
    dff = read_globiom_forest_land_use_data()
    dff = dff.loc[(dff.YEAR == year) & (dff.SCENARIO == scenario)].copy()
    dff.loc[(dff.LAND_USE == 'CurNC_M') | (dff.LAND_USE == 'CurC_M'), 'LAND_USE'] = 'MF_Light'
    dff.loc[(dff.LAND_USE == 'CurNC_L') | (dff.LAND_USE == 'CurC_L'), 'LAND_USE'] = 'MF_Minimal'
    dff.loc[(dff.LAND_USE == 'CurNC') | (dff.LAND_USE == 'CurC'), 'LAND_USE'] = 'MF_Intense'
    dff.loc[(dff.LAND_USE == 'Cur0'), 'LAND_USE'] = 'SF'
    dff = dff.groupby(by=['Country', 'UNIT', 'LAND_USE', 'SCENARIO', 'YEAR']).sum(numeric_only=True)
    dff.reset_index(inplace=True)
    dfc = df0.groupby(by=['Country', 'UNIT', 'LAND_USE', 'SCENARIO', 'YEAR']).sum(numeric_only=True)
    dfc.reset_index(inplace=True)
    dfc = dfc.loc[(dfc.YEAR == year) & (dfc.SCENARIO == scenario)].copy()
    dfcf = dfc.loc[(dfc.LAND_USE == 'MngFor') | (dfc.LAND_USE == 'PriFor')].copy()
    df = dfc.loc[(dfc.LAND_USE != 'MngFor') & (dfc.LAND_USE != 'PriFor')].copy()
    df['f'] = 1
    for country in list(dfcf.Country.unique()):
        if country in list(dff.Country.unique()):
            forest_area_tot = dfcf.loc[dfcf.Country == country, 'VALUE'].sum()
            df_temp = dff.loc[dff.Country == country].copy()
            df_temp = df_temp.loc[(df_temp.LAND_USE.str.contains('MF')) |
                                  (df_temp.LAND_USE.str.contains('SF')) |
                                  (df_temp.LAND_USE.str.contains('Pri'))]
            if 'PriFor' in list(df_temp.LAND_USE.unique()):
                forest_area_pf = df_temp.loc[df_temp.LAND_USE == 'PriFor', 'VALUE'].sum()
            else:
                forest_area_pf = 0
            forest_area_mf = df_temp.loc[df_temp.LAND_USE != 'PriFor', 'VALUE'].sum()
            f = (forest_area_tot - forest_area_pf) / forest_area_mf
            if f < 0:
                f = 1
            df_temp.loc[df_temp.LAND_USE != 'PriFor', 'VALUE'] *= f
            df_temp['f'] = f
            df = pd.concat([df, df_temp], ignore_index=True)
    df.loc[(df.LAND_USE == 'NotRel') | (df.LAND_USE == 'OagLnd') | (df.LAND_USE == 'WetLnd'), 'LAND_USE'] = 'Other land'
    df = df.groupby(by=['Country', 'UNIT', 'LAND_USE', 'SCENARIO', 'YEAR', 'f']).sum(numeric_only=True)
    df.reset_index(inplace=True)
    return df


def add_crop_area_by_intensity(year, scenario):
    df = harmonize_land_use_from_two_globiom_models(year, scenario)
    df_c = df[df.LAND_USE == 'CrpLnd'].copy()
    df = df[df.LAND_USE != 'CrpLnd'].copy()
    df_ci = calculate_crop_land_use_intensity_percent()
    df_ci = df_ci[(df_ci.YEAR == year) & (df_ci.SCENARIO == scenario)].copy()
    for country in list(df_c.Country.unique()):
        if country in list(df_ci.Country.unique()):
            df_temp = df_c.loc[df_c.Country == country].copy()
            area_crop = df_c.loc[df_c.Country == country, 'VALUE'].iloc[0]
            for intensity in ['Intense', 'Light', 'Minimal']:
                colname1 = f'CR_{intensity}'
                ratio = df_ci.loc[df_ci.Country == country, colname1].iloc[0]
                df_temp['LAND_USE'] = colname1
                df_temp['VALUE'] = area_crop * ratio
                df = pd.concat([df, df_temp], ignore_index=True)
        else:
            df_temp = df_c.loc[df_c.Country == country].copy()
            df = pd.concat([df, df_temp], ignore_index=True)
    return df


def harmonize_land_use_all():
    try:
        df = pd.read_csv('data/interim/globiom_harmonized_land_use.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    except FileNotFoundError:
        df = pd.DataFrame()
        for scenario in ['scenRCPref', 'scenRCP1p9']:
            for year in [2000, 2010, 2020, 2030, 2040, 2050]:
                df_temp = add_crop_area_by_intensity(year, scenario)
                df = pd.concat([df, df_temp], ignore_index=True)
        df.to_csv('data/interim/globiom_harmonized_land_use.csv')
    return df


def calculate_land_use_net_change(focus_year, scenario):
    df0 = harmonize_land_use_all()
    df = df0[(df0.YEAR == focus_year) | (df0.YEAR == focus_year-20)].copy()
    df = df[df.SCENARIO == scenario].copy()
    df = pd.pivot_table(df, columns='YEAR', index=['Country', 'UNIT', 'LAND_USE', 'SCENARIO'],
                        values='VALUE')
    df = df.fillna(0)
    df['NET_CHANGE'] = df[focus_year] - df[focus_year-20]
    df.reset_index(inplace=True)
    return df


def calculate_mf_luc(focus_year, scenario, intensity):
    df0 = calculate_land_use_net_change(focus_year, scenario)
    land_use = f'MF_{intensity}'
    df_mf_area = df0.loc[df0.LAND_USE.str.contains('MF_')].copy()
    df_mf_area = pd.pivot_table(df_mf_area, values=focus_year, columns='LAND_USE', index='Country', aggfunc=sum)
    df_mf_area = df_mf_area.fillna(0)
    df_mf_area['SHARE'] = df_mf_area[land_use] / df_mf_area.sum(axis=1)
    df_mf_area = df_mf_area[['SHARE']]
    df_mf_area.reset_index(inplace=True)
    df = df0[df0.LAND_USE == land_use].copy()
    df['ALUC_to'] = df['NET_CHANGE'] / df[focus_year] / 20
    df.loc[df.ALUC_to < 0, 'ALUC_to'] = 0
    lu_from_list = ['CR_Intense', 'CR_Light', 'CR_Minimal', 'MF_Intense', 'MF_Light', 'MF_Minimal', 'SF', 'PriFor',
                    'GrsLnd',  'NatLnd']
    df[lu_from_list] = 0
    for country in list(df.Country.unique()):
        df_temp = df0[df0.Country == country].copy()
        for lu in lu_from_list:
            if lu in list(df_temp.LAND_USE.unique()):
                area = df_temp.loc[df_temp.LAND_USE == lu, 'NET_CHANGE'].iloc[0]
            else:
                area = 0
            df.loc[df.Country == country, lu] = area
    df_mf = df[['MF_Intense', 'MF_Light', 'MF_Minimal', 'SF', 'PriFor']].copy()
    df['MF_expansion'] = df_mf.where(df_mf > 0).sum(axis=1)
    df['MF_contraction'] = -df_mf.where(df_mf < 0).sum(axis=1)
    df['SEMF'] = df['MF_contraction'] / df['MF_expansion']
    df['SEMF'] = df['SEMF'].fillna(1)
    df.loc[df.SEMF > 1, 'SEMF'] = 1
    mf_list = ['MF_Intense', 'MF_Light', 'MF_Minimal', 'SF', 'PriFor']
    mf_list.remove(land_use)
    for lu in mf_list:
        colname = f'SE{lu}'
        df[colname] = -df[lu] / df['MF_contraction'] * df['SEMF']
        df.loc[df[colname] < 0, colname] = 0
        df[colname] = df[colname].fillna(0)
    non_mf_list = ['CR', 'GrsLnd', 'NatLnd']
    df['CR'] = df[['CR_Intense', 'CR_Light', 'CR_Minimal']].sum(axis=1)
    df_non_mf = df[non_mf_list].copy()
    df['non_MF_contraction'] = -df_non_mf.where(df_non_mf < 0).sum(axis=1)
    for lu in non_mf_list:
        colname = f'SE{lu}'
        df[colname] = -df[lu] / df['non_MF_contraction'] * (1-df['SEMF'])
        df.loc[df[colname] < 0, colname] = 0
        df[colname] = df[colname].fillna(0)
    cr_list = ['CR_Intense', 'CR_Light', 'CR_Minimal']
    df_cr = df[cr_list].copy()
    df['CR_contraction'] = -df_cr.where(df_cr < 0).sum(axis=1)
    for lu in cr_list:
        colname = f'SE{lu}'
        df[colname] = -df[lu] / df['CR_contraction'] * df['SECR']
        df.loc[df[colname] < 0, colname] = 0
        df[colname] = df[colname].fillna(0)
    colname = f'SE{land_use}'
    df[colname] = 0
    for lu in lu_from_list:
        colname = f'ALUC_from_{lu}'
        colname2 = f'SE{lu}'
        df[colname] = df[colname2] * df['ALUC_to']
    df = df.rename(columns={focus_year: 'AREA'})
    df = df[['Country', 'UNIT', 'LAND_USE', 'SCENARIO', 'AREA', 'ALUC_to',
             'ALUC_from_CR_Intense', 'ALUC_from_CR_Light', 'ALUC_from_CR_Minimal',
             'ALUC_from_MF_Intense', 'ALUC_from_MF_Light', 'ALUC_from_MF_Minimal', 'ALUC_from_SF', 'ALUC_from_PriFor',
             'ALUC_from_GrsLnd',  'ALUC_from_NatLnd']].copy()
    df = pd.merge(df, df_mf_area, on='Country', how='left')
    df['YEAR'] = focus_year
    return df


def mf_luc_all():
    df = pd.DataFrame()
    for scenario in ['scenRCPref', 'scenRCP1p9']:
        for year in [2020, 2030, 2040, 2050]:
            for intensity in ['Intense', 'Light', 'Minimal']:
                df_temp = calculate_mf_luc(year, scenario, intensity)
                df = pd.concat([df, df_temp], ignore_index=True)
    df.to_csv('data/interim/forest_luc_with_intensity.csv')
    return df


def calculate_single_crop_land_use_intensity_all_crops():
    df = read_globiom_crop_data_g()
    df = df[(df.ITEM == 'harvest_area') & (df.YEAR < 2051)].copy()
    df = pd.pivot_table(df, index=['COUNTRY', 'CROP', 'YEAR', 'SCENARIO'],
                        columns='TECH', values='VALUE', aggfunc='sum')
    df = df.fillna(0)
    df.reset_index(inplace=True)
    # df['CROP'] = df['CROP'].map(crop_dict)
    return df


def calculate_single_crop_land_net_change(focus_year, scenario):
    df0 = calculate_single_crop_land_use_intensity_all_crops()
    df = df0.loc[((df0.YEAR == focus_year) | (df0.YEAR == focus_year - 20)) & (df0.SCENARIO == scenario)].copy()
    df['CR_Intense'] = df['HI'] + df['IR']
    df.rename(columns={'LI': 'CR_Light', 'SS': 'CR_Minimal'}, inplace=True)
    df = df[['COUNTRY', 'CROP', 'YEAR', 'SCENARIO', 'CR_Intense', 'CR_Light', 'CR_Minimal']].copy()
    df_output = pd.DataFrame()
    for intensity in ['Intense', 'Light', 'Minimal']:
        colname = f'CR_{intensity}'
        df_temp = pd.pivot_table(df, index=['COUNTRY', 'CROP', 'SCENARIO'], columns='YEAR',
                                 values=colname, aggfunc='sum')
        df_temp = df_temp.fillna(0)
        df_temp['NET_CHANGE'] = df_temp[focus_year] - df_temp[focus_year-20]
        df_temp.reset_index(inplace=True)
        df_temp['LAND_USE'] = colname
        df_output = pd.concat([df_output, df_temp], ignore_index=True)
    df_output = df_output.rename(columns={focus_year: 'AREA'})
    df_country = get_country_match_df_globiom()
    df_output['Country'] = df_output['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_output = df_output[['Country', 'CROP', 'SCENARIO', 'AREA', 'LAND_USE', 'NET_CHANGE']]
    df_output['YEAR'] = focus_year
    return df_output


def calculate_crop_luc(focus_year, scenario, crop):
    cr_list = ['CR_Intense', 'CR_Light', 'CR_Minimal', 'CR_Intense_P', 'CR_Light_P', 'CR_Minimal_P']
    non_cr_list = ['MF', 'GrsLnd']
    mf_list = ['MF_Intense', 'MF_Light', 'MF_Minimal', 'SF', 'PriFor']
    luc_list = ['CR_Intense', 'CR_Light', 'CR_Minimal', 'CR_Intense_P', 'CR_Light_P', 'CR_Minimal_P',
                'GrsLnd', 'PriFor', 'MF_Intense', 'MF_Light', 'MF_Minimal']
    occ_name_dict = {'CR_Intense': 'Occupation, annual crop, intensive',
                     'CR_Light': 'Occupation, annual crop, extensive',
                     'CR_Minimal': 'Occupation, annual crop, minimal'}
    tra_to_name_dict = {'CR_Intense': 'Transformation, to annual crop, intensive',
                        'CR_Light': 'Transformation, to annual crop, extensive',
                        'CR_Minimal': 'Transformation, to annual crop, minimal'}
    tra_from_name_dict = {'ALUC_from_CR_Intense': 'Transformation, from annual crop, intensive',
                          'ALUC_from_CR_Light': 'Transformation, from annual crop, extensive',
                          'ALUC_from_CR_Minimal': 'Transformation, from annual crop, minimal',
                          'ALUC_from_CR_Intense_P': 'Transformation, from permanent crop',
                          'ALUC_from_CR_Light_P': 'Transformation, from permanent crop, extensive',
                          'ALUC_from_CR_Minimal_P': 'Transformation, from permanent crop, minimal',
                          'ALUC_from_MF_Intense': 'Transformation, from forest, intensive',
                          'ALUC_from_MF_Light': 'Transformation, from forest, extensive',
                          'ALUC_from_MF_Minimal': 'Transformation, from shrub land, sclerophyllous',
                          'ALUC_from_SF': 'Transformation, from forest, minimal',
                          'ALUC_from_GrsLnd': 'Transformation, from grassland, natural, for livestock grazing',
                          'ALUC_from_NatLnd': 'Transformation, from grassland, natural, for livestock grazing'}
    df_luc = calculate_land_use_net_change(focus_year, scenario)
    df_luc['LAND_USE_2'] = df_luc['LAND_USE'].copy()
    df_luc.loc[df_luc.LAND_USE.str.contains('MF_'), 'LAND_USE_2'] = 'MF'
    df_luc.loc[df_luc.LAND_USE == 'SF', 'LAND_USE_2'] = 'MF'
    df_luc.loc[df_luc.LAND_USE == 'PriFor', 'LAND_USE_2'] = 'MF'
    df_luc.loc[df_luc.LAND_USE == 'NatLnd', 'LAND_USE_2'] = 'GrsLnd'
    df_luc_agg = df_luc.groupby(by=['Country', 'UNIT', 'SCENARIO', 'LAND_USE_2']).sum(numeric_only=True)
    df_luc_agg.reset_index(inplace=True)
    df_crop_all = calculate_single_crop_land_net_change(focus_year, scenario)
    df_crop_all.loc[df_crop_all.CROP == 'OPAL', 'LAND_USE'] += '_P'
    df = df_crop_all.loc[df_crop_all.CROP == crop].copy()
    df['ALUC_to'] = df['NET_CHANGE'] / df['AREA'] / 20
    df.loc[df.ALUC_to < 0, 'ALUC_to'] = 0
    df.loc[df.AREA == 0, 'ALUC_to'] = 0
    df_output = pd.DataFrame()
    for country in list(df.Country.unique()):
        # 1. change within cropland
        df_temp = df.loc[df.Country == country].copy()
        df_temp2 = df_crop_all[df_crop_all.Country == country]
        df_temp3 = df_crop_all.loc[df_crop_all.Country == country, ['NET_CHANGE']].copy()
        area_expansion_all_crop = df_temp3.where(df_temp3 > 0).sum()[0]
        area_contraction_all_crop = - df_temp3.where(df_temp3 < 0).sum()[0]
        if area_expansion_all_crop > 0:
            r = area_contraction_all_crop / area_expansion_all_crop
            if r > 1:
                r = 1
        else:
            r = 1
        df_temp['SECR'] = r
        for lu in cr_list:
            colname = f'SE{lu}'
            df_temp[colname] = 0
            if df_temp2.loc[(df_temp2.LAND_USE == lu) &
                            (df_temp2.NET_CHANGE < 0)].shape[0] > 0:
                area_contration_single = -df_temp2.loc[(df_temp2.LAND_USE == lu) &
                                                       (df_temp2.NET_CHANGE < 0), 'NET_CHANGE'].sum()
            else:
                area_contration_single = 0
            if area_contraction_all_crop != 0:
                df_temp[colname] = area_contration_single / area_contraction_all_crop * df_temp['SECR']
        # 2. change from forest and grassland
        df_luc_temp = df_luc_agg[df_luc_agg.Country == country].copy()
        df_luc_temp = df_luc_temp[df_luc_temp.LAND_USE_2.isin(non_cr_list)]
        df_luc_temp['Contraction'] = 0
        df_luc_temp.loc[df_luc_temp.NET_CHANGE < 0, 'Contraction'] = -df_luc_temp.loc[df_luc_temp.NET_CHANGE < 0,
                                                                                      'NET_CHANGE']
        if df_luc_temp['Contraction'].sum() > 0:
            df_luc_temp['Share'] = df_luc_temp['Contraction'] / df_luc_temp['Contraction'].sum()
        else:
            df_luc_temp['Share'] = 0
        df_mf_temp = df_luc[df_luc.Country == country].copy()
        df_mf_temp = df_mf_temp[df_mf_temp.LAND_USE.isin(mf_list)]
        df_mf_temp['Contraction'] = 0
        df_mf_temp.loc[df_mf_temp.NET_CHANGE < 0, 'Contraction'] = -df_mf_temp.loc[df_mf_temp.NET_CHANGE < 0,
        'NET_CHANGE']
        if df_mf_temp['Contraction'].sum() > 0:
            df_mf_temp['Share'] = df_mf_temp['Contraction'] / df_mf_temp['Contraction'].sum()
        else:
            df_mf_temp['Share'] = 0
        for lu in non_cr_list:
            colname = f'SE{lu}'
            df_temp[colname] = 0
            if lu in list(df_luc_temp.LAND_USE_2.unique()):
                lu_share = df_luc_temp.loc[df_luc_temp.LAND_USE_2 == lu, 'Share'].iloc[0]
                df_temp[colname] = (1-df_temp['SECR']) * lu_share
        for lu in mf_list:
            colname = f'SE{lu}'
            df_temp[colname] = 0
            if lu in list(df_mf_temp.LAND_USE.unique()):
                lu_share = df_mf_temp.loc[df_mf_temp.LAND_USE == lu, 'Share'].iloc[0]
                df_temp[colname] = df_temp['SEMF'] * lu_share
        df_temp['Intensity_share'] = df_temp['AREA'] / df_temp['AREA'].sum()
        df_temp['SEMF_Minimal'] = df_temp['SEMF_Minimal'] + df_temp['SESF']
        for lu in luc_list:
            colname1 = f'SE{lu}'
            colname2 = f'ALUC_from_{lu}'
            df_temp[colname2] = df_temp[colname1] * df_temp['ALUC_to']
        df_temp_output = df_temp.iloc[0:1][['Country', 'CROP', 'SCENARIO', 'YEAR']].copy()
        for lu in ['CR_Intense', 'CR_Light', 'CR_Minimal']:
            if lu in df_temp.LAND_USE.unique():
                intensity_share = df_temp.loc[df_temp.LAND_USE == lu, 'Intensity_share'].iloc[0]
                aluc_to = df_temp.loc[df_temp.LAND_USE == lu, 'ALUC_to'].iloc[0]
                df_temp_output[occ_name_dict[lu]] = intensity_share * 10000
                df_temp_output[tra_to_name_dict[lu]] = aluc_to * intensity_share * 10000
            else:
                df_temp_output[occ_name_dict[lu]] = 0
                df_temp_output[tra_to_name_dict[lu]] = 0
        for lu in luc_list:
            if lu != 'PriFor':
                colname = f'ALUC_from_{lu}'
                aluc_from = df_temp['Intensity_share'] * df_temp[colname]
                df_temp_output[tra_from_name_dict[colname]] = aluc_from.sum() * 10000
        df_output = pd.concat([df_output, df_temp_output], ignore_index=True)
    df_output = df_output.dropna()
    return df_output


def calculate_crop_luc_all():
    df = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCPref', 'scenRCP1p9']:
            for crop in crop_globiom_list:
                df_temp = calculate_crop_luc(year, scenario, crop)
                df = pd.concat([df, df_temp], ignore_index=True)
    df['Crop'] = df['CROP'].map(crop_dict)
    df.to_csv('data/interim/crop_luc.csv')
    return df
