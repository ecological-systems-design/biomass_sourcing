import bw2data as bd
import bw2calc as bc
import pandas as pd
import os

from src.other.name_match import residue_crop_dict


def get_lcia_method_list():
    method_list = []
    for method in bd.methods:
        if ('IPCC_AR6' in method
            or 'AWARE regionalized' in method
            or 'Biodiversity regionalized' in method
        ):
            method_list.append(method)
    return method_list


def get_crop_acts_for_lcia(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}'
    af_name = f"agrifootprint 6 {ei_name}_regionalized_update"
    afdb = bd.Database(af_name)
    product_list = [act for act in afdb if 'ha' == act.get('unit') and 'unchanged' not in act.get('name')]
    return product_list


def get_forest_acts_for_lcia(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}_regionalized_update'
    ei = bd.Database(ei_name)
    product_list = [act for act in ei if 'sawdust' in act.get('name')
                    or 'slab and siding' in act.get('name')
                    or 'cleft timber, measured as dry mass' in act.get('reference product')]
    return product_list


def get_crop_acts_glo_for_lcia(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}'
    af_name = f"agrifootprint 6 {ei_name}_regionalized_update"
    afdb = bd.Database(af_name)
    product_list = [act for act in afdb if 'ha' == act.get('unit')
                    and 'unchanged' in act.get('name') and 'GLO' in act.get('name')]
    return product_list


def lcia_crop(year, scenario):
    product_list = get_crop_acts_for_lcia(year, scenario)
    fu = [{product: 1} for product in product_list]
    lcia_method_list = get_lcia_method_list()
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_agri'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_agri')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Product_country'] = [act.get('name') for act in product_list]
    df['Product'] = [act.get('name').split(',')[0] for act in product_list]
    df['Country'] = [act.get('name')[-3:-1] for act in product_list]
    return df


def lcia_forest(year, scenario):
    product_list = get_forest_acts_for_lcia(year, scenario)
    fu = [{product: 1} for product in product_list]
    lcia_method_list = get_lcia_method_list()
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_forest'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_forest')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Product'] = [act.get('name') for act in product_list]
    df['Country'] = [act.get('location') for act in product_list]
    df_temp = df.copy()
    df_temp['name1'] = 'Logging residue'
    df_temp.loc[df_temp.Product.str.contains('slab'), 'name1'] = 'WoodChips'
    df_temp.loc[df_temp.Product.str.contains('sawdust'), 'name1'] = 'Sawdust'
    df_temp['name2'] = 'non-conifer'
    df_temp.loc[df_temp.Product.str.contains('softwood'), 'name2'] = 'conifer'
    df_temp['name'] = df_temp[['name1', 'name2']].agg(', '.join, axis=1)
    df['Product'] = df_temp['name']
    df['GHG'] = df['IPCC_AR6', 'GWP_100a', 'all']
    df['GTP'] = df['IPCC_AR6', 'GTP_100a', 'all']
    df['BDV'] = df['Biodiversity regionalized', 'Occupation'] + df['Biodiversity regionalized', 'Transformation']
    df['BDV_OCC'] = df['Biodiversity regionalized', 'Occupation']
    df['BDV_TRA'] = df['Biodiversity regionalized', 'Transformation']
    df['WATER'] = df['AWARE regionalized', 'Annual']
    df = df[['Product', 'Country', 'GHG', 'BDV', 'BDV_OCC', 'BDV_TRA', 'WATER', 'GTP']].copy()
    return df


def chemical_conditions(act):
    if (('acetone' in act.get('name')) or
        ('activated carbon' in act.get('name')) or
        ('ammonia' in act.get('name')) or
        ('allyl chloride' in act.get('name')) or
        ('benzene' in act.get('name')) or
        ('compressed air' in act.get('name')) or
        ('chlor' in act.get('name')) or
        ('dichloromethane' in act.get('name')) or
        ('dioxane' in act.get('name')) or
        ('ethy' in act.get('name')) or
        ('ethanol' in act.get('name')) or
        ('hydrogen' in act.get('name')) or
        ('Mannheim' in act.get('name')) or
        ('methanol' in act.get('name')) or
        ('naphtha' in act.get('name')) or
        ('butane' in act.get('name')) or
        ('phenol' in act.get('name')) or
        ('propanol' in act.get('name')) or
        ('propanal' in act.get('name')) or
        ('cumene' in act.get('name')) or
        ('acetic acid' in act.get('name')) or
        ('phosphoric acid' in act.get('name')) or
        ('propylene' in act.get('name')) or
        ('soda' in act.get('name')) or
        ('sodium' in act.get('name')) or
        ('sulfuric' in act.get('name')) or
        ('synthetic fuel' in act.get('name')) or
        ('tetrafluoroethylene' in act.get('name'))):
        return True
    else:
        return False


def add_node1(df, level, node):
    df[node] = 'Other chemicals'
    #df.loc[df[level].str.contains('dioxane'), node] = 'Dioxane'
    df.loc[df[level].str.contains('propanol'), node] = 'Propanol'
    #df.loc[df[level].str.contains('methanol'), node] = 'Methanol'
    #df.loc[df[level].str.contains('hexane'), node] = 'Hexane'
    df.loc[df[level].str.contains('cooling water'), node] = 'Others'
    df.loc[df[level].str.contains('market for water'), node] = 'Others'
    df.loc[df[level].str.contains('compressed'), node] = 'Compressed air'

    return df


