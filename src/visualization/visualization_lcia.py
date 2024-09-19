import os
import geopandas as gpd
import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from matplotlib.colors import ListedColormap
from plotly.subplots import make_subplots

from src.bw.bw_lcia import lcia_all, lcia_crop_ghg_contribution, lcia_crop_add_price
from src.other.colors import (color6_old, cmp_yellow_orange,
                              color_dict_residue)
from src.other.name_match import product_list, residue_crop_dict, get_country_match_df
from src.other.read_globiom_data import read_globiom_forest_rotation_data

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42


def get_lcia_df(year, scenario, price):
    file_name = f'data/interim/lcia_all_residues_{year}_{scenario}_{price}.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = lcia_all(year, scenario, price)
    return df


def get_ghg_contribution_df(year, scenario):
    df = lcia_crop_ghg_contribution(year, scenario)
    return df


def get_residue_potential(year, scenario):
    file_name = 'data/interim/GLOBIOM_all_residue_c_processed.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'].fillna('NA')
    else:
        from src.data.globiom_residue_potential import export_all_residues_c
        df = export_all_residues_c()
    df = df[(df.YEAR == year)].copy()
    return df


def get_world_shape_file():
    world_shape = gpd.read_file("data/external/shapefiles/World_Countries_(Generalized)/"
                                "World_Countries__Generalized_.shp")
    world_shape.rename(columns={'ISO': 'Country'}, inplace=True)
    world_shape = world_shape.loc[(world_shape.COUNTRY != 'Canarias') &
                                  (world_shape.COUNTRY != 'Azores') &
                                  (world_shape.COUNTRY != 'Madeira')]
    world_shape = world_shape.loc[world_shape.COUNTRY != 'Antarctica'].copy()
    return world_shape


def combine_potential_and_impact(year, scenario, price):
    df1 = get_lcia_df(year, scenario, price)
    df2 = get_residue_potential(year, scenario)
    df3 = read_globiom_forest_rotation_data()
    df = pd.merge(df1, df2, on=['Product', 'Country'], how='left')
    df = pd.merge(df, df3, on=['Country'], how='left')
    df.loc[df.CAT1 != 'Forestry', 'ROTATION_PERIOD'] = 1
    df['GHG_EOL'] = 0
    df.loc[df.ROTATION_PERIOD == 60, 'GHG_EOL'] = 0.5 / 12 * 44 * 0.25
    df.loc[df.ROTATION_PERIOD == 100, 'GHG_EOL'] = 0.5 / 12 * 44 * 0.44
    df.loc[df.ROTATION_PERIOD == 120, 'GHG_EOL'] = 0.5 / 12 * 44 * 0.54
    df['GHG_TOT'] = df['GHG'] + df['GHG_EOL']
    df['SUST'] = (df['SUST_MIN'] + df['SUST_MAX']) / 2
    df['GHGxSUST'] = df['GHG'] * df['SUST']
    df['GHG_TOTxSUST'] = df['GHG_TOT'] * df['SUST']
    df['BDVxSUST'] = df['BDV'] * df['SUST']
    df['BDV_TRAxSUST'] = df['BDV_TRA'] * df['SUST']
    df['BDV_OCCxSUST'] = df['BDV_OCC'] * df['SUST']
    df['WATERxSUST'] = df['WATER'] * df['SUST']
    df['GTPxSUST'] = df['GTP'] * df['SUST']
    global_ghg = df['GHGxSUST'].sum() / df['SUST'].sum()
    global_water = df['WATERxSUST'].sum() / df['SUST'].sum()
    global_bdv = df['BDVxSUST'].sum() / df['SUST'].sum()
    print(f"Global GHG: {global_ghg}" + '\n' + f"Global WATER: {global_water}" + '\n' + f"Global BDV: {global_bdv}")
    df_cat1 = df.groupby(by=['CAT1']).sum(numeric_only=True)
    df_cat1['GHG'] = df_cat1['GHGxSUST'] / df_cat1['SUST']
    df_cat1['GHG_TOT'] = df_cat1['GHG_TOTxSUST'] / df_cat1['SUST']
    df_cat1['BDV'] = df_cat1['BDVxSUST'] / df_cat1['SUST']
    df_cat1['BDV_TRA'] = df_cat1['BDV_TRAxSUST'] / df_cat1['SUST']
    df_cat1['BDV_OCC'] = df_cat1['BDV_OCCxSUST'] / df_cat1['SUST']
    df_cat1['WATER'] = df_cat1['WATERxSUST'] / df_cat1['SUST']
    print(f'Global agricultural GHG: {df_cat1.loc["Agricultural", "GHG"]}' + '\n'
          + f'Global agricultural WATER: {df_cat1.loc["Agricultural", "WATER"]}' + '\n'
          + f'Global agricultural BDV: {df_cat1.loc["Agricultural", "BDV"]}')
    print(f'Global forestry GHG: {df_cat1.loc["Forestry", "GHG"]}' + '\n'
            + f'Global forestry WATER: {df_cat1.loc["Forestry", "WATER"]}' + '\n'
            + f'Global forestry BDV: {df_cat1.loc["Forestry", "BDV"]}')
    df.to_csv(f'data/interim/combined_potential_impacts_{year}_{scenario}_price_{price}.csv')
    return df


