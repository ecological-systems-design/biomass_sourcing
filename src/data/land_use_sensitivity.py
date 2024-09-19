import pandas as pd
import matplotlib.pyplot as plt

from src.other.read_globiom_data import read_globiom_land_use_sensitivity_data_g
from src.other.colors import color_contribution_old


def df_land_use_sensitivity():
    df0 = read_globiom_land_use_sensitivity_data_g()
    df = df0.copy()
    df.loc[df.LAND_USE == 'PriFor', 'LAND_USE'] = 'Forest'
    df.loc[df.LAND_USE == 'MngFor', 'LAND_USE'] = 'Forest'
    df.loc[(df.LAND_USE == 'NotRel') | (df.LAND_USE == 'OagLnd') | (df.LAND_USE == 'WetLnd'), 'LAND_USE'] = 'Other land'
    df = df[df.YEAR <= 2050].copy()
    df1 = pd.pivot_table(df, index=['UNIT', 'YEAR', 'SCENARIO'], columns='LAND_USE', values='VALUE', aggfunc='sum')
    df1 = df1.fillna(0)
    df1.reset_index(inplace=True)
    cat_list = ['Forest', 'PltFor', 'AfrLnd',
                'CrpLnd', 'GrsLnd', 'NatLnd', 'Other land']
    color_list = [color_contribution_old[0], color_contribution_old[1],
                  color_contribution_old[4], color_contribution_old[5],
                  color_contribution_old[6], color_contribution_old[7],
                  color_contribution_old[-1]]
    pds_ref = []
    pds_1p9 = []
    pds_ref_s = []
    pds_1p9_s = []
    year_list = [2000, 2010, 2020, 2030, 2040, 2050]
    for cat in cat_list:
        pds_ref.append(df1[(df1.SCENARIO == 'scenRCPref')][cat].values)
        pds_ref_s.append(df1[(df1.SCENARIO == 'scenRCPref_1')][cat].values)
        pds_1p9.append(df1[(df1.SCENARIO == 'scenRCP1p9')][cat].values)
        pds_1p9_s.append(df1[(df1.SCENARIO == 'scenRCP1p9_1')][cat].values)
    fig, ax = plt.subplots(1, 2, figsize=(10, 5), dpi=600, sharey=True)
    ax[0].stackplot(year_list, pds_ref, labels=cat_list, edgecolors='white', colors=color_list)
    ax[0].set_xlim([2000, 2050])
    ax[1].stackplot(year_list, pds_ref_s, labels=cat_list, edgecolors='white', colors=color_list)
    ax[1].set_xlim([2000, 2050])
    figname = f'figures/temporal_lcia/land_use_sensitivity_ref.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()
    fig, ax = plt.subplots(1, 2, figsize=(10, 5), dpi=600, sharey=True)
    ax[0].stackplot(year_list, pds_1p9, labels=cat_list, edgecolors='white', colors=color_list)
    ax[0].set_xlim([2000, 2050])
    ax[1].stackplot(year_list, pds_1p9_s, labels=cat_list, edgecolors='white', colors=color_list)
    ax[1].set_xlim([2000, 2050])
    figname = f'figures/temporal_lcia/land_use_sensitivity_1p9.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()
    return df