def add_node2(df, level):
    df.loc[df[level].str.contains('transport'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('electricity'), 'node1'] = 'Electricity'
    df.loc[df[level].str.contains('water production'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('heat'), 'node1'] = 'Fuel'
    df.loc[df[level].str.contains('coal'), 'node1'] = 'Fuel'
    df.loc[df[level].str.contains('natural gas'), 'node1'] = 'Fuel'
    df.loc[df[level].str.contains('petroleum gas'), 'node1'] = 'Fuel'
    df.loc[df[level].str.contains('water production'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('factory'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('Onsite'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('market for chemical'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('petroleum refinery'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('compressor'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('aluminium'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('facilit'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('nitrogen'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('waste'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('market for water'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('nitrogen'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('solvent'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('tap water'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('sludge'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('residue'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('zinc'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('lime'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('oil'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('copper'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('nickel'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('molybdenum'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('oxygen'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('chichibabin'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('potassium'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('rare earth'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('coking'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('dinitrotoluene'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('fibre'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('cobalt'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('lead production'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('acetaldehyde'), 'node1'] = 'Chemical'
    df.loc[df[level].str.contains('battery'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('steam'), 'node1'] = 'Fuel'
    df.loc[df[level].str.contains('water production'), 'node1'] = 'Other'
    df.loc[df[level].str.contains('treatment of'), 'node1'] = 'Other'
    return df


def lcia_chemical_level_5():
    db = bd.Database('chemical')
    product_list = [act for act in db if 'birch wood' in act.get('name') and 'no biogenic' in act.get('name')]
    lcia_method_list = get_lcia_method_list()
    fu = []
    product_level_0_list = []
    product_level_1_list = []
    product_level_2_list = []
    product_level_3_list = []
    product_level_4_list = []
    product_level_5_list = []
    level_list = []
    amount_list = []
    product = product_list[0]
    fu.append({product: 1})
    product_level_0_list.append(product.get('name'))
    product_level_1_list.append(999)
    product_level_2_list.append(999)
    product_level_3_list.append(999)
    product_level_4_list.append(999)
    product_level_5_list.append(999)
    level_list.append(0)
    amount_list.append(1)
    for tech_flow in product.technosphere():
        act = tech_flow.input
        amount = tech_flow['amount']
        fu.append({act: amount})
        product_level_0_list.append(product.get('name'))
        product_level_1_list.append(act.get('name'))
        product_level_2_list.append(999)
        product_level_3_list.append(999)
        product_level_4_list.append(999)
        product_level_5_list.append(999)
        level_list.append(1)
        amount_list.append(amount)
        if ('sawdust' not in act.get('name')) and ('electricity' not in act.get('name')):
            for tech_flow2 in act.technosphere():
                act2 = tech_flow2.input
                amount2 = tech_flow2['amount']
                fu.append({act2: amount * amount2})
                product_level_0_list.append(product.get('name'))
                product_level_1_list.append(act.get('name'))
                product_level_2_list.append(act2.get('name'))
                product_level_3_list.append(999)
                product_level_4_list.append(999)
                product_level_5_list.append(999)
                level_list.append(2)
                amount_list.append(amount * amount2)
                if chemical_conditions(act2):
                    for tech_flow3 in act2.technosphere():
                        act3 = tech_flow3.input
                        amount3 = tech_flow3['amount']
                        fu.append({act3: amount * amount2 * amount3})
                        product_level_0_list.append(product.get('name'))
                        product_level_1_list.append(act.get('name'))
                        product_level_2_list.append(act2.get('name'))
                        product_level_3_list.append(act3.get('name'))
                        product_level_4_list.append(999)
                        product_level_5_list.append(999)
                        level_list.append(3)
                        amount_list.append(amount * amount2 * amount3)
                        if chemical_conditions(act3):
                            for tech_flow4 in act3.technosphere():
                                act4 = tech_flow4.input
                                amount4 = tech_flow4['amount']
                                fu.append({act4: amount * amount2 * amount3 * amount4})
                                product_level_0_list.append(product.get('name'))
                                product_level_1_list.append(act.get('name'))
                                product_level_2_list.append(act2.get('name'))
                                product_level_3_list.append(act3.get('name'))
                                product_level_4_list.append(act4.get('name'))
                                product_level_5_list.append(999)
                                level_list.append(4)
                                amount_list.append(amount * amount2 * amount3 * amount4)
                                if chemical_conditions(act4):
                                    for tech_flow5 in act4.technosphere():
                                        act5 = tech_flow5.input
                                        amount5 = tech_flow5['amount']
                                        fu.append({act5: amount * amount2 * amount3 * amount4 * amount5})
                                        product_level_0_list.append(product.get('name'))
                                        product_level_1_list.append(act.get('name'))
                                        product_level_2_list.append(act2.get('name'))
                                        product_level_3_list.append(act3.get('name'))
                                        product_level_4_list.append(act4.get('name'))
                                        product_level_5_list.append(act5.get('name'))
                                        level_list.append(5)
                                        amount_list.append(amount * amount2 * amount3 * amount4 * amount5)
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_agri'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_agri')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Amount'] = amount_list
    df['Level0'] = product_level_0_list
    df['Level1'] = product_level_1_list
    df['Level2'] = product_level_2_list
    df['Level3'] = product_level_3_list
    df['Level4'] = product_level_4_list
    df['Level5'] = product_level_5_list
    df['Level'] = level_list
    df['GWP'] = df.iloc[:, 0:3].sum(axis=1)
    df = df.iloc[:, 7:]
    df0 = df.loc[df.Level == 0].copy()
    df1 = df.loc[df.Level == 1].copy()
    impact_onsite = df0['GWP'].sum() - df1['GWP'].sum()
    df_temp = pd.DataFrame(columns=['GWP', 'Level0', 'Level1', 'Level2', 'Level3', 'Level4', 'Level5', 'Level'],
                           data=[[impact_onsite, df0['Level0'].iloc[0], 'Onsite', 999, 999, 999, 999, 1]])
    df1 = pd.concat([df1, df_temp], ignore_index=True)
    df1['node2'] = 'Biomass fractionation'
    df1 = add_node1(df1, 'Level1', 'node1')
    df1.loc[df1.Level1.str.contains('sawdust'), 'node1'] = 'Biomass feedstock'
    df1.loc[df1.Level1.str.contains('electricity'), 'node1'] = 'Electricity'
    df1.loc[df1.Level1.str.contains('Onsite'), 'node1'] = 'Onsite'
    df2 = df.loc[(df.Level == 2)].copy()
    df2 = add_node1(df2, 'Level1', 'node2')
    df2 = add_node2(df2, 'Level2')
    df21 = df2[df2.node1.isna()].copy()
    df22 = df2[~df2.node1.isna()].copy()
    df3 = df[(df.Level == 3) & df.Level2.isin(list(df21.Level2.unique()))].copy()
    for x in list(df21.Level2.unique()):
        df_temp = df.loc[(df.Level2 == x) & (df.Level.isin([2, 3]))].copy()
        df_temp = pd.pivot_table(df_temp, index=['Level0', 'Level1', 'Level2', 'Level4', 'Level5'], columns='Level',
                                 values='GWP', aggfunc='sum')
        df_temp['GWP'] = df_temp[2]-df_temp[3]
        df_temp.reset_index(inplace=True)
        df_temp = df_temp[['Level0', 'Level1', 'Level2', 'Level4', 'Level5', 'GWP']].copy()
        df_temp['Level3'] = 'Onsite'
        df3 = pd.concat([df3, df_temp], ignore_index=True)
    df3 = add_node1(df3, 'Level1', 'node2')
    df3 = add_node2(df3, 'Level3')
    df31 = df3[df3.node1.isna()].copy()
    df32 = df3[~df3.node1.isna()].copy()
    df4 = df[(df.Level == 4) & df.Level3.isin(list(df31.Level3.unique()))].copy()
    for x in list(df31.Level3.unique()):
        df_temp = df.loc[(df.Level3 == x) & (df.Level.isin([3, 4]))].copy()
        df_temp = pd.pivot_table(df_temp, index=['Level0', 'Level1', 'Level2', 'Level3', 'Level5'], columns='Level',
                                 values='GWP', aggfunc='sum')
        df_temp['GWP'] = df_temp[3]-df_temp[4]
        df_temp.reset_index(inplace=True)
        df_temp = df_temp[['Level0', 'Level1', 'Level2', 'Level3', 'Level5', 'GWP']].copy()
        df_temp['Level4'] = 'Onsite'
        df4 = pd.concat([df4, df_temp], ignore_index=True)
    df4 = add_node1(df4, 'Level1', 'node2')
    df4 = add_node2(df4, 'Level4')
    df41 = df4[df4.node1.isna()].copy()
    df42 = df4[~df4.node1.isna()].copy()
    df5 = df[(df.Level == 5) & df.Level4.isin(list(df41.Level4.unique()))].copy()
    for x in list(df41.Level4.unique()):
        df_temp = df.loc[(df.Level4 == x) & (df.Level.isin([4, 5]))].copy()
        df_temp = pd.pivot_table(df_temp, index=['Level0', 'Level1', 'Level2', 'Level3', 'Level4'], columns='Level',
                                 values='GWP', aggfunc='sum')
        df_temp['GWP'] = df_temp[4]-df_temp[5]
        df_temp.reset_index(inplace=True)
        df_temp = df_temp[['Level0', 'Level1', 'Level2', 'Level3', 'Level4', 'GWP']].copy()
        df_temp['Level5'] = 'Onsite'
        df5 = pd.concat([df5, df_temp], ignore_index=True)
    df5 = add_node1(df5, 'Level1', 'node2')
    df5['node1'] = 'Chemical'
    df5 = add_node2(df5, 'Level5')
    df_out = pd.concat([df1, df22, df32, df42, df5], ignore_index=True)
    df_out = pd.pivot_table(df_out, index=['node1', 'node2'], values='GWP', aggfunc='sum')
    df_out.reset_index(inplace=True)
    return df_out


def lcia_luc_forest(year, scenario):
    product_list = get_forest_acts_for_lcia(year, scenario)
    product_name_list = []
    country_list = []
    lu_list = []
    value_list = []
    for act in product_list:
        if 'sustainable forest management' in act.get('name'):
            for exc in act.exchanges():
                if ('Occupation' in exc.get('name') or
                    'Transformation' in exc.get('name')) and 'traffic area' not in exc.get('name'):
                    product_name_list.append(act.get('name'))
                    country_list.append(act.get('location'))
                    lu_list.append(exc.get('name'))
                    value_list.append(exc.get('amount'))
        else:
            for exc in act.exchanges():
                if 'sawlog' in exc.get('name'):
                    amount = exc.get('amount')
                    act2 = bd.get_activity(exc.get('input'))
                    for exc2 in act2.exchanges():
                        if ('Occupation' in exc2.get('name') or
                            'Transformation' in exc2.get('name')) and 'traffic area' not in exc2.get('name'):
                            product_name_list.append(act.get('name'))
                            country_list.append(act.get('location'))
                            lu_list.append(exc2.get('name'))
                            value_list.append(exc2.get('amount') * amount)

    df = pd.DataFrame.from_dict({'Product': product_name_list,
                                 'Country': country_list,
                                 'LU': lu_list,
                                 'Value': value_list})
    df_temp = df.copy()
    df_temp['name1'] = 'Logging residue'
    df_temp.loc[df_temp.Product.str.contains('slab'), 'name1'] = 'WoodChips'
    df_temp.loc[df_temp.Product.str.contains('sawdust'), 'name1'] = 'Sawdust'
    df_temp['name2'] = 'non-conifer'
    df_temp.loc[df_temp.Product.str.contains('softwood'), 'name2'] = 'conifer'
    df_temp['name'] = df_temp[['name1', 'name2']].agg(', '.join, axis=1)
    df['Product'] = df_temp['name']
    df = pd.pivot_table(df, index=['Product', 'Country'], columns='LU', values='Value')
    trans_from_list = [x for x in df.columns if 'Transformation, from' in x]
    df['Transformation, from primary forest'] = df['Transformation, to forest, extensive'] - \
                                                df[trans_from_list].sum(axis=1)
    df.reset_index(inplace=True)
    df.to_csv(f'data/interim/forest_lci_luc_per_kg_product_{year}_{scenario}.csv')
    return df


def onsite_ghg_glo(year, scenario):
    product_list = get_crop_acts_glo_for_lcia(year, scenario)
    df_ghg = pd.DataFrame()
    for product in product_list:
        product_name = product.get('name').split(',')[0]
        exc_lime = 0
        exc_co2_peat = 0
        exc_manure_direct = 0
        exc_manure_indirect = 0
        exc_n2o_peat = 0
        exc_rice = 0
        exc_ch4_peat = 0
        for exc_glo in product.exchanges():
            if exc_glo.get('type') == 'technosphere':
                act = bd.get_activity(exc_glo.get('input'))
                amount = exc_glo.get('amount')
                for exc in act.exchanges():
                    if exc.get('type') == 'biosphere':
                        if 'Carbon dioxide, fossil' in exc.get('name'):
                            if 'Lime' in exc['comment']:
                                exc_lime += exc.get('amount') * amount
                            elif 'peat' in exc['comment']:
                                exc_co2_peat = exc.get('amount') * amount
                        elif 'Dinitrogen monoxide' in exc.get('name'):
                            if 'Direct Manure' in exc['comment']:
                                exc_manure_direct += exc.get('amount') * amount
                            elif 'Indirect Manure' in exc['comment']:
                                exc_manure_indirect += exc.get('amount') * amount
                            elif 'peat' in exc['comment']:
                                exc_n2o_peat += exc.get('amount') * amount
                        elif 'Methane' in exc.get('name'):
                            if 'rice' in exc['comment']:
                                exc_rice += exc.get('amount') * amount
                            elif 'peat' in exc['comment']:
                                exc_ch4_peat += exc.get('amount') * amount
        df_temp = pd.DataFrame(
            [[product_name, "CO2_lime", exc_lime],
             [product_name, "CO2_peat", exc_co2_peat],
             [product_name, "N2O_manure_direct", exc_manure_direct],
             [product_name, "N2O_manure_indirect", exc_manure_indirect],
             [product_name, "N2O_peat", exc_n2o_peat],
             [product_name, "CH4_rice", exc_rice],
             [product_name, "CH4_peat", exc_ch4_peat]])
        df_ghg = pd.concat([df_ghg, df_temp], ignore_index=True)
    df_ghg = df_ghg.rename(columns={0: 'CROP', 1: 'GHG', 2: 'AMOUNT'})
    return df_ghg


def lcia_crop_onsite_ghg(year, scenario):
    df_ghg = pd.DataFrame(columns=['CROP', 'COUNTRY', 'GHG', 'AMOUNT'])
    product_list = get_crop_acts_for_lcia(year, scenario)
    df_ghg_glo = onsite_ghg_glo(year, scenario)
    for product in product_list:
        product_name = product.get('name').split(',')[0]
        product_country = product.get('name')[-3:-1]
        for exc in product.exchanges():
            if exc.get('type') == 'biosphere':
                if 'Carbon dioxide, fossil' in bd.get_activity(exc.get('input')).get('name'):
                    exc_name = -999
                    exc_val = -999
                    if 'Lime' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'CO2_lime'
                    elif 'Emission CO2, modified by JH' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'CO2_fert'
                    elif 'peat' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'CO2_peat'
                    df_temp = pd.DataFrame([[product_name, product_country, exc_name, exc_val]],
                                           columns=['CROP', 'COUNTRY', 'GHG', 'AMOUNT'])
                    df_ghg = pd.concat([df_ghg, df_temp], ignore_index=True)
                elif 'Dinitrogen monoxide' in bd.get_activity(exc.get('input')).get('name'):
                    exc_name = -999
                    exc_val = -999
                    if 'Emission N2O direct, modified by JH' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_fert_direct'
                    elif 'Emission N2O indirect, modified by JH' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_fert_indirect'
                    elif 'Direct Manure' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_manure_direct'
                    elif 'Indirect Manure' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_manure_indirect'
                    elif 'Emission N2O direct CR, modified by JH' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_cr_direct'
                    elif 'Emission N2O indirect CR, modified by JH' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_cr_indirect'
                    elif 'peat' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'N2O_peat'
                    df_temp = pd.DataFrame([[product_name, product_country, exc_name, exc_val]],
                                           columns=['CROP', 'COUNTRY', 'GHG', 'AMOUNT'])
                    df_ghg = pd.concat([df_ghg, df_temp], ignore_index=True)
                elif 'Methane' in bd.get_activity(exc.get('input')).get('name'):
                    exc_name = -999
                    exc_val = -999
                    if 'rice' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'CH4_rice'
                    elif 'peat' in exc['comment']:
                        exc_val = exc.get('amount')
                        exc_name = 'CH4_peat'
                    df_temp = pd.DataFrame([[product_name, product_country, exc_name, exc_val]],
                                           columns=['CROP', 'COUNTRY', 'GHG', 'AMOUNT'])
                    df_ghg = pd.concat([df_ghg, df_temp], ignore_index=True)
            elif 'unchanged' in exc.get('name'):
                df_temp = df_ghg_glo[df_ghg_glo.CROP == product_name].copy()
                df_temp['COUNTRY'] = product_country
                df_ghg = pd.concat([df_ghg, df_temp], ignore_index=True)
    df_ghg['IMPACT'] = df_ghg['AMOUNT']
    df_ghg.loc[df_ghg.GHG.str.contains('N2O'), 'IMPACT'] *= 298
    df_ghg.loc[df_ghg.GHG.str.contains('CH4_rice'), 'IMPACT'] *= 34
    df_ghg.loc[df_ghg.GHG.str.contains('CH4_peat'), 'IMPACT'] *= 36.8
    return df_ghg


def lcia_crop_onsite_ghg_less_cat(year, scenario):
    df = lcia_crop_onsite_ghg(year, scenario)
    df['GHG_cat'] = 'Others'
    df.loc[df.GHG.str.contains('N2O_cr'), 'GHG_cat'] = 'N2O, crop residue'
    df.loc[df.GHG.str.contains('N2O_fer'), 'GHG_cat'] = 'N2O, fertilizer'
    df.loc[df.GHG.str.contains('N2O_manure'), 'GHG_cat'] = 'N2O, manure'
    df.loc[df.GHG.str.contains('CO2'), 'GHG_cat'] = 'CO2'
    df.loc[df.GHG.str.contains('CH4'), 'GHG_cat'] = 'CH4'
    df.loc[df.GHG.str.contains('N2O_peat'), 'GHG_cat'] = 'N2O, Peat'
    df = pd.pivot_table(df, index=['CROP', 'COUNTRY'], columns='GHG_cat', values='IMPACT',
                        aggfunc='sum')
    df.reset_index(inplace=True)
    df = df.fillna(0)
    return df


def lcia_crop_glo_contribution(year, scenario):
    product_list = get_crop_acts_glo_for_lcia(year, scenario)
    lcia_method_list = get_lcia_method_list()
    product_name_list = []
    fu = []
    product_level_0_list = []
    product_level_1_list = []
    level_list = []
    for product in product_list:
        product_name = product.get('name').split(',')[0]
        for tech_flow in product.technosphere():
            act = tech_flow.input
            amount = tech_flow['amount']
            fu.append({act: amount})
            product_name_list.append(product_name)
            product_level_0_list.append(act.get('name'))
            product_level_1_list.append(act.get('name').split('{')[0])
            level_list.append(1)
            for tech_flow2 in act.technosphere():
                act2 = tech_flow2.input
                amount2 = tech_flow2['amount']
                fu.append({act2: amount * amount2})
                product_name_list.append(product_name)
                product_level_0_list.append(act.get('name'))
                product_level_1_list.append(act2.get('name').split('{')[0])
                level_list.append(2)
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_agri'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_agri')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Product_country'] = product_level_0_list
    df['Activity'] = product_level_1_list
    df['Level'] = level_list
    df['Product'] = product_name_list
    df2 = df.groupby(by=['Product', 'Level', 'Activity']).sum(numeric_only=True)
    df2.reset_index(inplace=True)
    df_onsite = df.groupby(by=['Product', 'Level']).sum(numeric_only=True)
    df_onsite.reset_index(inplace=True)
    product_name_glo_list = list(df_onsite.Product.unique())
    df_onsite.set_index(['Level'], inplace=True)
    for product in product_name_glo_list:
        df_temp = df_onsite.loc[df_onsite.Product == product].copy()
        df_temp = df_temp.drop(['Product'], axis=1)
        df_temp.loc['onsite'] = df_temp.loc[1] - df_temp.loc[2]
        df_temp = df_temp.loc[['onsite'], :].copy()
        df_temp['Product'] = product
        df_temp['Level'] = 2
        df_temp['Activity'] = 'onsite'
        df2 = pd.concat([df2, df_temp], ignore_index=True)
        df2 = df2.loc[df2.Level == 2].copy()
    return df2


def lcia_crop_contribution(year, scenario):
    df_glo = lcia_crop_glo_contribution(year, scenario)
    df_glo['Level'] = 1
    product_list = get_crop_acts_for_lcia(year, scenario) #datasets for lcia calculation
    lcia_method_list = get_lcia_method_list() #list of lcia method
    product_level_1_list = []
    level_list = []
    fu = []
    product_name_list = []
    product_country_list = []
    for product in product_list:
        product_name = product.get('name').split(',')[0]
        product_country = product.get('name')[-3:-1]
        fu.append({product: 1})
        product_name_list.append(product_name)
        product_country_list.append(product_country)
        product_level_1_list.append(product.get('name').split('{')[0])
        level_list.append(0)
        for tech_flow in product.technosphere(): #go through each technosphere flow to identify their contribution
            act = tech_flow.input
            amount = tech_flow['amount']
            fu.append({act: amount})
            product_name_list.append(product_name)
            product_country_list.append(product_country)
            product_level_1_list.append(act.get('name').split('{')[0])
            level_list.append(1)
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_agri'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_agri')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Activity'] = product_level_1_list
    df['Level'] = level_list
    df['Product'] = product_name_list
    df['Country'] = product_country_list
    df_onsite = df.groupby(by=['Product', 'Country', 'Level']).sum(numeric_only=True)
    df_onsite.reset_index(inplace=True)
    product_name_glo_list = list(df_onsite.Product.unique())
    df_onsite.set_index(['Level'], inplace=True)
    for product in product_name_glo_list:
        for country in list(df_onsite[df_onsite.Product == product].Country.unique()):
            df_temp = df_onsite.loc[(df_onsite.Product == product) & (df_onsite.Country == country)].copy()
            df_temp = df_temp.drop(['Product', 'Country'], axis=1)
            df_temp.loc['onsite'] = df_temp.loc[0] - df_temp.loc[1]
            df_temp = df_temp.loc[['onsite'], :].copy()
            df_temp['Product'] = product
            df_temp['Country'] = country
            df_temp['Level'] = 1
            df_temp['Activity'] = 'onsite'
            df = pd.concat([df, df_temp], ignore_index=True)
    df = df[df.Level == 1].copy()
    df_unchanged = df[df.Activity.str.contains('unchanged')].copy()
    for product in product_name_glo_list:
        df_temp_glo = df_glo.loc[df_glo.Product == product].copy()
        for country in list(df_unchanged[df_unchanged.Product == product].Country.unique()):
            df_temp = df_temp_glo.copy()
            df_temp['Country'] = country
            df = pd.concat([df, df_temp], ignore_index=True)
    df = df[~df.Activity.str.contains('unchanged')].copy()
    return df


def lcia_crop_ghg_contribution(year, scenario):
    df = lcia_crop_contribution(year, scenario)
    df2 = lcia_crop_onsite_ghg_less_cat(year, scenario)
    df['Cat'] = 'Others'
    df.loc[(df.Activity.str.contains('NPK') | df.Activity.str.contains('Lime')), 'Cat'] = 'Fertilizer production'
    df.loc[df.Activity.str.contains('icide'), 'Cat'] = 'Fertilizer production'
    df.loc[df.Activity.str.contains('icide emissions'), 'Cat'] = 'Onsite'
    df.loc[df.Activity.str.contains('onsite'), 'Cat'] = 'Onsite'
    df.loc[(df.Activity.str.contains('diesel') | (df.Activity.str.contains('electricity'))), 'Cat'] = 'Machinery energy'
    df.loc[(df.Activity.str.contains('start material') | df.Activity.str.contains('Lime')), 'Cat'] = 'Seed'
    df['GHG_LUC'] = df['IPCC_AR6', 'GWP_100a', 'LUC'].copy()
    df['GHG_non_LUC'] = df['IPCC_AR6', 'GWP_100a', 'Fossil'] + df['IPCC_AR6', 'GWP_100a', 'Biogenic']
    df_luc = pd.pivot_table(df, index=['Product', 'Country'],
                            values='GHG_LUC',
                            aggfunc='sum')
    df_luc['Cat'] = 'Land use change'
    df_luc.reset_index(inplace=True)
    df_luc = df_luc.rename(columns={"GHG_LUC": 'GHG'})
    df_cat = pd.pivot_table(df, index=['Product', 'Country', 'Cat'],
                            values='GHG_non_LUC',
                            aggfunc='sum')
    df_cat.reset_index(inplace=True)
    df_cat = df_cat.rename(columns={"GHG_non_LUC": 'GHG'})
    df_cat = pd.concat([df_cat, df_luc], ignore_index=True)
    df2 = df2.rename(columns={'CROP': 'Product', 'COUNTRY': 'Country'})
    df_cat['GHG_sub'] = df_cat['GHG']
    df_cat.loc[df_cat.Cat == 'Onsite', 'GHG_sub'] = 0
    for ghg in list(df2.columns)[2:]:
        cat_name = f'Onsite, {ghg}'
        df_temp = df2[['Product', 'Country', ghg]].copy()
        df_temp = df_temp.rename(columns={ghg: 'GHG_sub'})
        df_temp['Cat'] = cat_name
        df_cat = pd.concat([df_cat, df_temp], ignore_index=True)
    df_cat = df_cat.fillna(0)
    file_name = f'data/interim/lcia_ghg_contribution_{year}_{scenario}.csv'
    df_cat.to_csv(file_name)
    return df_cat


def read_crop_lci_csv(year, scenario):
    if os.path.exists(r'data/interim/crop_lci.csv'):
        df = pd.read_csv(r'data/interim/crop_lci.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        from src.data.agriculture_lci import crop_lci_final_output
        df = crop_lci_final_output()
    df_scenario = df.loc[(df.YEAR == year) & (df.SCENARIO == scenario)].copy()
    return df_scenario


def lcia_crop_allocation(year, scenario, price):
    df_lci = read_crop_lci_csv(year, scenario)
    df_lci = df_lci.rename(columns={'Crop': 'Product',
                                    'Yield_kg_per_ha': 'Yield_c',
                                    'Residue_removal_kg_per_ha': 'Yield_r',
                                    'Price_crop_USD_per_t': 'Price_c',
                                    'Price_residue_USD_per_t': 'Price_r',
                                    'Price_residue_min_USD_per_t': 'Price_r_min'})
    df_lci = df_lci[['Product', 'Country', 'Yield_c', 'Yield_r',
                     'Price_c', 'Price_r', 'Price_r_min']].copy()
    if price == 'normal':
        df_lci['Alloc_r'] = df_lci['Yield_r'] * df_lci['Price_r'] / (df_lci['Yield_r'] * df_lci['Price_r'] +
                                                                     df_lci['Yield_c'] * df_lci['Price_c'])
    else:
        df_lci['Alloc_r'] = df_lci['Yield_r'] * df_lci['Price_r_min'] / (df_lci['Yield_r'] * df_lci['Price_r_min'] +
                                                                          df_lci['Yield_c'] * df_lci['Price_c'])
    return df_lci


def lcia_crop_add_price(year, scenario, price):
    df = lcia_crop(year, scenario)
    df['GHG'] = df['IPCC_AR6', 'GWP_100a', 'all']
    df['BDV'] = df['Biodiversity regionalized', 'Occupation'] + df['Biodiversity regionalized', 'Transformation']
    df['BDV_OCC'] = df['Biodiversity regionalized', 'Occupation']
    df['BDV_TRA'] = df['Biodiversity regionalized', 'Transformation']
    df['GTP'] = df['IPCC_AR6', 'GTP_100a', 'all']
    df['WATER'] = df['AWARE regionalized', 'Annual']
    df = df[['Product', 'Country', 'GHG', 'BDV', 'BDV_OCC', 'BDV_TRA', 'WATER', 'GTP']].copy()
    df_lci = lcia_crop_allocation(year, scenario, price)
    #df_lci = df_lci[['Product', 'Country', 'Yield_r', 'Alloc_r']].copy()
    df = pd.merge(df, df_lci, on=['Product', 'Country'], how='left')
    df['Product'] = df['Product'].map(residue_crop_dict)
    df.to_csv(f'data/interim/lcia_crop_add_price_{year}_{scenario}_{price}.csv')
    df1 = df[(df.Country == 'BR') | (df.Country == 'CN')].copy()
    df1['BDV'] *= 1e15
    return df


def lcia_crop_residue_per_kg(year, scenario, price):
    df = lcia_crop_add_price(year, scenario, price)
    for impact in ['GHG', 'BDV', 'BDV_OCC', 'BDV_TRA', 'WATER', 'GTP']:
        df[impact] = df[impact] * df['Alloc_r'] / df['Yield_r']
    df = df[['Product', 'Country', 'GHG', 'BDV', 'BDV_OCC', 'BDV_TRA', 'WATER', 'GTP']].copy()
    return df


def lcia_all(year, scenario, price):
    df_forest = lcia_forest(year, scenario)
    df_crop = lcia_crop_residue_per_kg(year, scenario, price)
    df = pd.concat([df_forest, df_crop], ignore_index=True)
    file_name = f'data/interim/lcia_all_residues_{year}_{scenario}_{price}.csv'
    df.to_csv(file_name)
    return df


def lcia_electricity(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}_regionalized'
    ei = bd.Database(ei_name)
    product_list = [act for act in ei if 'market group for electricity, medium voltage' == act.get('name')]
    fu = [{product: 1} for product in product_list]
    lcia_method_list = []
    for method in bd.methods:
        if (
                ('EF v3.0' in method
                 and (("global warming potential (GWP100)" in method
                       and 'climate change' == method[1]))
                 )
        ):
            lcia_method_list.append(method)
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_electricity'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_electricity')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Product'] = [act.get('name') for act in product_list]
    df['Country'] = [act.get('location') for act in product_list]
    df['Act_key'] = [act.key for act in product_list]
    df['GHG'] = df.iloc[:,0]
    electricity_scenario_list = [df.loc[df.GHG == df['GHG'].max(), 'Act_key'].iloc[0],
                                 df.loc[df.GHG == df['GHG'].min(), 'Act_key'].iloc[0]]
    return electricity_scenario_list


def lcia_chemical_level_1(year, scenario, price):
    db = bd.Database('chemical')
    product_list = [act for act in db if 'birch wood' in act.get('name')]
    lcia_method_list = get_lcia_method_list()
    fu = []
    product_level_0_list = []
    product_level_1_list = []
    level_list = []
    amount_list = []
    sce = 0
    df_out = pd.DataFrame()
    for product in product_list:
        sce += 1
        fu.append({product: 1})
        product_level_0_list.append(f'S{sce}')
        product_level_1_list.append(999)
        level_list.append(0)
        amount_list.append(1)
        for tech_flow in product.technosphere():
            act = tech_flow.input
            amount = tech_flow['amount']
            fu.append({act: amount})
            product_level_0_list.append(f'S{sce}')
            product_level_1_list.append(act.get('name'))
            level_list.append(1)
            amount_list.append(amount)
    multi_lca_setup = {'inv': fu, 'ia': lcia_method_list}
    bc.multi_lca.calculation_setups['multi_lca_chem'] = multi_lca_setup
    mlca = bc.multi_lca.MultiLCA('multi_lca_chem')
    df = pd.DataFrame(mlca.results, columns=lcia_method_list)
    df['Amount'] = amount_list
    df['Level0'] = product_level_0_list
    df['Level1'] = product_level_1_list
    df['Level'] = level_list
    df['GWP'] = df.iloc[:, 0:3].sum(axis=1)
    df = df.iloc[:, 7:]
    for sce in list(df.Level0.unique()):
        df0 = df.loc[(df.Level == 0) & (df.Level0 == sce)].copy()
        df1 = df.loc[(df.Level == 1) & (df.Level0 == sce)].copy()
        impact_onsite = df0['GWP'].sum() - df1['GWP'].sum()
        df_temp = pd.DataFrame(columns=['GWP', 'Level0', 'Level1', 'Level'],
                               data=[[impact_onsite, df0['Level0'].iloc[0], 'Onsite', 1]])
        df1 = pd.concat([df1, df_temp], ignore_index=True)
        df1 = add_node1(df1, 'Level1', 'node1')
        df1.loc[df1.Level1.str.contains('sawdust'), 'node1'] = 'Biomass feedstock'
        df1.loc[df1.Level1.str.contains('compressed air'), 'node1'] = 'Others'
        df1.loc[df1.Level1.str.contains('electricity'), 'node1'] = 'Electricity'
        df1.loc[df1.Level1.str.contains('Onsite'), 'node1'] = 'Onsite'
        df1 = pd.pivot_table(df1, index=['Level0', 'node1'], values='GWP', aggfunc='sum')
        df1.reset_index(inplace=True)
        df_out = pd.concat([df_out, df1], ignore_index=True)
    # df_out = pd.pivot_table(df_out, index='node1', columns='Level0', values='GWP', aggfunc='sum')
    df_biomass = lcia_all(year, scenario, price)
    df_biomass['check'] = abs(df_biomass['GHG'] - df_biomass['GHG'].quantile(0.95))
    biomass_impact_max = df_biomass.loc[df_biomass['check'] == df_biomass['check'].min(), 'GHG'].iloc[0]
    biomass_impact_min = df_biomass.loc[df_biomass['GHG'] == df_biomass['GHG'].min(), 'GHG'].iloc[0]
    df_out_2 = df_out.copy()
    df_out.loc[df_out.node1 == 'Biomass feedstock', 'GWP'] = biomass_impact_max
    df_out.loc[df_out.Level0 == 'S1', 'Level0'] = 'S5'
    df_out.loc[df_out.Level0 == 'S2', 'Level0'] = 'S6'
    df_out.loc[df_out.Level0 == 'S3', 'Level0'] = 'S7'
    df_out.loc[df_out.Level0 == 'S4', 'Level0'] = 'S8'
    df_out_2.loc[df_out_2.node1 == 'Biomass feedstock', 'GWP'] = biomass_impact_min
    df_out = pd.concat([df_out_2, df_out], ignore_index=True)
    return df_out
