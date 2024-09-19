from src.visualization.visualization_lcia import (aggregate_impact_cat1,
                                                  ghg_contribution_aggregated_cat1,
                                                  ghg_contribution_df)
from src.bw.bw_scenario_set_up import bw_scenario_set_up
from src.other.colors import color6_old

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns


def ghg_contribution_all_scenarios(price):
    df = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCP1p9', 'scenRCPref']:
            bw_scenario_set_up(year, scenario)
            df_temp = ghg_contribution_df(year, scenario, price)
            df_temp['YEAR'] = year
            df_temp['SCENARIO'] = scenario
            df = pd.concat([df, df_temp], axis=0)
    df.to_csv(f'data/interim/ghg_crop_all_years_scenarios_price_{price}.csv')
    return df


def cat1_impacts_all_scenarios(price):
    df = pd.DataFrame()
    df_ghg = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050]:
        for scenario in ['scenRCP1p9', 'scenRCPref']:
            bw_scenario_set_up(year, scenario)
            df_temp = aggregate_impact_cat1(year, scenario, price)
            df_temp['YEAR'] = year
            df_temp['SCENARIO'] = scenario
            df = pd.concat([df, df_temp], axis=0)
            df_ghg_temp = ghg_contribution_aggregated_cat1(year, scenario, price)
            df_ghg_temp['YEAR'] = year
            df_ghg_temp['SCENARIO'] = scenario
            df_ghg = pd.concat([df_ghg, df_ghg_temp], axis=0)
    df.to_csv(f'data/interim/lcia_cat1_all_years_scenarios_price_{price}.csv')
    df_ghg.to_csv(f'data/interim/lcia_ghg_contribution_cat1_all_years_scenarios_price_{price}.csv')
    return df, df_ghg


def get_ghg_all_year_scenario(price):
    if os.path.exists(f'data/interim/ghg_crop_all_years_scenarios_price_{price}.csv'):
        df = pd.read_csv(f'data/interim/ghg_crop_all_years_scenarios_price_{price}.csv', index_col=0,
                         encoding="utf-8")
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = ghg_contribution_all_scenarios(price)
    return df


def get_ghg_cat1_all_year_scenario(price):
    if os.path.exists(f'data/interim/lcia_ghg_contribution_cat1_all_years_scenarios_price_{price}.csv'):
        df = pd.read_csv(f'data/interim/lcia_ghg_contribution_cat1_all_years_scenarios_price_{price}.csv', index_col=0,
                         encoding="utf-8")
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = cat1_impacts_all_scenarios(price)[1]
    df = df.set_index(['Country', 'YEAR', 'SCENARIO'])
    df['Onsite'] = df[['Onsite, N2O, crop residue', 'Onsite, N2O, fertilizer',
                       'Onsite, CO2', 'Onsite, CH4']].sum(axis=1)
    return df


def get_lcia_all_year_scenario(price):
    if os.path.exists(f'data/interim/lcia_cat1_all_years_scenarios_price_{price}.csv'):
        df = pd.read_csv(f'data/interim/lcia_cat1_all_years_scenarios_price_{price}.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        df = cat1_impacts_all_scenarios(price)[0]
    return df


def bar_plot_ghg_by_year_scenario(country, price):
    df = get_ghg_cat1_all_year_scenario(price)
    df1 = df.reset_index()
    df1 = df1[df1.Country == 'IN']
    df1['Total'] = df1.iloc[:, 3:].sum(axis=1)
    df2 = get_ghg_cat1_all_year_scenario('min')
    df2 = df2.reset_index()
    df2 = df2[df2.Country == 'IN']
    df2['Total'] = df2.iloc[:, 3:].sum(axis=1)
    x = np.arange(4)  # the label locations
    width = 0.3  # the width of the bars
    cat_list = ['Onsite', 'Land use change', 'Fertilizer production', 'Machinery energy', 'End of life', 'Others']
    year = [2020, 2030, 2040, 2050]
    legend_list = cat_list
    legend_list.append('Residue production (right axis)')
    legend = []
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    for i in list(range(6)):
        cat = cat_list[i]
        df_temp_1 = df.loc[(country, slice(None), 'scenRCPref'), cat]
        df_temp_2 = df.loc[(country, slice(None), 'scenRCP1p9'), cat]
        if i == 0:
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, label='RCP6.5', color=color6_old[i],
                             edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, label='RCP1.9', color=color6_old[i],
                   edgecolor='white')
        else:
            df_sum_1 = df.loc[(country, slice(None), 'scenRCPref'), cat_list[0:i]].sum(axis=1)
            df_sum_2 = df.loc[(country, slice(None), 'scenRCP1p9'), cat_list[0:i]].sum(axis=1)
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, bottom=df_sum_1.to_list(),
                             label='RCP6.5', color=color6_old[i], edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, bottom=df_sum_2.to_list(), label='RCP1.9',
                   color=color6_old[i], edgecolor='white')
    ax.set_title(f'{country}')
    ax.set_ylim(0, 0.5)
    x_tick_position = list(x) + [i - 0.15 for i in x] + [i + 0.15 for i in x]
    x_tick_label = [f'\n{yr}' for yr in year] + ['RCP6.5'] * 4 + ['RCP1.9'] * 4
    ax.set_xticks(x_tick_position, x_tick_label)
    ax.tick_params(bottom=False)
    ax.legend([legend[i] for i in range(len(legend)) if i % 4 == 0][::-1], legend_list[::-1],
              loc='upper right', frameon=False, bbox_to_anchor=(1.45, 0.6), ncols=1)
    fig_name = f'figures/lcia_contribution_CC_{country}_price_{price}.pdf'
    plt.savefig(fig_name)
    fig.show()


