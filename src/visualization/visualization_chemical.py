from src.bw.bw_lcia import lcia_chemical_level_5, lcia_chemical_level_1
from src.other.colors import color_sankey, color6_old

import plotly.graph_objects as go
import plotly.express as px
from matplotlib.sankey import Sankey
import matplotlib.pyplot as plt


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

