import bw2data as bd
import bw2calc as bc
import pandas as pd

from src.bw.bw_scenario_set_up import bw_scenario_set_up


def lcia_random():
    method_list = [('IPCC_AR6', 'GWP_100a', 'all')]
    scenario = 'scenRCP1p9'
    df = pd.DataFrame()
    for year in [2020, 2030, 2040, 2050, 2100]:
        bw_scenario_set_up(year, scenario)
        if year == 2020:
            ei_name = 'ecoinvent 3.8'
        else:
            ei_name = f'ecoinvent_image_SSP2-RCP19_{year}'
        ei = bd.Database(ei_name)
        product_list1 = [act for act in ei if 'concrete production, for building' in act.get('name')]
        product_list2 = [act for act in ei if 'market for electricity' in act.get('name') and 'CH' == act.get('location')]
        product_list3 = [act for act in ei if 'market for heat' in act.get('name') and 'CH' == act.get('location')]
        product_list4 = [act for act in ei if 'market for heat, future' in act.get('name')]
        product_list = product_list1 + product_list2 + product_list3 + product_list4
        fu = [{product: 1} for product in product_list]
        multi_lca_setup = {'inv': fu, 'ia': method_list}
        bc.multi_lca.calculation_setups['multi_lca_agri'] = multi_lca_setup
        mlca = bc.multi_lca.MultiLCA('multi_lca_agri')
        df_temp = pd.DataFrame(mlca.results, columns=['GWP100'])
        df_temp['year'] = year
        df_temp['name'] = [act.get('name') for act in product_list]
        df_temp['location'] = [act.get('location') for act in product_list]
        df_temp['unit'] = [act.get('unit') for act in product_list]
        df = pd.concat([df, df_temp])
    df.to_csv('luc.csv')