def bar_plot_bdv_by_year_scenario(country, price, cat1):
    df = get_lcia_all_year_scenario(price)
    df = df.set_index(['Country', 'YEAR', 'SCENARIO', 'CAT1'])
    x = np.arange(4)  # the label locations
    width = 0.3  # the width of the bars
    cat_list = ['BDV_OCC', 'BDV_TRA']
    # cat1_list = ['Agricultural', 'Forestry']
    year = [2020, 2030, 2040, 2050]
    legend_list = cat_list
    legend_list.append('Residue production (right axis)')
    legend = []
    fig, ax = plt.subplots(1, 1, figsize=(10, 4), sharex=True)
    ax2 = ax.twinx()
    for i in list(range(2)):
        cat = cat_list[i]
        df_temp_1 = df.loc[(country, slice(None), 'scenRCPref', cat1), cat]
        df_temp_2 = df.loc[(country, slice(None), 'scenRCP1p9', cat1), cat]
        if i == 0:
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, label='RCP6.5', color=color6_old[i],
                             edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, label='RCP1.9', color=color6_old[i],
                   edgecolor='white')
        else:
            df_sum_1 = df.loc[(country, slice(None), 'scenRCPref', cat1), cat_list[0:i]].sum(axis=1)
            df_sum_2 = df.loc[(country, slice(None), 'scenRCP1p9', cat1), cat_list[0:i]].sum(axis=1)
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, bottom=df_sum_1.to_list(),
                             label='RCP6.5', color=color6_old[i], edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, bottom=df_sum_2.to_list(), label='RCP1.9',
                   color=color6_old[i], edgecolor='white')

    ax.set_title(f'Process contribution to biodiversity loss impact, {country}, {cat1}')
    ax.set_ylabel('kg CO2-eq/ha')
    ax2.set_ylabel('kt residue production')
    ax2.set_ylim(bottom=0)
    x_tick_position = list(x) + [i - 0.15 for i in x] + [i + 0.15 for i in x]
    x_tick_label = [f'\n{yr}' for yr in year] + ['RCP6.5'] * 4 + ['RCP1.9'] * 4
    ax.set_xticks(x_tick_position, x_tick_label)
    # ax.set_xticks([i-0.15 for i in x], ['RCP6.5']*4)
    ax.tick_params(bottom=False)
    ax.legend([legend[i] for i in range(len(legend)) if i % 4 == 0][::-1], legend_list[::-1],
              loc='upper right', frameon=False, bbox_to_anchor=(1.45, 0.6), ncols=1)
    fig_name = f'figures/lcia_contribution_BDV_{country}_{cat1}_price_{price}.png'
    plt.savefig(fig_name)
    fig.show()


def lcia_scenario_comparison(price, cat1):
    df = get_lcia_all_year_scenario(price)
    df1 = pd.pivot_table(df, columns='SCENARIO', index=['CAT1', 'Country', 'YEAR'], values='GHG')
    df1 = df1.dropna(axis=0)
    df1.reset_index(inplace=True)
    df1 = df1[(df1.CAT1 == cat1) & (df1.YEAR == 2050)].copy()
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    sns.scatterplot(data=df1, x='scenRCPref', y='scenRCP1p9')
    fig.show()
    return df


