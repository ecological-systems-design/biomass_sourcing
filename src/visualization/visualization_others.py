from src.data.land_use_change import harmonize_land_use_all
from src.data.agriculture_lci import calculate_fertilizer_products
from src.other.colors import color_contribution_old, diverging_colors, color37
from src.bw.bw_lcia import lcia_crop_add_price
from src.bw.bw_scenario_set_up import bw_scenario_set_up

import os
import pandas as pd
import seaborn as sns
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.axes_grid1 import make_axes_locatable


from src.visualization.visualization_lcia import get_world_shape_file
from src.other.country_match import get_country_match_df_globiom


def plot_country_land_use(country):
    df = harmonize_land_use_all()
    if country == 'global':
        dfc = df.copy()
    else:
        dfc = df[df.Country == country].copy()
    dfc = dfc.pivot_table(index=['UNIT', 'SCENARIO', 'YEAR'], columns='LAND_USE', values='VALUE', aggfunc='sum')
    dfc = dfc.fillna(0)
    dfc_temp = dfc.copy()
    cat_list = ['PriFor', 'SF', 'MF_Minimal', 'MF_Light', 'MF_Intense', 'PltFor', 'AfrLnd',
                'CR_Minimal', 'CR_Light', 'CR_Intense', 'GrsLnd', 'NatLnd', 'Other land', ]
    color_list = [color_contribution_old[0], color_contribution_old[1],
                  color_contribution_old[2], color_contribution_old[2],
                  color_contribution_old[2], color_contribution_old[2],
                  color_contribution_old[4], color_contribution_old[5],
                  color_contribution_old[5], color_contribution_old[5],
                  color_contribution_old[6], color_contribution_old[7],
                  color_contribution_old[-1]]
    hatch_list = ['', '', '\\\\\\', '||', '///', '...', '', '\\\\\\', '||', '///', '', '', '']
    for cat in cat_list:
        if cat not in list(dfc.columns):
            dfc[cat] = 0
            dfc_temp[cat] = 0
        dfc[cat] = dfc_temp[cat] / dfc_temp.sum(axis=1)
    dfc.reset_index(inplace=True)
    dfc.sort_values(by='YEAR', inplace=True)
    dfc['CR'] = dfc['CR_Minimal'] + dfc['CR_Light'] + dfc['CR_Intense']
    dfc['FR'] = dfc['PriFor'] + dfc['MF_Minimal'] + dfc['MF_Light'] + dfc['MF_Intense'] + dfc['PltFor']
    pds_ref = []
    pds_1p9 = []
    year_list = list(dfc.YEAR.unique())
    for cat in cat_list:
        pds_ref.append(dfc[(dfc.SCENARIO == 'scenRCPref')][cat].values)
        pds_1p9.append(dfc[(dfc.SCENARIO == 'scenRCP1p9')][cat].values)
    fig, ax = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    stack1 = ax[0].stackplot(year_list, pds_ref, labels=cat_list, edgecolors='white', colors=color_list)
    for stack, hatch in zip(stack1, hatch_list):
        stack.set_hatch(hatch)
    ax[0].set_xlim([2000, 2050])
    ax[0].set_ylim([0, 1])
    ax[1].stackplot(year_list, pds_1p9, labels=cat_list, edgecolors='white', colors=color_list)
    ax[1].set_xlim([2000, 2050])
    ax[1].set_ylim([0, 1])
    handles, labels = ax[1].get_legend_handles_labels()
    for handle, hatch in zip(handles, hatch_list):
        handle.set_hatch(hatch)
    ax[1].legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(1.2, 1.1), ncol=1)
    figname = f'figures/temporal_lcia/land_use_{country}.pdf'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()
    a=0


