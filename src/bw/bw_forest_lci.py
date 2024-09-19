import bw2data as bd
import pandas as pd
from bw2io.utils import activity_hash

from src.other.name_match import regionalized_act, luluc_list, get_luc_dict, get_lca_db_locations, sawmill_product_list
from src.data.forest_lci import calculate_forest_occupation_and_transformation
from src.other.read_globiom_data import read_globiom_price_data


def get_harvest_activities_list(ei):
    print(f'---Get list of harvest activities to be regionalized---')
    harvest_activities = []
    for act in ei:
        if (
                (act.get('name') == 'hardwood forestry, mixed species, sustainable forest management'
                 or act.get('name') == 'softwood forestry, mixed species, sustainable forest management')
                and act.get('location') == 'CH'
        ):
            for exc in act.exchanges():
                if exc.get('type') == 'technosphere':
                    input_code = exc.get('input')
                    act2 = bd.get_activity(input_code)
                    for exc2 in act2.exchanges():
                        if (
                                exc2.get('location') == 'WEU'
                                and act2 not in harvest_activities
                        ):
                            harvest_activities.append(act2)
    return harvest_activities


def get_harvest_activities_names_list(ei):
    list_harvest_activities = get_harvest_activities_list(ei)
    list_harvest_activities_names = []
    for act in list_harvest_activities:
        if act.get('name') not in list_harvest_activities_names:
            list_harvest_activities_names.append(act.get('name'))
    return list_harvest_activities_names


def get_wood_production_list(ei):
    print(f'---Get list of wood products productions to be regionalized---')
    wood_activities = []
    for act in ei:
        if (
                (act.get('name') == 'hardwood forestry, mixed species, sustainable forest management'
                 or act.get('name') == 'softwood forestry, mixed species, sustainable forest management')
                and act.get('location') == 'CH'
        ):
            wood_activities.append(act)
    return wood_activities


def get_sawing_activity_list(ei, wood_type):
    act_list = [act for act in ei if (
            f'sawing, {wood_type}' in act['name'] and
            'CH' in act['location'])]
    return act_list


def get_sawnwood_activity(act_list):
    act_list_1 = [act for act in act_list if 'cubic meter' in act['unit']]
    return act_list_1[0]


def get_original_ei_sawnmill_inventory(ei, wood_type):
    df_sawmill = pd.DataFrame(columns=['PRODUCT', 'UNIT', 'PRODUCTION', 'PRICE', 'ALLOCATION', 'SAWLOG_M3',
                                       'ELE_KWH', 'DIESEL_MJ', 'LUBOIL_KG', 'WASTE_MINERAL_OIL_KG',
                                       'SAWMILL_UNIT', 'CO2_KG'])
    density = get_wood_density(wood_type)
    if wood_type == "hardwood":
        alloc_sw = 0.9092
        alloc_slab = 0.0659
        alloc_sawdust = 0.0129
        alloc_bark = 0.0120
    else:
        alloc_sw = 0.9145
        alloc_slab = 0.0539
        alloc_sawdust = 0.0168
        alloc_bark = 0.0148
    list_sawing = get_sawing_activity_list(ei, wood_type)
    for act in list_sawing:
        product = 0
        unit = 0
        production = 0
        sawlog = 0
        for exc in act.exchanges():
            if exc.get('type') == 'production':
                product = act.get('reference product')
                unit = exc.get('unit')
                production = exc.get('amount')
            elif exc.get('name') == f'market for sawlog and veneer log, {wood_type}, measured as solid wood under bark':
                sawlog = exc.get('amount')
        df_temp = pd.DataFrame([[product, unit, production, sawlog]],
                               columns=['PRODUCT', 'UNIT', 'PRODUCTION', 'SAWLOG_M3'])
        df_sawmill = pd.concat([df_sawmill, df_temp], ignore_index=True)
    df_sawmill.loc[df_sawmill.UNIT == 'kilogram', 'SAWLOG_M3'] *= density
    df_sawmill.loc[df_sawmill.UNIT == 'kilogram', 'UNIT'] = 'cubic meter'
    # original allocation information according to ecoinvent documentation
    df_sawmill.loc[df_sawmill.PRODUCT == f'sawnwood, {wood_type}, raw', 'ALLOCATION'] = alloc_sw
    df_sawmill.loc[df_sawmill.PRODUCT == 'bark', 'ALLOCATION'] = alloc_bark
    df_sawmill.loc[df_sawmill.PRODUCT == 'sawdust, loose, wet, measured as dry mass', 'ALLOCATION'] = alloc_sawdust
    df_sawmill.loc[
        df_sawmill.PRODUCT == f'slab and siding, {wood_type}, wet, measured as dry mass', 'ALLOCATION'] = alloc_slab

    allocation_core = alloc_sw  # for sawnwood
    sawlog_core = df_sawmill.loc[df_sawmill.PRODUCT == f'sawnwood, {wood_type}, raw', 'SAWLOG_M3'].iloc[0]
    for x in df_sawmill.index:
        allocation = df_sawmill.loc[x, 'ALLOCATION']
        sawlog = df_sawmill.loc[x, 'SAWLOG_M3']
        production = sawlog_core / allocation_core * allocation / sawlog
        price = allocation / allocation_core / production
        df_sawmill.loc[x, 'PRODUCTION'] = production
        df_sawmill.loc[x, 'PRICE'] = price
    df = pd.DataFrame(columns=['type', 'unit', 'name', 'price', 'amount'])
    for exc in get_sawnwood_activity(list_sawing).exchanges():
        if exc.get('type') != 'production':
            df_temp = pd.DataFrame([[exc.get('type'), exc.get('unit'), exc.get('name'),
                                     exc.get('input'), exc.get('amount')]],
                                   columns=['type', 'unit', 'name', 'input', 'amount'])
            df = pd.concat([df, df_temp], ignore_index=True)
    df.loc[df.type != 'production', 'amount'] /= 0.9092
    for x in df_sawmill.index:
        product = df_sawmill.loc[x, 'PRODUCT']
        amount = df_sawmill.loc[x, 'PRODUCTION']
        df_temp = pd.DataFrame([['production', 'cubic meter', product, amount]],
                               columns=['type', 'unit', 'name', 'amount'])
        df = pd.concat([df, df_temp], ignore_index=True)
    for product_name in list(df['name'].unique()):
        if product_name in list(df_sawmill.PRODUCT.unique()):
            price = df_sawmill.loc[df_sawmill.PRODUCT == product_name, 'PRICE'].iloc[0]
            df.loc[df.name == product_name, 'price'] = price
    return df