def get_df_combined_potential_impacts(year, scenario, price):
    file_name = f'data/interim/combined_potential_impacts_{year}_{scenario}_price_{price}.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'].fillna('NA')
    else:
        df = combine_potential_and_impact(year, scenario, price)
    df.loc[df.CAT1 == 'Forestry', 'Product'] = 'Forest residues'
    return df



def recalculate_impacts(df):
    df.reset_index(inplace=True)
    df['GHG'] = df['GHGxSUST'] / df['SUST']
    df['GHG_TOT'] = df['GHG_TOTxSUST'] / df['SUST']
    df['BDV'] = df['BDVxSUST'] / df['SUST']
    df['BDV_TRA'] = df['BDV_TRAxSUST'] / df['SUST']
    df['BDV_OCC'] = df['BDV_OCCxSUST'] / df['SUST']
    df['WATER'] = df['WATERxSUST'] / df['SUST']
    if 'GTP' in df.columns:
        df['GTP'] = df['GTPxSUST'] / df['SUST']
    return df


def all_potential_impacts_with_aggregate_forest_impact(year, scenario, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df = df.groupby(by=['Product', 'Country', 'CAT1']).sum(numeric_only=True)
    df = recalculate_impacts(df)
    df = df[['Product', 'Country', 'GHG', 'GHG_TOT',
             'BDV', 'BDV_TRA', 'BDV_OCC', 'WATER', 'GTP', 'AVAI_MIN', 'AVAI_MAX']].copy()
    filename = f'data/interim/lcia_aggregated_residue_{year}_{scenario}.csv'
    df.to_csv(filename)
    return df


def aggregate_impact_no_biomass_cat(year, scenario, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df = df.groupby(by=['Country']).sum(numeric_only=True)
    df = recalculate_impacts(df)
    df = df[['Country', 'GHG', 'GHG_TOT', 'BDV', 'BDV_TRA', 'BDV_OCC', 'WATER', 'GTP', 'AVAI_MIN', 'AVAI_MAX']].copy()
    filename = f'data/interim/lcia_aggregated_residue_no_biomass_cat_{year}_{scenario}.csv'
    df.to_csv(filename)
    return df


def aggregate_impact_cat1(year, scenario, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df = df.groupby(by=['Country', 'CAT1']).sum(numeric_only=True)
    df = recalculate_impacts(df)
    df = df[['Country', 'CAT1', 'GHG', 'GHG_TOT', 'BDV', 'BDV_TRA', 'BDV_OCC',
             'WATER', 'GTP', 'AVAI_MIN', 'AVAI_MAX']].copy()
    df.to_csv(f'data/interim/lcia_aggregated_residue_cat1_{year}_{scenario}_{price}.csv')
    return df


def forest_availability_share(year, scenario, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df['SUST'] = (df['SUST_MIN'] + df['SUST_MAX']) / 2
    df = pd.pivot_table(df, columns='CAT1', index='Country', values='SUST', aggfunc='sum')
    df = df.fillna(0)
    df['F_ratio'] = df['Forestry'] / (df['Agricultural'] + df['Forestry'])
    return df


def get_aggregated_impact(year, scenario, price):
    file_name = f'data/interim/lcia_aggregated_residue_{year}_{scenario}.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'].fillna('NA')
    else:
        df = all_potential_impacts_with_aggregate_forest_impact(year, scenario, price)
    return df


def calculate_impact_upper_fence(df):
    #df = get_aggregated_impact(year, scenario)
    upper_fence_dict = {}
    for impact in ['GHG', 'GHG_TOT', 'BDV', 'WATER', 'GTP']:
        fence = (df[impact].quantile(0.75) - df[impact].quantile(0.25)) * 1.5 + df[impact].quantile(0.75)
        upper_fence_dict[impact] = fence
    return upper_fence_dict


def impact_trade_off(year, scenario, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df2 = df.copy()
    df2.loc[~df2.Product.isin(product_list), 'Product'] = 'Other agricultural residues'
    df2 = df2.groupby(by=['Product', 'Country']).sum(numeric_only=True)
    df2 = recalculate_impacts(df2)
    df1 = df2[df2.AVAI_MAX > 0.1].copy()
    # df1['BDV'] *= 10e14
    df1['Size'] = df1['AVAI_MAX']/1000
    df1.loc[df1.Size > 20, 'Size'] = 20
    #df1['Size'] = df1['Size'] ** 0.5
    dfcn = df1[df1.Country == 'CN'].copy()
    dfcn['color'] = "#c1272d"
    dfbr = df1[df1.Country == 'BR'].copy()
    dfbr['color'] = "blue"
    dfcnbr = pd.concat([dfcn, dfbr], ignore_index=True)
    dfcnbr = dfcnbr[dfcnbr.AVAI_MAX > 10].copy()
    fig, ax = plt.subplots(1, 1, figsize=(9, 9), squeeze=True)
    sns.scatterplot(data=df1, x="GHG", y="BDV", hue="Product", ax=ax,
                    hue_order=['Forest residues', 'Maize stover', 'Rice straw',
                               'Sugarcane tops and leaves', 'Wheat straw',
                               'Other agricultural residues'],
                    palette=color6_old,
                    size='Size', sizes=(20, 200), alpha=0.8, edgecolor="black")
    sns.scatterplot(data=dfcnbr, x="GHG", y="BDV", hue="Product", ax=ax,
                    hue_order=['Forest residues', 'Maize stover', 'Rice straw',
                               'Sugarcane tops and leaves', 'Wheat straw',
                               'Other agricultural residues'],
                    palette=color6_old,
                    size='Size', sizes=(20, 200), alpha=0.8, edgecolor=list(dfcnbr.color), linewidth=2
                    )
    ax.set_xlim(0.008, 1.2)
    ax.set_ylim(5e-17, 3e-13)
    ax.set_yscale("log")
    ax.set_xscale("log")
    figname = f'figures/lcia/lcia_cc_bdv_tradeoff_{year}_{scenario}_with_legend.pdf'
    plt.savefig(figname, bbox_inches='tight')
    ax.get_legend().remove()
    figname = f'figures/lcia/lcia_cc_bdv_tradeoff_{year}_{scenario}.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()
    fig, ax = plt.subplots(1, 1, figsize=(9, 9), squeeze=True)
    sns.scatterplot(data=dfcn, x="GHG", y="BDV", hue="Product", ax=ax,
                    hue_order=['Forest residues', 'Maize stover', 'Rice straw',
                               'Sugarcane tops and leaves', 'Wheat straw',
                               'Other agricultural residues'],
                    palette=color6_old,
                    size='Size', sizes=(20, 200), alpha=0.8, edgecolor="black", linewidth=0.5
                  )
    ax.set_xlim(0, 0.2)
    ax.set_ylim(0, 10e-15)
    #ax.set_yscale("log")
    #ax.set_xscale("log")
    ax.get_legend().remove()
    figname = f'figures/lcia/lcia_cc_bdv_tradeoff_{year}_{scenario}_cn.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()
    fig, ax = plt.subplots(1, 1, figsize=(9, 9), squeeze=True)
    sns.scatterplot(data=dfbr, x="GHG", y="BDV", hue="Product", ax=ax,
                    hue_order=['Forest residues', 'Maize stover', 'Rice straw',
                               'Sugarcane tops and leaves', 'Wheat straw',
                               'Other agricultural residues'],
                    palette=color6_old,
                    size='Size', sizes=(20, 200), alpha=0.8,
                    edgecolor="black", linewidth=0.5
                    )
    ax.set_xlim(0, 0.2)
    ax.set_ylim(0, 10e-15)
    #ax.set_yscale("log")
    #ax.set_xscale("log")
    ax.get_legend().remove()
    figname = f'figures/lcia/lcia_cc_bdv_tradeoff_{year}_{scenario}_br.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()
    # combined CN BR
    fig, ax = plt.subplots(1, 1, figsize=(5, 5), squeeze=True)
    sns.scatterplot(data=dfcnbr, x="GHG", y="BDV", hue="Product", ax=ax,
                    hue_order=['Forest residues', 'Maize stover', 'Rice straw',
                               'Sugarcane tops and leaves', 'Wheat straw',
                               'Other agricultural residues'],
                    palette=color6_old,
                    size='Size', sizes=(20, 200), alpha=0.8, edgecolor=list(dfcnbr.color), linewidth=2
                    )
    ax.set_xlim(0, 0.2)
    ax.set_ylim(0, 10e-15)
    figname = f'figures/lcia/lcia_cc_bdv_tradeoff_{year}_{scenario}_br_cn_legend.pdf'
    plt.savefig(figname, bbox_inches='tight')
    # ax.set_yscale("log")
    # ax.set_xscale("log")
    ax.get_legend().remove()
    figname = f'figures/lcia/lcia_cc_bdv_tradeoff_{year}_{scenario}_br_cn.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()
    return df


def merit_order_curve_single_country(year, scenario, country, impact, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df2 = df.copy()
    df2['AVAI_MAX'] /= 1000 #Mt
    df2.loc[~df2.Product.isin(product_list), 'Product'] = 'Other agricultural residues'
    df2 = df2.groupby(by=['Product', 'Country']).sum(numeric_only=True)
    df2.reset_index(inplace=True)
    df2 = recalculate_impacts(df2)
    df_temp = df2[df2.Country.isin(['BR', 'CN', 'IN', 'US'])].copy()
    impact_max = df_temp[impact].max()
    df3 = df2[df2.Country == country].copy()
    df3.sort_values(by=[impact], inplace=True)
    df3['color'] = df3['Product'].map(color_dict_residue)
    begin_with = [0]
    for i in range(0, df3.shape[0] - 1):
        a = begin_with[-1] + list(df3['AVAI_MAX'])[i]
        begin_with.append(a)
    handles = []
    ind1 = list(color_dict_residue.keys())
    for residue in ind1:
        b = mpatches.Patch(color=color_dict_residue[residue], label=residue)
        handles.append(b)
    fig, ax = plt.subplots(1, 1, figsize=(5, 5), squeeze=True)
    ax.bar(begin_with, df3[impact],
           width=df3['AVAI_MAX'], align='edge',
           edgecolor='white', linewidth=0.5, color=df3['color'])
    # ax.legend().set_visible(False)
    xmax = ax.patches[-1].get_x() + ax.patches[-1].get_width()
    plt.xlim(0, xmax)
    plt.ylim(0, impact_max * 1.1)
    figname = f'figures/lcia/lcia_merit_order_curve_{country}_{impact}_{year}_{scenario}.pdf'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()


def joint_plot(year, scenario, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df2 = df.copy()
    df2['AVAI_MAX'] /= 1000  # Mt
    df2.loc[~df2.Product.isin(product_list), 'Product'] = 'Other agricultural residues'
    df2 = df2.groupby(by=['Product', 'Country']).sum(numeric_only=True)
    df2.reset_index(inplace=True)
    df2 = recalculate_impacts(df2)
    df2 = df2.dropna(subset=['GHG', 'BDV'])
    df1 = df2[df2.AVAI_MAX > 0.1].copy()
    df1['Size'] = df1['AVAI_MAX'] / 1000
    df1.loc[df1.Size > 20, 'Size'] = 20
    df1['Size'] = df1['Size'] ** 0.5
    for product in list(df2.Product.unique()):
        i = 0
        df3 = df1[df1.Product == product].copy()
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(4, 4))
        sns.kdeplot(data=df3, x="GHG", y="BDV", levels=100, thresh=.3, fill=True,
                    log_scale=True, cmap="rocket", ax=ax)
        sns.scatterplot(data=df3, x="GHG", y="BDV", hue="Product", s=10,
                        palette=[color_dict_residue[product]], ax=ax)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(0.008, 1.2)
        ax.set_ylim(5e-17, 3e-13)
        ax.get_legend().remove()
        figname = f'figures/lcia/lcia_joint_plot_{product}_{year}_{scenario}.pdf'
        plt.savefig(figname, bbox_inches='tight')
        plt.show()
        i += 1
    a=0


def impact_heat_map(year, scenario, impact, price):
    df = get_df_combined_potential_impacts(year, scenario, price)
    df.loc[~df.Product.isin(product_list), 'Product'] = 'Other agricultural residues'
    df_country = get_country_match_df()
    df['Region'] = df['Country'].map(df_country.set_index('ISO2')['Region_Group_Paper_2'])
    country_list = ['BR', 'CN', 'IN', 'RME', 'US', 'RAF', 'EU', 'ASEAN', 'RoW']
    df.loc[~df.Region.isin(country_list), 'Region'] = 'RoW'
    df1 = df.groupby(by=['Product']).sum(numeric_only=True)
    df1 = recalculate_impacts(df1)
    df1['BDV'] *= 1E15
    upper_fence_dict = calculate_impact_upper_fence(df1)
    df = df.groupby(by=['Region', 'Product']).sum(numeric_only=True)
    df = recalculate_impacts(df)
    df = df.loc[df.Region != 'RoW'].copy()
    df['BDV'] *= 1E15
    table = pd.pivot_table(df, index='Product', columns='Region', values=impact)
    table = table.reindex(['Forest residues', 'Maize stover', 'Rice straw',
                   'Sugarcane tops and leaves', 'Wheat straw', 'Other agricultural residues'])
    table = table[['BR', 'CN', 'IN', 'US', 'EU', 'ASEAN', 'RAF', 'RME']]
    fig, ax = plt.subplots(1, 1, figsize=(9, 9), squeeze=True, subplot_kw={'aspect': 1})
    sns.heatmap(
        np.where(table.isna(), 0, np.nan),
        ax=ax, vmin=0, vmax=0,
        cbar=False,
        annot=np.full_like(table, "NA", dtype=object),
        fmt="",
        annot_kws={"size": 10, "va": "center_baseline", "color": "black"},
        cmap=ListedColormap(['#d8d8d8']),
        linewidth=0)
    sns.heatmap(table, cmap=cmp_yellow_orange(), square=True, annot=True, fmt=".2f",
                linewidth=0.5, cbar=False, ax=ax, vmax=upper_fence_dict[impact], vmin=0,
                annot_kws={"size": 10, "va": "center_baseline", "color": "black"}, )
    figname = f'figures/lcia/lcia_heatmap_{year}_{scenario}_{impact}.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()


def impact_distribution_box(year, scenario, impact, price):
    df0 = get_aggregated_impact(year, scenario, price)
    df0.loc[~df0.Product.isin(product_list), 'Product'] = 'Others'
    fig = px.box(df0, x=impact, y='Product', color_discrete_sequence=[color6_old[-2]],
                 category_orders={'Product': ['Forest residues', 'Maize stover', 'Rice straw',
                                              'Sugarcane tops and leaves', 'Wheat straw', 'Others']},
                 width=400, height=400)
    fig.update_layout(showlegend=False,
                      template=None,
                      xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=False)
                      )
    fig.update_traces(line=dict(#color="#414042",
                                width=0.5))
    if 'BDV' in impact:
        fig.update_xaxes(tickvals=[-100e-15, -50e-15, 0, 50e-15],
                         ticktext=[-100, -50, 0, 50],
                         range=[-100e-15, 80e-15])
    fig.write_image(f'figures/lcia/lcia_distribution_box_plot_{impact}_{year}_{scenario}.pdf')
    #fig.show()
    return fig


def impact_distribution_box_log(year, scenario, impact, price):
    df0 = get_aggregated_impact(year, scenario, price)
    df0.loc[~df0.Product.isin(product_list), 'Product'] = 'Others'
    df1 = df0.copy()
    df1['BDV'] *= 1e15
    df1 = df1[df1['GHG'] > 0].copy()
    fig, ax = plt.subplots(1, 1, figsize=(4, 4), squeeze=True)
    sns.boxplot(data=df1, x=impact, y='Product', ax=ax, linewidth=0.5, color=color6_old[-2],
                flierprops={"marker": "o", 'markerfacecolor': color6_old[-2], 'markeredgecolor': 'black',
                            'markeredgewidth': 0.5},
                order=['Forest residues', 'Maize stover', 'Rice straw',
                       'Sugarcane tops and leaves', 'Wheat straw', 'Others'])
    for i, artist in enumerate(ax.artists):
        artist.set_edgecolor('black')
        for j in range(i * 6, i * 6 + 6):
            line = ax.lines[j]
            line.set_color('black')
            line.set_mfc('black')
            line.set_mec('black')
            line.set_linewidth(0.5)
    if impact == 'BDV':
        ax.set_xscale('symlog')
        ax.set_xlim(-35, 150)
        plt.xlabel('Biodiversity loss (x10^-15)')
    elif impact == 'WATER':
        ax.set_xscale('log')
        ax.set_xlim(0.0004, 200)
    for spine in ax.spines.values():
        spine.set_edgecolor('#bcbec0')
        spine.set_linewidth(0.5)
    ax.tick_params(colors='#bcbec0', width=0.5, labelcolor='black', which='both')
    figname = f'figures/lcia/lcia_distribution_box_plot_{impact}_{year}_{scenario}.pdf'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()


def ghg_contribution_df(year, scenario, price):
    df0 = get_ghg_contribution_df(year, scenario)
    df = pd.pivot_table(df0, index=['Product', 'Country'], columns='Cat', values='GHG_sub', aggfunc='sum')
    df.reset_index(inplace=True)
    df['Product'] = df['Product'].map(residue_crop_dict)
    df2 = get_residue_potential(year, scenario)
    df_lci = lcia_crop_add_price(year, scenario, price)
    df = pd.merge(df, df_lci, on=['Product', 'Country'], how='left')
    # df['Product'] = df['Product'].map(residue_crop_dict)
    df_temp = df.copy()
    for x in ['Fertilizer production',
              'Land use change', 'Machinery energy', 'Onsite', 'Onsite, CH4',
              'Onsite, CO2', 'Onsite, N2O, Peat', 'Onsite, N2O, crop residue',
              'Onsite, N2O, fertilizer', 'Onsite, N2O, manure', 'Others', 'Seed']:
        df[x] = df_temp[x] * df_temp['Alloc_r'] / df_temp['Yield_r']
    df['Others'] += df['Seed']
    df['Others'] += df['Onsite, N2O, Peat']
    df['Onsite, N2O, fertilizer'] += df['Onsite, N2O, manure']
    df['End of life'] = 0
    '''
    df = df[['Product', 'Country', 'Fertilizer production', 'Land use change',
             'Machinery energy', 'Onsite, CH4', 'Onsite, CO2',
             'Onsite, N2O, crop residue', 'Onsite, N2O, fertilizer', 'End of life', 'Others',
             'Yield_r', 'Alloc_r']].copy()
    '''
    df = pd.merge(df, df2, on=['Product', 'Country'], how='left')
    return df


def ghg_contribution_aggregated_cat1(year, scenario, price):
    df = ghg_contribution_df(year, scenario, price)
    df['SUST'] = (df['SUST_MIN'] + df['SUST_MAX']) / 2
    ghg_cat_list = ['Fertilizer production', 'Land use change',
                    'Machinery energy', 'Onsite, CH4', 'Onsite, CO2',
                    'Onsite, N2O, crop residue', 'Onsite, N2O, fertilizer', 'End of life', 'Others']
    for ghg_cat in ghg_cat_list:
        column_name = f'{ghg_cat}xSUST'
        df[column_name] = df[ghg_cat] * df['SUST']
    df = df.groupby(by=['Country']).sum(numeric_only=True)
    for ghg_cat in ghg_cat_list:
        column_name = f'{ghg_cat}xSUST'
        df[ghg_cat] = df[column_name] / df['SUST']
    df = df[ghg_cat_list].copy()
    df.reset_index(inplace=True)
    df['YEAR'] = year
    df['SCENARIO'] = scenario
    return df


def ghg_contribution_bar_plot_2_cats_4_countries(year, scenario, price):
    df1 = get_aggregated_impact(year, scenario, price)
    df1 = df1[df1.Product == 'Forest residues'].copy()
    df = ghg_contribution_aggregated_cat1(year, scenario, price)
    country_to_plot = ['BR', 'CN', 'IN', 'US']
    fig = make_subplots(rows=2, cols=2,
                        shared_xaxes=True,
                        shared_yaxes=True,
                        vertical_spacing=0.01,
                        horizontal_spacing=0.02,
                        column_widths=[0.85, 0.15])
    i = 1
    j = 0
    marker_pattern_list = ['.', '/', '|', '\\']
    for cat in ['Onsite, N2O, crop residue', 'Onsite, N2O, fertilizer', 'Onsite, CO2', 'Onsite, CH4',
                'Land use change', 'Fertilizer production', 'Machinery energy', 'End of life', 'Others']:
        y_list_1 = []
        y_list_2 = []
        for country in country_to_plot:
            df_temp_1 = df1[df1.Country == country].copy()
            y_list_2.append(df.loc[df.Country == country, cat].iloc[0])
            if cat == 'End of life':
                y_list_1.append(df_temp_1['GHG_TOT'].iloc[0]-df_temp_1['GHG'].iloc[0])
            elif cat == 'Machinery energy':
                y_list_1.append(df_temp_1['GHG'].iloc[0])
            else:
                y_list_1.append(0)
        if 'Onsite' in cat:
            bar1 = go.Bar(
                name=cat,
                y=country_to_plot,
                x=y_list_1,
                orientation='h',
                marker=dict(color=color6_old[0], line_color='white', pattern_shape=marker_pattern_list[j],
                            pattern_fillmode='overlay'),
            )
            bar2 = go.Bar(
                name=cat,
                y=country_to_plot,
                x=y_list_2,
                orientation='h',
                marker=dict(color=color6_old[0], line_color='white', pattern_shape=marker_pattern_list[j],
                            pattern_fillmode='overlay'),
                showlegend=False
            )
            j += 1
        else:
            bar1 = go.Bar(
                name=cat,
                y=country_to_plot,
                x=y_list_1,
                orientation='h',
                marker=dict(color=color6_old[i], line_color='white'),
            )
            bar2 = go.Bar(
                name=cat,
                y=country_to_plot,
                x=y_list_2,
                orientation='h',
                marker=dict(color=color6_old[i], line_color='white'),
                showlegend=False
            )
            i += 1
        fig.add_trace(bar1, row=1, col=1)
        bar1.showlegend = False
        fig.add_trace(bar2, row=2, col=1)
        fig.add_trace(bar1, row=1, col=2)
        fig.add_trace(bar2, row=2, col=2)
    fig.update_layout(barmode='stack',
                      template=None,
                      width=1200,
                      height=600,
                      legend_traceorder='reversed'
                      )
    xlim = 0.16
    fig.update_xaxes(range=[0, xlim], showgrid=False, row=1, col=1)
    fig.update_xaxes(range=[0.3, 0.9], showgrid=False, row=1, col=2)
    fig.update_xaxes(range=[0, xlim], showgrid=False, showline=True, row=2, col=1)
    fig.update_xaxes(range=[0.3, 0.9], showgrid=False, showline=True, row=2, col=2)
    fig.write_image(f'figures/lcia/lcia_ghg_contribution_bar_plot_2_cats_4_countries_{year}_{scenario}.pdf')
    return fig

