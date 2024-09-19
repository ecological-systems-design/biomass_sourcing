import os
import pandas as pd
import geopandas as gpd


# local import
from src.old.agriculture_lci import calculate_single_crop_land_use_intensity
from src.other.name_match import (get_country_match_df_globiom)


def add_shapefile_to_residue_grid_df():
    if os.path.exists(r'data/interim/GLOBIOM_all_residue_g_processed.csv'):
        df0 = pd.read_csv(r'data/interim/GLOBIOM_all_residue_g_processed.csv', index_col=0)
    else:
        from src.old.GLOBIOM_residue_potential import export_all_residues_g
        df0 = export_all_residues_g()

    lu_shape = gpd.read_file("data/external/shapefiles/LUID_CTY/LUID_CTY.shp")
    lu_shape = lu_shape.rename(columns={"Field2": "COUNTRY", "Field1_1": "LU_GRID"})
    df = pd.merge(lu_shape, df0, on=['LU_GRID', 'COUNTRY'], how='right')
    return df


def dash_map_all_potential():
    df0 = add_shapefile_to_residue_grid_df()
    df_all = df0.groupby(by=['COUNTRY', 'LU_GRID', 'geometry', 'UNIT', 'YEAR', 'SCENARIO']).sum(numeric_only=True)
    df_all.reset_index(inplace=True)
    df_all['CAT'] = 'All lignocellulose biomass residues'
    df_cat1 = df0.groupby(by=['COUNTRY', 'LU_GRID', 'geometry',
                              'UNIT', 'YEAR', 'SCENARIO', 'CAT1']).sum(numeric_only=True)
    df_cat1.reset_index(inplace=True)
    df_cat1 = df_cat1.rename(columns={'CAT1': 'CAT'})
    df_cat1.loc[df_cat1.CAT == 'Agricultural', 'CAT'] = 'All crop residues'
    df_cat1.loc[df_cat1.CAT == 'Forestry', 'CAT'] = 'All forest residues'

    df = pd.concat([df_cat1, df_all], ignore_index=True)
    df = df[['COUNTRY', 'LU_GRID', 'geometry', 'UNIT', 'YEAR', 'SCENARIO', 'CAT', 'AVAI_MIN', 'AVAI_MAX']].copy()
    df = df[df.YEAR < 2051].copy()
    df = df.sort_values(by='YEAR')
    df = df[df.AVAI_MAX != 0].copy()
    print('start saving')
    df.to_csv(r'data/processed/dash_all_residue_map.csv')
    # df.to_csv(r'C:/Users/Huo/PycharmProjects/biomass_dash/data/dash_all_residue_map.csv')
    return df


def dash_crop_land_use_intensity_percent():
    intensity_list = ['HI', 'IR', 'LI', 'SS']
    intensity_explanation_list = ['High input', 'High input, irrigation', 'Low input', 'Self-sustaining']
    intensity_dict = {intensity_list[i]: intensity_explanation_list[i] for i in range(len(intensity_explanation_list))}
    df = calculate_single_crop_land_use_intensity()
    df_country = get_country_match_df_globiom()
    df['REGION'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['Region_Group_Paper_2'])
    df['REGION_STANDARD'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['Country'])
    df_r = df.groupby(by=['REGION', 'CROP', 'SCENARIO', 'YEAR']).sum()
    df_r.reset_index(inplace=True)
    df_r = df_r[df_r.REGION.isin(['ASEAN', 'EU', 'RAF', 'RME'])].copy()
    df_r.rename(columns={"REGION": "REGION_STANDARD"}, inplace=True)
    df_g = df.groupby(by=['CROP', 'SCENARIO', 'YEAR']).sum()
    df_g.reset_index(inplace=True)
    df_g['REGION_STANDARD'] = 'GLOBAL'
    df = df[['REGION_STANDARD', 'CROP', 'YEAR', 'SCENARIO', 'HI', 'IR', 'LI', 'SS']].copy()
    df = pd.concat([df_g, df_r, df], ignore_index=True)
    df_percent = df.copy()
    for x in intensity_list:
        df_percent[x] = df_percent[x] / df[intensity_list].sum(axis=1, numeric_only=True)
    df_percent = df_percent.rename(columns=intensity_dict)
    df_percent.to_csv(r'data/processed/dash_crop_intensity_percentage.csv')
    return df_percent


