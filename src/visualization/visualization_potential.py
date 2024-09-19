from src.visualization.visualization_lcia import get_world_shape_file
from src.data.globiom_residue_potential import all_residue_available_potential_g_no_scenario
from src.other.colors import color6_old, cmp_yellow_green, color_purple
from src.other.name_match import get_country_match_df_globiom

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import plotly.express as px


def map_potential(year, potential_type):
    df0 = all_residue_available_potential_g_no_scenario()
    df = df0[df0.YEAR == year].copy()
    df = df.groupby(by=['LU_GRID', 'COUNTRY', 'YEAR']).sum(numeric_only=True)
    df.reset_index(inplace=True)
    world_shape = get_world_shape_file()
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    world_shape.plot(color='#a2a3a5', ax=ax)
    lu_shape = gpd.read_file(f'data/external/shapefiles/LUID_CTY/LUID_CTY.shp')
    lu_shape = lu_shape.rename(columns={'Field2': 'COUNTRY', 'Field1_1': 'LU_GRID'})
    gdf = pd.merge(lu_shape, df, how='right', on=['COUNTRY', 'LU_GRID'])
    gdf1 = gdf.to_crs({'proj': 'cea'})
    gdf['Area'] = gdf1['geometry'].area / 10 ** 6
    gdf['AVAI_MAX'] *= 1000
    gdf['AVAI_MIN'] *= 1000
    gdf['AVAI_MAX'] /= gdf['Area'] #t/km2
    gdf['AVAI_MIN'] /= gdf['Area'] #t/km2
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.1)
    gdf.plot(column=potential_type, ax=ax, legend=True, cax=cax, vmin=0, vmax=250, cmap=cmp_yellow_green())
    ax.axis('off')
    figname = f'figures/potential/potential_{year}_{potential_type}_tonne_per_km2.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()


def stack_plot_by_biomass_type():
    df0 = all_residue_available_potential_g_no_scenario()
    df0['CAT'] = 'Other agricultural residues'
    df0.loc[df0.CAT1 == 'Forestry', 'CAT'] = 'Forest residues'
    df0.loc[df0.RESIDUE.str.contains('Rice'), 'CAT'] = 'Rice'
    df0.loc[df0.RESIDUE.str.contains('Maize'), 'CAT'] = 'Maize'
    df0.loc[df0.RESIDUE.str.contains('Wheat'), 'CAT'] = 'Wheat'
    df0.loc[df0.RESIDUE.str.contains('Sugarcane'), 'CAT'] = 'Sugarcane'
    df0 = df0[df0.YEAR < 2051].copy()
    df = df0.groupby(by=['YEAR', 'CAT']).sum(numeric_only=True)
    df /= 1000000 #GT
    df.reset_index(inplace=True)
    df.sort_values(by='YEAR', inplace=True)
    pds_max = []
    pds_min = []
    year_list = list(df.YEAR.unique())
    cat_list = ['Forest residues', 'Maize', 'Rice', 'Sugarcane', 'Wheat', 'Other agricultural residues']
    for cat in cat_list:
        pds_max.append(df[df.CAT == cat]['AVAI_MAX'].values)
        pds_min.append(df[df.CAT == cat]['AVAI_MIN'].values)
    fig, ax = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    ax[0].stackplot(year_list, pds_min, colors=color6_old, labels=cat_list, edgecolors='white')
    ax[0].set_xlim([2000, 2050])
    ax[1].stackplot(year_list, pds_max, colors=color6_old, labels=cat_list, edgecolors='white')
    ax[1].set_xlim([2000, 2050])
    handles, labels = ax[1].get_legend_handles_labels()
    ax[1].legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(-0.85, 1), ncol=1)
    figname = f'figures/potential/potential_stack_plot.pdf'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()
    return df


def bar_plot_methanol_demand():
    chemicals = ['Methanol', 'Olefins', 'BTX-aromatics']
    scenarios = ['Minimum', 'Maximum']
    methanol = [0.146, 0.224]#Gt
    olefins = [0.774, 1.236]
    btx = [0.476, 0.747]

    fig, ax = plt.subplots(figsize=(5, 5))
    plt.bar(scenarios, methanol, color=color_purple[0], width=0.5)
    plt.bar(scenarios, olefins, bottom=methanol, color=color_purple[1], width=0.5)
    plt.bar(scenarios, btx, bottom=[x + y for x, y in zip(methanol, olefins)], color=color_purple[2], width=0.5)
    plt.tick_params(bottom=False)
    plt.ylabel('Gt methanol')
    fig.savefig("figures/potential/methanol_demand.pdf", bbox_inches='tight')
    plt.show()


def bar_plot_potential_top_countries(year):
    df0 = all_residue_available_potential_g_no_scenario()
    df0['CAT'] = 'Other agricultural residues'
    df0.loc[df0.CAT1 == 'Forestry', 'CAT'] = 'Forest residues'
    df0.loc[df0.RESIDUE.str.contains('Rice'), 'CAT'] = 'Rice'
    df0.loc[df0.RESIDUE.str.contains('Maize'), 'CAT'] = 'Maize'
    df0.loc[df0.RESIDUE.str.contains('Wheat'), 'CAT'] = 'Wheat'
    df0.loc[df0.RESIDUE.str.contains('Sugarcane'), 'CAT'] = 'Sugarcane'
    df0 = df0[df0.YEAR == year].copy()
    df = df0.groupby(by=['COUNTRY', 'CAT']).sum(numeric_only=True)
    df.reset_index(inplace=True)
    df_country = get_country_match_df_globiom()
    df['Country'] = df['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_temp = df.groupby(by=['Country']).sum(numeric_only=True)
    df_temp.reset_index(inplace=True)
    df_temp = df_temp.sort_values(by='AVAI_MAX', ascending=False)
    country_list_max = list(df_temp.Country.unique())[0:10]
    df_temp = df_temp.sort_values(by='AVAI_MIN', ascending=False)
    country_list_min = list(df_temp.Country.unique())[0:10]
    cat_list = ['Forest residues', 'Maize', 'Rice', 'Sugarcane', 'Wheat', 'Other agricultural residues']
    df1 = df.loc[df.Country.isin(country_list_max)]
    fig = px.bar(df1, x='Country', y='AVAI_MAX', color='CAT',
                 category_orders={'Country': country_list_max,
                                  'CAT': cat_list},
                color_discrete_sequence=color6_old)
    fig.update_layout(barmode='stack',
                      template=None,
                      width=1500,
                      height=500,
                      legend_traceorder='reversed',
                      )
    fig.update_yaxes(showgrid=False)
    fig.write_image(f'figures/potential/max_potential_by_country_stacked_bar.pdf')
    fig.show()
    df2 = df.loc[df.Country.isin(country_list_min)]
    fig = px.bar(df2, x='Country', y='AVAI_MIN', color='CAT',
                 category_orders={'Country': country_list_min,
                                  'CAT': cat_list},
                 color_discrete_sequence=color6_old)
    fig.update_layout(barmode='stack',
                      template=None,
                      width=1500,
                      height=500,
                      # legend_traceorder='reversed',
                      showlegend=False
                      )
    fig.update_yaxes(showgrid=False)
    fig.write_image(f'figures/potential/min_potential_by_country_stacked_bar.pdf')
    fig.show()

