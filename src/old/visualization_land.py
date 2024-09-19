from src.data.land_use_change import harmonize_land_use_all
from src.other.colors import color_contribution_old

import io
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import plotly.io as pio


pio.renderers.default = 'png'


def plot(fig):
    img_bytes = fig.to_image(format="png")
    fp = io.BytesIO(img_bytes)
    with fp:
        i = mpimg.imread(fp, format='png')
    plt.axis('off')
    plt.imshow(i, interpolation='nearest')
    plt.show()


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
                  color_contribution_old[4], color_contribution_old[6],
                  color_contribution_old[5], color_contribution_old[5],
                  color_contribution_old[5], color_contribution_old[7],
                  color_contribution_old[-1]]
    hatch_list = ['', '', '\\\\\\', '||', '///', '...', '', '', '\\\\\\', '||', '///', '', '']
    for cat in cat_list:
        if cat not in list(dfc.columns):
            dfc[cat] = 0
            dfc_temp[cat] = 0
        dfc[cat] = dfc_temp[cat] / dfc_temp.sum(axis=1)
    dfc.reset_index(inplace=True)
    dfc.sort_values(by='YEAR', inplace=True)
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
    ax[1].stackplot(year_list, pds_1p9, labels=cat_list, edgecolors='white', colors=color_list)
    ax[1].set_xlim([2000, 2050])
    handles, labels = ax[1].get_legend_handles_labels()
    for handle, hatch in zip(handles, hatch_list):
        handle.set_hatch(hatch)
    ax[1].legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(1, 1), ncol=1)
    figname = f'figures/others/land_use_{country}.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()