def plot_fertilizer():
    if os.path.exists(r'data/interim/crop_lci_fertilizer_dose.csv'):
        df = pd.read_csv(r'data/interim/crop_lci_fertilizer_dose.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = calculate_fertilizer_products()
    df1 = pd.pivot_table(df, columns='SCENARIO', index=['Crop', 'Country', 'YEAR'], values='N_kg_per_ha')
    df1 = df1.dropna(axis=0)
    df1.reset_index(inplace=True)
    df1 = df1[df1.Country == 'CN']
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    sns.scatterplot(data=df1, x='scenRCPref', y='scenRCP1p9')
    ax.plot([0, 500], [0, 500])
    fig.show()


def plot_crop_impact_per_ha_land(price):
    df = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCP1p9', 'scenRCPref']:
            bw_scenario_set_up(year, scenario)
            df_temp = lcia_crop_add_price(year, scenario, price)
            df_temp['SCENARIO'] = scenario
            df_temp['YEAR'] = year
            df = pd.concat([df, df_temp], axis=0)
    df1 = pd.pivot_table(df, columns='SCENARIO', index=['Product', 'Country', 'YEAR'], values='GHG')
    df1 = df1.dropna(axis=0)
    df1.reset_index(inplace=True)
    # df1 = df1[df1.Country == 'CN']
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    sns.scatterplot(data=df1, x='scenRCPref', y='scenRCP1p9')
    fig.show()


def plot_carbon_price_and_bioenergy_demand():
    carbon_price_1p9 = [0.01, 0.01, 0.01, 58.905, 83.21, 135.54]  # 2000--2050
    carbon_price_ref = [0.01] * 6
    bioenergy_demand_ref = [41, 52, 57, 58.0825, 59.165, 60.2475]
    bioenergy_demand_1p9 = [41, 52, 57, 78.0666, 99.1333, 120.2]
    year = list(range(2000, 2060, 10))
    x = np.arange(len(year))  # the label locations
    width = 0.3  # the width of the bars
    fig, ax = plt.subplots(2, 1, figsize=(10, 5), dpi=600, sharex=True)
    ax[0].bar(x - width / 2, carbon_price_ref, width, label='RCP6.5', color=color_contribution_old[5])
    ax[0].bar(x + width / 2, carbon_price_1p9, width, label='RCP1.9', color=color_contribution_old[1])
    ax[1].bar(x - width / 2, bioenergy_demand_ref, width, label='RCP6.5', color=color_contribution_old[5])
    ax[1].bar(x + width / 2, bioenergy_demand_1p9, width, label='RCP1.9', color=color_contribution_old[1])
    ax[0].set_title('Carbon price')
    ax[0].set_ylabel('$')
    ax[0].set_xticks(x, year)
    ax[1].set_title('Solid bioenergy demand')
    ax[1].set_ylabel('EJ')
    ax[0].legend(loc='upper left', ncols=2)
    plt.savefig(r'figures/carbon_price_and_solid_bioenergy_demand_by_year_and_scenario.pdf')
    plt.savefig(r'figures/carbon_price_and_solid_bioenergy_demand_by_year_and_scenario.png')
    plt.show()


def plot_globiom_region_map():
    df0 = get_country_match_df_globiom()
    world_shape = get_world_shape_file()
    world_shape.rename(columns={'Country': 'ISO2'}, inplace=True)
    df = pd.merge(df0, world_shape, on='ISO2', how='right')
    df = gpd.GeoDataFrame(df, geometry=df.geometry)
    from src.data.globiom_residue_potential import globiom_crop_data_with_crops_in_scope
    df1 = globiom_crop_data_with_crops_in_scope()
    df1['Region'] = df1['COUNTRY'].map(df0.set_index('GLOBIOM')['GLOBIOM_region'])
    df2 = pd.pivot_table(df1, index=['SCENARIO', 'YEAR', 'COUNTRY'], columns='ITEM',
                         values='VALUE', aggfunc='sum').reset_index()
    df2 = df2.loc[(df2.SCENARIO=='scenRCP1p9') & (df2.YEAR==2050)]
    df2 = pd.merge(df, df2, left_on='GLOBIOM', right_on='COUNTRY', how='left')
    df2 = gpd.GeoDataFrame(df2, geometry=df.geometry)
    df2['YIELD'] = df2['production'] / df2['harvest_area']
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", color37)
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    df.plot(column='GLOBIOM_region', ax=ax, legend=True, categorical=True,
            cmap=cmap, linewidth=.6, edgecolor='0.2',
            legend_kwds={'bbox_to_anchor': (1.1, 1.05), 'frameon': False},
            missing_kwds={'color': 'white', 'label': 'Missing values'})
    ax.axis('off')
    plt.savefig(r'figures/globiom_region_map.pdf')
    plt.show()
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    df2.plot(column='production', ax=ax, legend=True, linewidth=.6, edgecolor='0.2', vmax=1e5,
            missing_kwds={'color': 'white', 'label': 'Missing values'})
    ax.axis('off')
    plt.title('Production (kT)')

    plt.show()

    df3 = pd.read_csv('data/interim/GLOBIOM_all_residue_c_processed.csv')
    df3 = pd.pivot_table(df3, index=['Country', 'YEAR', 'CAT1'], values='AVAI_MAX').reset_index()
    df4 = df3.loc[(df3.YEAR==2050) & (df3.CAT1.isin(['Forestry']))]
    df4 = pd.merge(df, df4, left_on='ISO2', right_on='Country', how='left')
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    df4.plot(column='AVAI_MAX', ax=ax, legend=True, categorical=True,
            cmap=cmap, linewidth=.6, edgecolor='0.2',
            missing_kwds={'color': 'white', 'label': 'Missing values'})
    ax.axis('off')
    plt.show()
    return df


def plot_image_region_map():
    df0 = get_country_match_df_globiom()
    df0 = df0[['IMAGE_region', 'ISO2']]
    world_shape = get_world_shape_file()
    world_shape.rename(columns={'Country': 'ISO2'}, inplace=True)
    world_shape = world_shape[['ISO2', 'geometry']]
    df = pd.merge(df0, world_shape, on='ISO2', how='right')
    df = gpd.GeoDataFrame(df, geometry=df.geometry)
    df = df.dissolve(by='IMAGE_region')
    df = df.reset_index()
    df = df[['IMAGE_region', 'geometry']]
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    df.plot(column='IMAGE_region', ax=ax, legend=True, categorical=True,
            linewidth=.6, edgecolor='0.2',
            legend_kwds={'bbox_to_anchor': (1.1, 1.05), 'frameon': False},
            missing_kwds={'color': 'white', 'label': 'Missing values'})
    ax.axis('off')
    fig.show()
    output_path = r'data/processed/image_region_shapefile.shp'
    df.to_file(output_path, driver='ESRI Shapefile')
    return df