def bar_plot_bdv_by_year(scenario, country, price):
    df = get_lcia_all_year_scenario(price)
    df = df[df.SCENARIO == scenario].copy()
    df = df.set_index(['Country', 'YEAR', 'CAT1'])
    x = np.arange(4)  # the label locations
    width = 0.3  # the width of the bars
    cat_list = ['BDV_OCC', 'BDV_TRA']
    year = [2020, 2030, 2040, 2050]
    legend_list = cat_list
    legend = []
    fig, ax = plt.subplots(1, 1, figsize=(6, 5), sharex=True)
    for i in list(range(2)):
        cat = cat_list[i]
        df_temp_1 = df.loc[(country, slice(None), 'Forestry'), cat]
        df_temp_2 = df.loc[(country, slice(None), 'Agricultural'), cat]
        if i == 0:
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, label='Forest', color="#00625a",
                             edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, label='Agricultural', color="#00625a",
                   edgecolor='white')
        else:
            df_sum_1 = df.loc[(country, slice(None), 'Forestry'), cat_list[0:i]].sum(axis=1)
            df_sum_2 = df.loc[(country, slice(None), 'Agricultural'), cat_list[0:i]].sum(axis=1)
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, bottom=df_sum_1.to_list(),
                             label='Forest', color="#c69b58", edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, bottom=df_sum_2.to_list(), label='Agricultural',
                   color="#c69b58", edgecolor='white')
    ax.set_title(f'Biodiversity loss impact, {country}')
    ax.set_ylabel('PDF/kg')
    ax.set_ylim(0, 1e-14)
    x_tick_position = list(x) + [i - 0.15 for i in x] + [i + 0.15 for i in x]
    x_tick_label = [f'\n{yr}' for yr in year] + ['F'] * 4 + ['A'] * 4
    ax.set_xticks(x_tick_position, x_tick_label)
    ax.tick_params(bottom=False)
    ax.legend([legend[i] for i in range(len(legend)) if i % 4 == 0][::-1], legend_list[::-1],
              loc='upper right', frameon=False, bbox_to_anchor=(1.45, 0.6), ncols=1)
    fig_name = f'figures/temporal_lcia/lcia_contribution_BDV_{scenario}_{country}_price_{price}.pdf'
    plt.savefig(fig_name)
    fig.show()


def bar_plot_ghg_by_year(scenario, country, price, ylim):
    dfg = get_ghg_cat1_all_year_scenario(price)
    df = get_lcia_all_year_scenario(price)
    dfg = dfg[['Land use change']].copy()
    dfg.reset_index(inplace=True)
    dfg = dfg[dfg.SCENARIO == scenario].copy()
    dfg['CAT1'] = 'Agricultural'
    df = df[df.SCENARIO == scenario].copy()
    df = pd.merge(df, dfg, how='left', on=['Country', 'CAT1', 'YEAR', 'SCENARIO'])
    df.loc[df.CAT1 == 'Forestry', 'Land use change'] = 0
    df['GHG_non_LUC'] = df['GHG'] - df['Land use change']
    df = df.set_index(['Country', 'YEAR', 'CAT1'])
    x = np.arange(4)  # the label locations
    width = 0.3  # the width of the bars
    cat_list = ['GHG_non_LUC', 'Land use change']
    year = [2020, 2030, 2040, 2050]
    legend_list = cat_list
    legend = []
    fig, ax = plt.subplots(1, 1, figsize=(6, 5))
    for i in list(range(2)):
        cat = cat_list[i]
        df_temp_1 = df.loc[(country, slice(None), 'Forestry'), cat]
        df_temp_2 = df.loc[(country, slice(None), 'Agricultural'), cat]
        if i == 0:
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, label='Others', color=color6_old[i],
                             edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, label='Others', color=color6_old[i],
                   edgecolor='white')
        else:
            df_sum_1 = df.loc[(country, slice(None), 'Forestry'), cat_list[0:i]].sum(axis=1)
            df_sum_2 = df.loc[(country, slice(None), 'Agricultural'), cat_list[0:i]].sum(axis=1)
            legend += ax.bar(x - width / 2, df_temp_1.to_list(), width, bottom=df_sum_1.to_list(),
                             label='LUC', color=color6_old[i], edgecolor='white')
            ax.bar(x + width / 2, df_temp_2.to_list(), width, bottom=df_sum_2.to_list(), label='LUC',
                   color=color6_old[i], edgecolor='white')
    ax.set_title(f'Climate change impact, {country}')
    ax.set_ylabel('kg CO2eq/kg')
    ax.set_ylim(0, ylim)
    x_tick_position = list(x) + [i - 0.15 for i in x] + [i + 0.15 for i in x]
    x_tick_label = [f'\n{yr}' for yr in year] + ['F'] * 4 + ['A'] * 4
    ax.set_xticks(x_tick_position, x_tick_label)
    ax.tick_params(bottom=False)
    ax.legend([legend[i] for i in range(len(legend)) if i % 4 == 0][::-1], legend_list[::-1],
              loc='upper right', frameon=False, bbox_to_anchor=(1.45, 0.6), ncols=1)
    fig_name = f'figures/temporal_lcia/lcia_contribution_CC_{scenario}_{country}_price_{price}.pdf'
    plt.savefig(fig_name)
    fig.show()
