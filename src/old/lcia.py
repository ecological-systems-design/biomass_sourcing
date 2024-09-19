import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


from src.other.colors import color6


def get_lcia_df(year, scenario, price):
    file_name = f'data/interim/lcia_all_residues_{year}_{scenario}_{price}.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'].fillna('NA')
    else:
        from src.bw.bw_lcia import lcia_all
        df = lcia_all(year, scenario, price)
    return df


def get_residue_potential(year, scenario):
    file_name = 'data/interim/GLOBIOM_all_residue_c_processed.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'].fillna('NA')
    else:
        from src.old.GLOBIOM_residue_potential import export_all_residues_c
        df = export_all_residues_c()
    df = df[(df.YEAR == year) & (df.SCENARIO == scenario)].copy()
    return df


def combine_potential_and_impact(year, scenario, price):
    df1 = get_lcia_df(year, scenario, price)
    df2 = get_residue_potential(year, scenario)
    df = pd.merge(df1, df2, on=['Product', 'Country'], how='left')
    df.loc[df.CAT1 == 'Forestry', 'Product'] = 'Forest residues'
    return df


def aggregate_impact(year, scenario, price):
    df = combine_potential_and_impact(year, scenario, price)
    df['SUST'] = (df['SUST_MIN'] + df['SUST_MAX']) / 2
    df['GHGxSUST'] = df['GHG'] * df['SUST']
    df['BDVxSUST'] = df['BDV'] * df['SUST']
    df['WATERxSUST'] = df['WATER'] * df['SUST']
    df = df.groupby(by=['Product', 'Country', 'CAT1']).sum(numeric_only=True)
    df.reset_index(inplace=True)
    df['GHG'] = df['GHGxSUST'] / df['SUST']
    df['BDV'] = df['BDVxSUST'] / df['SUST']
    df['WATER'] = df['WATERxSUST'] / df['SUST']
    df = df[['Product', 'Country', 'GHG', 'BDV', 'WATER', 'AVAI_MIN', 'AVAI_MAX']].copy()
    return df


def wind_rose_plot(year, scenario, price):
    df = aggregate_impact(year, scenario, price)
    for x in ['GHG', 'BDV', 'WATER']:
        colname = f'{x}_n'
        df[colname] = df[x] / df[x].quantile(q=0.95)
        df.loc[df[colname] < 0, colname] = 0
        df.loc[df[colname] > 1, colname] = 1
    df2 = df[df.Country.isin(['BR', 'CN', 'IN', 'US'])].copy()
    row_num = 3
    col_num = 3
    fig = make_subplots(rows=row_num, cols=col_num,
                        specs=[[{"type": "polar"}]*col_num]*row_num,
                        subplot_titles=list(df2.Product.unique()))
    i = 0
    for product in list(df2.Product.unique()):
        df3 = df2[df2.Product == product].copy()
        ghg_list = []
        bdv_list = []
        water_list = []
        for country in ['BR', 'CN', 'IN', 'US']:
            if country in list(df3.Country.unique()):
                ghg = df3.loc[df3.Country == country, 'GHG_n'].iloc[0]
                bdv = df3.loc[df3.Country == country, 'BDV_n'].iloc[0]
                water = df3.loc[df3.Country == country, 'WATER_n'].iloc[0]
            else:
                ghg = 0
                bdv = 0
                water = 0
                print(product, country)
            theta_list = [30 * i + 15 for i in range(0, 12)]
            ghg_list += [ghg, 0, 0]
            bdv_list += [0, bdv, 0]
            water_list += [0, 0, water]
        fig.add_trace(go.Barpolar(
            r=ghg_list,
            theta=theta_list,
            name='Climate change',
            marker_color=color6[0],
            opacity=0.8,
            marker_line_color='black',
            marker_line_width=1,
            legendgroup=1
        ), row=i//col_num+1, col=i%col_num+1)
        fig.add_trace(go.Barpolar(
            r=bdv_list,
            theta=theta_list,
            name='Biodiversity',
            marker_color=color6[1],
            opacity=0.8,
            marker_line_color='black',
            marker_line_width=1,
            legendgroup=2
        ), row=i//col_num+1, col=i%col_num+1)
        fig.add_trace(go.Barpolar(
            r=water_list,
            theta=theta_list,
            name='Water stress',
            marker_color=color6[2],
            opacity=0.8,
            marker_line_color='black',
            marker_line_width=1,
            legendgroup=3
        ), row=i//col_num+1, col=i%col_num+1)
        fig.update_polars(
            radialaxis=dict(range=[0, 1], showticklabels=False, ticks='',
                            gridwidth=0.5),
            angularaxis=dict(showticklabels=False, ticks='',
                             tickvals=[0, 90, 180, 270],
                             gridwidth=0.5),
            row=i // col_num + 1, col=i % col_num + 1,
            hole=0.3
        )
        i += 1
    fig.update_layout(
        template=None
    )
    fig.write_image('figures/lcia_wind_rose_plot.svg')
    fig.show()
    return fig
