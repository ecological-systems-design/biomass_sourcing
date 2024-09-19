import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import plotly.graph_objects as go
import os
import matplotlib.patches as mpatches


from src.visualization.visualization_lcia import get_world_shape_file, get_lcia_df, get_residue_potential, combine_potential_and_impact
from src.other.colors import color_dict_residue


def get_biodiversity_cf():
    file_name = f'data/interim/cf_biodiversity_processed.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Location'].fillna('NA')
    else:
        from src.data.lcia_regionalized_cfs import biodiversity_cf_match_locations
        df = biodiversity_cf_match_locations()
    df.rename(columns={'Location': 'Country'}, inplace=True)
    return df


def get_forest_luc_lci(year, scenario):
    file_name = f'data/interim/forest_lci_luc_per_kg_product_{year}_{scenario}.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Country'].fillna('NA')
    else:
        from src.bw.bw_lcia import lcia_luc_forest
        df = lcia_luc_forest(year, scenario)
    return df


def combine_forest_dfs(year, scenario, price):
    df_cf = get_biodiversity_cf()
    df_cf = df_cf[df_cf.habitat == 'Managed_forest_Intense'].copy()
    df_forest_lci = get_forest_luc_lci(year, scenario)
    df_lcia = get_lcia_df(year, scenario, price)
    df = pd.merge(df_forest_lci, df_lcia, on=['Product', 'Country'], how='left')
    df = pd.merge(df, df_cf, on=['Country'], how='left')
    df = df[['Product', 'Country', 'Occupation, forest, extensive',
             'Transformation, from primary forest', 'BDV', 'BDV_TRA',
             'CF_gji_occ_avg_glo', 'CF_gji_tra_avg_glo']].copy()
    df = df[df.Product == 'Logging residue, conifer'].copy()
    df = df.dropna()
    df['BDV_TRA_ranking'] = df['BDV_TRA'].rank(method='first')
    df['BDV_ranking'] = df['BDV'].rank(method='first')
    df['occ_ranking'] = df['Occupation, forest, extensive'].rank(method='first')
    df['tra_ranking'] = df['Transformation, from primary forest'].rank(method='first')
    df['cf_tra_ranking'] = df['CF_gji_tra_avg_glo'].rank(method='first')
    df['cf_occ_ranking'] = df['CF_gji_occ_avg_glo'].rank(method='first')
    df = df.sort_values('BDV_ranking')
    df.to_csv(f'data/processed/biodiviersity_impact_ranking_logging_residues.csv')
    fig = go.Figure()
    count = 0
    for i in df.index:
        if count > 83:
            x_list = [1, 2, 3, 4]
            y_list = []
            column_list = ['BDV_ranking', 'BDV_TRA_ranking', 'tra_ranking', 'cf_tra_ranking']
            for j in column_list:
                y_list.append(df.loc[i, j])
            fig.add_trace(go.Scatter(x=x_list,
                                     y=y_list,
                                     text=df.loc[i, 'Country']))
        count += 1
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False,
                     range=[20, 106])
    figname = f'figures/biodiversity_rankings.png'
    fig.write_image(figname)
    fig.show()
    return df


def plot_biodiversity_cf_map():
    world_shape = get_world_shape_file()
    df0 = get_biodiversity_cf()
    habitat = 'Managed_forest_Intense'
    df = df0[df0.habitat == habitat].copy()
    df = pd.merge(df, world_shape, on='Country', how='right')
    df = gpd.GeoDataFrame(df, geometry=df.geometry)
    impact_list = ['tra', 'occ']
    for impact in impact_list:
        if impact == 'tra':
            vmax = 2e-12
        else:
            vmax = 8e-15
        fig, ax = plt.subplots(1, 1, figsize=(15, 7))
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.1)
        df.plot(column=f'CF_gji_{impact}_avg_glo', missing_kwds={'color': 'lightgrey'}, ax=ax, legend=True, cax=cax,
                vmax=vmax)
        ax.axis('off')
        figname = f'figures/cf_map_biodiversity_{habitat}_{impact}.png'
        plt.savefig(figname, bbox_inches='tight')
        fig.show()
    return df