def get_wood_density(wood_type):
    if wood_type == 'hardwood':
        density = 560
    else:
        density = 450
    return density


def read_image_region_mapping():
    df_region = pd.read_excel(r'data/raw_data/GLOBIOM_IMAGE_region_mapping.xlsx',
                              engine='openpyxl', sheet_name='Sheet1')
    return df_region


def get_image_region_list():
    df_region = read_image_region_mapping()
    image_region_list = list(df_region.IMAGE_REGION.unique())
    return image_region_list


def get_regionalized_act_code(ei):
    print(f'---Get input code of regionalized act from premise in a dataframe---')
    image_region_list = get_image_region_list()
    df_regionalized_act_code = pd.DataFrame(columns=regionalized_act, index=image_region_list)
    for act in ei:
        if (
                act.get('name') in regionalized_act
                and act.get('location') in image_region_list
        ):
            df_regionalized_act_code.loc[act.get('location'), act.get('name')] = act.get('code')
    return df_regionalized_act_code


def get_wood_price(year, scenario):
    df = read_globiom_price_data()
    df = df[(df.YEAR == year) & (df.SCENARIO == scenario)].copy()
    df = df[df.PRODUCT.isin(sawmill_product_list)].copy()
    df_region = read_image_region_mapping()
    df['REGION'] = df['REGION'].map(df_region.set_index('GLOBIOM_REGION')['IMAGE_REGION'])
    df = pd.pivot_table(df, index='REGION', columns='PRODUCT', values='VALUE', aggfunc='sum')
    df.reset_index(inplace=True)
    return df


def create_regionalized_harvest_activitiy(ei, ei_name, new_db_name):
    db_dict = {}
    image_region_list = get_image_region_list()
    list_harvest_activities = get_harvest_activities_list(ei)
    df_regionalized_act_code = get_regionalized_act_code(ei)
    for act in list_harvest_activities:
        for region in image_region_list:
            act_dict = {"name": act.get('name'),
                        'reference product': act.get('reference product'),
                        'exchanges': [],
                        'unit': act.get('unit'),
                        'location': region
                        }
            for exc in act.exchanges():
                if exc.get('type') != 'production':
                    if exc.get('name') in regionalized_act:
                        input_code = df_regionalized_act_code.loc[region, exc.get('name')]
                        input_input = (ei_name, input_code)
                    else:
                        input_input = exc.get('input')
                    exc = {
                        "name": exc.get('name'),
                        "amount": exc.get('amount'),
                        "input": input_input,
                        "type": exc.get('type')
                    }
                    act_dict.get('exchanges').append(exc)
            dbname_code = (new_db_name, activity_hash(act_dict))
            db_dict[dbname_code] = act_dict
            db_dict[dbname_code].get('exchanges').append({"amount": 1,
                                                          "input": dbname_code,
                                                          "type": 'production',
                                                          "name": act.get('name')
                                                          })
    return db_dict


