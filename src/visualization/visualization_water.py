import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os


from src.visualization.visualization_lcia import get_world_shape_file


def get_aware_cf():
    file_name = f'data/interim/cf_aware_processed.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, index_col=0)
        df['Location'].fillna('NA')
    else:
        from src.data.lcia_regionalized_cfs import calculate_area_weighted_regional_water_cfs
        df = calculate_area_weighted_regional_water_cfs()
    df.rename(columns={'Location': 'Country'}, inplace=True)
    return df


def plot_aware_cf_map():
    world_shape = get_world_shape_file()
    df = get_aware_cf()
    df = pd.merge(df, world_shape, on='Country', how='right')
    df = gpd.GeoDataFrame(df, geometry=df.geometry)
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.1)
    df.plot(column=f'Agg_CF_irri', missing_kwds={'color': 'lightgrey'}, ax=ax, legend=True, cax=cax,
            # vmax=vmax
            )
    ax.axis('off')
    figname = f'figures/cf_map_aware_irrigation.png'
    plt.savefig(figname, bbox_inches='tight')
    fig.show()