def biodiversity_reduction_action(year, scenario, price):
    df1 = combine_potential_and_impact(year, scenario, price)
    df2 = df1.copy()
    df2['BDV'] = df1['BDV'] * 1e15
    df2['AVAI'] = df2['AVAI_MIN']
    df2 = df2[['Product', 'Country', 'BDV', 'GHG', 'AVAI']].copy()
    df2['BDVxAVAI'] = df2['BDV'] * df2['AVAI']
    df2['GHGxAVAI'] = df2['GHG'] * df2['AVAI']
    df3 = df2[df2.BDV < 10].copy()
    df4 = df2[df2.GHG < 0.3].copy()
    df5 = df2[(df2.BDV < 10) & (df2.GHG < 0.3)].copy()
    total_bdv = df2['BDVxAVAI'].sum() / 1000000
    total_ghg = df2['GHGxAVAI'].sum() / 1000000
    total_availability = df2['AVAI'].sum() / 1000000
    total_bdv_reduced = df3['BDVxAVAI'].sum() / 1000000
    total_availability_reduced_bdv = df3['AVAI'].sum() / 1000000
    total_ghg_reduced = df4['GHGxAVAI'].sum() / 1000000
    total_availability_reduced_ghg = df4['AVAI'].sum() / 1000000
    total_availability_reduced = df5['AVAI'].sum() / 1000000
    print("Global bdv impacts: ", total_bdv, "x10^-9 PDF; Global availability: ", total_availability, "Gt")
    print("Global bdv impacts: ", total_bdv_reduced, "x10^-9 PDF; Global availability: ",
          total_availability_reduced_bdv, "Gt")
    print("BDV reduction: ", (total_bdv - total_bdv_reduced) / total_bdv * 100, "%")
    print("Availability reduction: ", (total_availability - total_availability_reduced_bdv) / total_availability * 100, "%")
    print("Global ghg impacts: ", total_ghg, "Gt CO2eq; Global availability: ", total_availability, "Gt")
    print("Global ghg impacts: ", total_ghg_reduced, "Gt CO2eq; Global availability: ", total_availability, "Gt")
    print("GHG reduction: ", (total_ghg - total_ghg_reduced) / total_ghg * 100, "%")
    print("Availability reduction: ", (total_availability - total_availability_reduced_ghg) / total_availability * 100, "%")
    print("Combined availability reduction: ", (total_availability - total_availability_reduced) / total_availability * 100, "%")


def merit_order_curve_biodiversity_all(year, scenario, price):
    df1 = combine_potential_and_impact(year, scenario, price)
    df2 = df1.copy()
    df2['AVAI_MAX'] /= 1000 #Mt
    df2.sort_values(by=["BDV"], inplace=True)
    df2.loc[df2.Product.str.contains('conifer'), 'Product'] = "Forest residues"
    df2['color'] = df2['Product'].map(color_dict_residue)
    df2.loc[df2.color.isna(), 'color'] = '#d8d8d8'
    begin_with = [0]
    for i in range(0, df2.shape[0] - 1):
        a = begin_with[-1] + list(df2['AVAI_MAX'])[i]
        begin_with.append(a)
    begin_with_2 = [0]
    impact_value_list_2 = [0]
    for x in df2.index:
        production = df2.loc[x, 'AVAI_MAX']
        impact_value = df2.loc[x, 'BDV']
        a = begin_with_2[-1] + production
        begin_with_2.append(a)
        impact_value_list_2.append(impact_value)
    handles = []
    ind1 = list(color_dict_residue.keys())
    for residue in ind1:
        b = mpatches.Patch(color=color_dict_residue[residue], label=residue)
        handles.append(b)
    fig, ax = plt.subplots(1, 1, figsize=(9, 4), squeeze=True)
    ax.bar(begin_with, df2['BDV'],
                     width=df2['AVAI_MAX'], align='edge',
                     edgecolor='white', linewidth=0.5, color=df2['color'])
    xmax = ax.patches[-1].get_x() + ax.patches[-1].get_width()
    ax.step(begin_with_2, impact_value_list_2, label='post', linewidth=1, color='grey')
    ax.set_yscale("log")
    plt.xlim(0, xmax)
    plt.legend(handles=handles, framealpha=0.0, loc="upper left")
    plt.show()
    return df2