def create_regionalized_wood_production_activity(ei, year, scenario, temp_db_dict, new_db_name):
    db_dict = {}
    list_wood_production_activities = get_wood_production_list(ei)
    list_harvest_activities_names = get_harvest_activities_names_list(ei)
    luc_id_dict = get_luc_dict()
    print(f'---Create regionalized wood products productions activities datasets---')
    # df_land = get_df_luluc(year, scenario)
    df_land = calculate_forest_occupation_and_transformation(year, scenario)
    luluc_list_relevant = [x for x in luluc_list if x in df_land.columns]
    df_new_db_dict = pd.DataFrame.from_dict(temp_db_dict, orient='index')
    loc_list = get_lca_db_locations()
    for act in list_wood_production_activities:
        for location in list(df_land.Country.unique()):
            if location in loc_list:
                df_temp = df_land[df_land.Country == location].copy()
                region = df_temp['Region'].iloc[0]
                act_dict = {
                    "name": act.get('name'),
                    'reference product': act.get('reference product'),
                    'exchanges': [],
                    'unit': act.get('unit'),
                    'location': location
                }
                for exc in act.exchanges():
                    if exc.get('type') != 'production' and 'forest, extensive' not in exc.get('name'):
                        if exc.get('name') in list_harvest_activities_names:
                            mask = (df_new_db_dict['name'] == exc.get('name')) & (
                                    df_new_db_dict['location'] == region)
                            exc_input = df_new_db_dict[mask].index.tolist()[0]
                            exc_comment = f"{exc.get('name')}, modified by JH"
                        else:
                            exc_input = exc.get('input')
                            exc_comment = exc.get('name')
                        exc = {
                            "amount": exc.get('amount'),
                            "input": exc_input,
                            "type": exc.get('type'),
                            "comment": exc_comment,
                            "name": exc.get('name')
                        }
                        act_dict.get('exchanges').append(exc)
                for y in luluc_list_relevant:
                    exc_input = luc_id_dict[y][location]
                    if 'pulpwood' in act.get('reference product'):
                        exc_amount = df_temp.loc[df_temp.PRODUCT == 'sw', y].iloc[0]
                    elif 'sawlog' in act.get('reference product'):
                        exc_amount = df_temp.loc[df_temp.PRODUCT == 'sw', y].iloc[0]
                    elif 'hardwood' in act.get('name') and 'kilogram' == act.get('unit'):
                        exc_amount = df_temp.loc[df_temp.PRODUCT == 'logging_residue',
                                                 y].iloc[0] / get_wood_density("hardwood")
                    else:
                        exc_amount = df_temp.loc[df_temp.PRODUCT == 'logging_residue',
                                                 y].iloc[0] / get_wood_density("softwood")
                    exc = {
                        "amount": exc_amount,
                        "input": exc_input,
                        "type": 'biosphere',
                        "comment": f'{y}, modified by JH',
                        "name": y
                    }
                    act_dict.get('exchanges').append(exc)
                dbname_code = (new_db_name, activity_hash(act_dict))
                db_dict[dbname_code] = act_dict
                db_dict[dbname_code].get('exchanges').append({"amount": 1,
                                                              "input": dbname_code,
                                                              "type": 'production',
                                                              "name": act.get('name')
                                                              })
    return db_dict


