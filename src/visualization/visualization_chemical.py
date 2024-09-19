from src.bw.bw_lcia import lcia_chemical_level_5, lcia_chemical_level_1
from src.other.colors import color_sankey, color6_old

import plotly.graph_objects as go
import plotly.express as px
from matplotlib.sankey import Sankey
import matplotlib.pyplot as plt


def chemical_climate_change_impact_sankey():
    df_out = lcia_chemical_level_5()
    node_list = list(df_out.node1.unique())
    node_list2 = list(df_out.node2.unique())
    node_list.extend(x for x in node_list2 if x not in node_list)
    number_list = list(range(len(node_list)))
    node_dict = dict(zip(node_list, number_list))
    source = [node_dict[x] for x in list(df_out.node1)]
    target = [node_dict[x] for x in list(df_out.node2)]
    y_dict = {'Biomass feedstock': 0.01, 'Chemical': 0.83, 'Electricity': 0.43, 'Fuel': 0.63, 'Onsite': 0.17, 'Other': 0.95,
              'Compressed air': 0.93,  'Other chemicals': 0.82, 'Others': 0.99, 'Propanol': 0.6,
              'Biomass fractionation': 0.5}
    x_dict = {'Biomass feedstock': 0.1, 'Chemical': 0.1, 'Electricity': 0.1, 'Fuel': 0.1, 'Onsite': 0.1, 'Other': 0.1,
              'Compressed air': 0.5,  'Other chemicals': 0.5, 'Others': 0.5, 'Propanol': 0.5,
              'Biomass fractionation': 0.9}
    df = df_out.groupby(by='node1').sum(numeric_only=True)
    df.reset_index(inplace=True)
    pos1 = ['Biomass feedstock', 'Onsite', 'Electricity', 'Fuel', 'Chemical', 'Other']
    pos2 = ['Propanol', 'Other chemicals', 'Compressed air', 'Others']
    df1 = df[~df.node1.isin(pos2)].copy()
    df2 = df[df.node1.isin(pos2)].copy()
    sum1 = df1['GWP'].sum()
    sum2 = df2['GWP'].sum()
    ypos1 = []
    sumx1 = 0
    for i in range(0, len(pos1)):
        x = df1.loc[df1.node1 == pos1[i], 'GWP'].iloc[0] / sum1
        pos = x / 2 + sumx1
        ypos1.append(pos)
        sumx1 += x
    ypos2 = []
    sumx2 = (sum1-sum2)/sum1
    for i in range(0, len(pos2)):
        x = df2.loc[df2.node1 == pos2[i], 'GWP'].iloc[0] / sum1
        pos = x / 2 + sumx2
        ypos2.append(pos)
        sumx2 += x
    ypos = ypos1 + ypos2
    ypos.append(0.5)
    yname = pos1 + pos2
    yname.append('Biomass fractionation')
    y_dict = dict(zip(yname, ypos))
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=0,
            thickness=20,
            label=node_list,
            x=[x_dict[x] for x in node_list],
            y=[y_dict[x] for x in node_list],
            line=dict(color='white', width=0.5),
            color=[color_sankey(1)[x] for x in node_list]
        ),
        link=dict(
            source=source,
            target=target,
            value=list(df_out.GWP),
            color=[color_sankey(0.5)[x] for x in list(df_out.node1)]
        )
    )])
    fig.update_layout(width=1200,
                      height=600,
                      )
    fig.write_image(f'figures/chemical_sankey.pdf')
    fig.show()
    a=0


def chemical_climate_change_impact_scenario_bar(year, scenario, price):
    df = lcia_chemical_level_1(year, scenario, price)
    fig = px.bar(df, x="Level0", y="GWP", color="node1",
                 category_orders={'node1': ['Propanol', 'Other chemicals', 'Biomass feedstock',
                                            'Electricity', 'Onsite', 'Others'],
                                  },
                 labels={'node1': '', 'Level0': ''},
                 color_discrete_sequence=color6_old)
    fig.update_layout(xaxis={'categoryorder': 'total ascending'},
                      width=1500,
                      height=600,
                      template=None,
                      )
    for idx in range(len(fig.data)):
        fig.data[idx].x = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']
    fig.write_image(f'figures/lcia_chemical_scenarios.png')
    fig.write_image(f'figures/lcia_chemical_scenarios.pdf')


def biomass_to_chemical_sankey():
    fig = plt.figure(figsize=[6, 4], dpi=330)
    ax = fig.add_subplot(1, 1, 1, )
    s = Sankey(ax=ax, scale=1 / 40000, unit='kg', gap=.4, shoulder=0.05, )
    s.add(
        flows=[6.758, -4.159, -2.599, ],
        orientations=[0, 1, 0, ],
        labels=["S Value", "K Value", None, ],
        trunklength=1, pathlengths=0.4, edgecolor='#000000', facecolor='darkgreen',
        lw=0.5,
    )
    s.add(
        flows=[2.599, -1.584, -1.015],
        orientations=[0, 1, 0],
        labels=[None, "U Value", None],
        trunklength=1.5, pathlengths=0.5, edgecolor='#000000', facecolor='grey',
        prior=0, connect=(2, 0), lw=0.5,
    )
    s.add(
        flows=[1.015, -1, -0.015],
        orientations=[0, 0, 1],
        labels=[None, "H Value", "F Value"],
        trunklength=1, pathlengths=0.5, edgecolor='#000000', facecolor='darkred',
        prior=1, connect=(2, 0), lw=0.5,
    )
    diagrams = s.finish()
    for d in diagrams:
        for t in d.texts:
            t.set_horizontalalignment('left')

    plt.axis("off")

    figname = f'figures/lcia_maps/sankey.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.show()
    a=0