def update_sawnmill_allocation(wood_type, year, scenario, region, df_ei):
    df_price = get_wood_price(year, scenario)
    df_product = df_ei[df_ei.type == 'production'].copy()
    df_product['priceXamount'] = df_product['price'] * df_product['amount']
    df_product['allocation'] = df_product['priceXamount'] / df_product['priceXamount'].sum()
    df_product['allocation_amount'] = df_product['allocation'] / df_product['amount']
    price_sawnwood = df_price.loc[(df_price.REGION == region), 'Sawnwood'].iloc[0]
    price_bark = df_price.loc[(df_price.REGION == region), 'Bark'].iloc[0]
    price_chip = df_price.loc[(df_price.REGION == region), 'WoodChips'].iloc[0]
    price_sawdust = df_price.loc[(df_price.REGION == region), 'Sawdust'].iloc[0]
    df_product.loc[df_product.name == f'sawnwood, {wood_type}, raw', 'price'] = price_sawnwood
    df_product.loc[df_product.name == f'slab and siding, {wood_type}, wet, measured as dry mass', 'price'] = price_chip
    df_product.loc[df_product.name == 'sawdust, loose, wet, measured as dry mass', 'price'] = price_sawdust
    df_product.loc[df_product.name == 'bark', 'price'] = price_bark
    df_product['price'] = df_product['price'].astype(float)
    df_product['priceXamount'] = df_product['price'] * df_product['amount']
    df_product['allocation'] = df_product['priceXamount'] / df_product['priceXamount'].sum()
    df_product['allocation_amount'] = df_product['allocation'] / df_product['amount']
    return df_product


def create_regionalized_sawnmill_activity(ei, ei_name, year, scenario, temp_db_dict, new_db_name):
    print(f'---create regionalized saw mill activities')
    db_dict = {}
    df_new_db_dict = pd.DataFrame.from_dict(temp_db_dict, orient='index')
    #df_land = get_df_luluc(year, scenario)
    df_land = calculate_forest_occupation_and_transformation(year, scenario)
    loc_list = get_lca_db_locations()
    for wood_type in ['hardwood', 'softwood']:
        print(f'------{wood_type}------')
        df_ei = get_original_ei_sawnmill_inventory(ei, wood_type)
        df_inputs = df_ei[df_ei.type != 'production'].copy()
        df_regionalized_act_code = get_regionalized_act_code(ei)
        density = get_wood_density(wood_type)
        for location in list(df_land.Country.unique()):
            if location in loc_list:
                region = df_land.loc[df_land.Country == location, 'Region'].iloc[0]
                df_product = update_sawnmill_allocation(wood_type, year, scenario, region, df_ei)
                for x in df_product.index:
                    allocation = df_product.loc[x, 'allocation_amount']
                    product = df_product.loc[x, 'name']
                    if wood_type not in product:
                        product += f', {wood_type}'
                    act_dict = {
                        "name": product,
                        'exchanges': [],
                        'unit': 'kilogram',
                        'location': location,
                        'reference product': product
                    }
                    for y in df_inputs.index:
                        input_name = df_inputs.loc[y, 'name']
                        input_type = df_inputs.loc[y, 'type']
                        input_amount = df_inputs.loc[y, 'amount'] * allocation / density  # kg
                        if input_name in regionalized_act:
                            input_input = (ei_name, df_regionalized_act_code.loc[region, input_name])
                        elif 'sawlog and veneer log' in input_name:
                            mask = (df_new_db_dict['reference product'] == input_name[11:]) & (
                                        df_new_db_dict['location'] == location)
                            input_input = df_new_db_dict[mask].index.tolist()[0]
                        else:
                            input_input = df_inputs.loc[y, 'input']

                        exc = {
                            "amount": input_amount,
                            "input": input_input,
                            "type": input_type,
                            "name": input_name,
                            "comment": f'{input_name}, modified by JH'
                        }
                        act_dict.get('exchanges').append(exc)
                    dbname_code = (new_db_name, activity_hash(act_dict))
                    db_dict[dbname_code] = act_dict
                    db_dict[dbname_code].get('exchanges').append({"amount": 1,
                                                                  "input": dbname_code,
                                                                  "type": 'production',
                                                                  "name": product
                                                                  })
    return db_dict


def create_forest_lci(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}_regionalized'
    new_db_name = f'{ei_name}_update'
    '''
    try:
        del bd.databases[new_db_name]
    except KeyError:
        pass
    '''
    if new_db_name in list(bd.databases):
        print(f'{new_db_name} already exist.')
    else:
        print(f'Setting up regionalized forest LCI database: "{new_db_name}".')
        ei = bd.Database(ei_name)
        new_db_dict = {}
        new_db_dict.update(create_regionalized_harvest_activitiy(ei, ei_name, new_db_name))
        temp_db_dict = new_db_dict.copy()
        new_db_dict.update(create_regionalized_wood_production_activity(ei, year, scenario, temp_db_dict, new_db_name))
        temp_db_dict = new_db_dict.copy()
        new_db_dict.update(create_regionalized_sawnmill_activity(ei, ei_name, year, scenario,
                                                                 temp_db_dict, new_db_name))
        ei_update = bd.Database(new_db_name)
        ei_update.write(new_db_dict)
