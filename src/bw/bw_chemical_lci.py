import bw2data as bd
from bw2io.utils import activity_hash
import pandas as pd
from copy import deepcopy

from src.bw.bw_lcia import lcia_all, lcia_electricity


bio_dict = {'water_resource': ('biosphere water regionalized', '3406fa5adc8115e4b190cf2c491616c5'),
            'water_emission': ('biosphere water regionalized', '28b32d9f1678ca6c24cfc72cca3fdca0'),
            'CO2 (fossil)': ('biosphere3', '349b29d1-3e58-4c66-98b9-9d1a076efd2e'),
            'CO2 (biogenic)': ('biosphere3', '349b29d1-3e58-4c66-98b9-9d1a076efd2e'),
            'Hcl_air': ('biosphere3', 'c9a8073a-8a19-5b9b-a120-7d549563b67b'),
            'Hcl_water': ('biosphere3', '7dd051f1-c653-44d9-90e4-828f144253c3'),
            'Propionaldehyde': ('biosphere3', '2f2450fa-6720-4b59-9876-10a9ee843958')}


def find_biomass_least_and_most_impact(year, scenario, price='normal'):
    df = lcia_all(year, scenario, price)
    df['check'] = abs(df['GHG'] - df['GHG'].quantile(0.95))
    df_min = df[df['check'] == df['check'].min()]
    biomass = df_min['Product'].iloc[0]
    biomass_db_list = [db for db in list(bd.databases) if 'update' in db]
    act_list_min = []
    for db_name in biomass_db_list:
        db = bd.Database(db_name)
        act_min = [act for act in db if df_min['Product'].iloc[0] in act.get('name') and
        act.get('location') == df_min['Country'].iloc[0]]
    return df


def read_chemical_lci_inputs():
    df = pd.read_excel(r'data/raw_data/Inventory_biomass_fractionation.xlsx', engine='openpyxl', sheet_name='Inputs')
    return df


def read_chemical_lci_emissions():
    df = pd.read_excel(r'data/raw_data/Inventory_biomass_fractionation.xlsx', engine='openpyxl', sheet_name='Emissions')
    return df


def read_chemical_lci_utility():
    df = pd.read_excel(r'data/raw_data/Inventory_biomass_fractionation.xlsx', engine='openpyxl', sheet_name='Energy')
    return df


def create_cooling_water_activity(new_db_name, electricity_code):
    db_dict = {}
    exc_list = [
        {"amount": 0.00166,
         "input": electricity_code,
         "type": 'technosphere',
         "comment": 'electricity, modified by JH',
         "name": f"market group for electricity, medium voltage"
         },
        {"amount": 0.00061127,
         "input": bio_dict['water_resource'],
         "type": 'biosphere',
         "comment": 'water resource, modified by JH',
         "name": f"water"
         },
        {"amount": 0.000204,
         "input": bio_dict['water_emission'],
         "type": 'biosphere',
         "comment": 'water emitted to water, modified by JH',
         "name": f"water"
         },
    ]
    act_dict = {
        "name": f"cooling water, {electricity_code}",
        'reference product': f"cooling water, {electricity_code}",
        'exchanges': exc_list,
        'unit': 'MJ',
        'production amount': 1,
        'location': 'WEU'
    }
    dbname_code = (new_db_name, activity_hash(act_dict))
    db_dict[dbname_code] = act_dict
    product_dict = {"amount": 1,
                    "input": dbname_code,
                    "type": 'production',
                    "name": "cooling water, {WEU}"
                    }
    db_dict[dbname_code].get('exchanges').append(product_dict)
    return db_dict, dbname_code


def create_chemical_pretreatment_activitiy_same_for_all(ei, wood_db, new_db_name, electricity_code):
    df_inputs = read_chemical_lci_inputs()
    df_emissions = read_chemical_lci_emissions()
    df_utility = read_chemical_lci_utility()
    sawdust_code = [act for act in wood_db if 'sawdust, loose, wet, measured as dry mass, hardwood' == act.get('name')
                    and 'CH' == act.get('location')][0].key
    exc_list = [{"amount": 1,
                 "input": sawdust_code,
                 "type": 'technosphere',
                 "comment": 'biomass input, 1kg',
                 "name": f"water"
                 }]
    for x in df_inputs.index:
        chemical_name = df_inputs.loc[x, 'Chemical']
        location = df_inputs.loc[x, 'Location']
        search_name = df_inputs.loc[x, 'Search']
        chemical_amount = df_inputs.loc[x, 'Value']
        chemical_unit = df_inputs.loc[x, 'Unit']
        chemical_code = [act for act in ei if search_name in act.get('name') and
                         location == act.get('location') and
                         chemical_unit == act.get('unit')][0].key
        exc_list.append({"amount": chemical_amount,
                         "input": chemical_code,
                         "type": 'technosphere',
                         "comment": 'simulation results',
                         "name": chemical_name
                         })
    for x in df_emissions.index:
        emission = df_emissions.loc[x, 'Inputs']
        if emission == emission:
            emission_name = df_emissions.loc[x, 'Chemical']
            emission_code = bio_dict[emission_name]
            emission_amount = df_emissions.loc[x, 'Value']
            exc_list.append({"amount": emission_amount,
                             "input": emission_code,
                             "type": 'biosphere',
                             "comment": 'simulation results',
                             "name": emission_name
                             })
    cooling_water_amount = df_utility.loc[df_utility.Energy == 'Cooling', 'Value'].iloc[0]
    cooling_water_code = create_cooling_water_activity(new_db_name, electricity_code)[1]
    electricity_amount = df_utility.loc[df_utility.Energy == 'Electricity', 'Value'].iloc[0]
    exc_list.append({"amount": cooling_water_amount,
                     "input": cooling_water_code,
                     "type": 'technosphere',
                     "comment": 'simulation results',
                     "name": 'cooling water'
                     })
    exc_list.append({"amount": electricity_amount,
                     "input": electricity_code,
                     "type": 'technosphere',
                     "comment": 'simulation results',
                     "name": f"market group for electricity, medium voltage"
                     })
    act = {"name": f"birch wood fractionation, {electricity_code}",
           'reference product': f"birch wood fractionation, {electricity_code}",
           'exchanges': exc_list,
           'unit': 'kilogram',
           'production amount': 1,
           'location': 'CH'}
    return act


def create_chemical_pretreatment_activitiy(ei, wood_db, new_db_name, electricity_code):
    df_emissions = read_chemical_lci_emissions()
    co2_amount = df_emissions.loc[df_emissions.Chemical == 'CO2 (biogenic)', 'Value'].iloc[0] * 0.43
    co2_code = bio_dict['CO2 (biogenic)']
    co2_dict = {"amount": co2_amount,
                "input": co2_code,
                "type": 'biosphere',
                "comment": 'simulation results, biogenic carbon, 100 years rotation period, impact = 0.43',
                "name": f"CO2 (biogenic)"
                }
    act = create_chemical_pretreatment_activitiy_same_for_all(ei, wood_db, new_db_name, electricity_code)
    db_dict = {}
    act_dict1 = deepcopy(act)
    act_dict1['name'] = f"birch wood fractionation, no biogenic carbon impacts, {electricity_code}"
    dbname_code1 = (new_db_name, activity_hash(act_dict1))
    db_dict[dbname_code1] = act_dict1
    product_dict1 = {"amount": 1,
                     "input": dbname_code1,
                     "type": 'production',
                     "name": f"birch wood fractionation, no biogenic carbon impacts, {electricity_code}"
                    }
    db_dict[dbname_code1].get('exchanges').append(product_dict1)

    act_dict2 = deepcopy(act)
    act_dict2['name'] = f"birch wood fractionation, with biogenic carbon impacts, {electricity_code}"
    act_dict2.get('exchanges').append(co2_dict)
    dbname_code2 = (new_db_name, activity_hash(act_dict2))
    db_dict[dbname_code2] = act_dict2
    product_dict2 = {"amount": 1,
                     "input": dbname_code2,
                     "type": 'production',
                     "name": f"birch wood fractionation, with biogenic carbon impacts, {electricity_code}"
                     }
    db_dict[dbname_code2].get('exchanges').append(product_dict2)
    return db_dict


def create_chemical_lci(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}_regionalized'
    wood_db_name = f'{ei_name}_update'
    ei = bd.Database(ei_name)
    wood_db = bd.Database(wood_db_name)
    new_db_name = f'chemical'
    # del bd.databases[new_db_name]
    if new_db_name in list(bd.databases):
        print(f'{new_db_name} already exist.')
    else:
        new_db_dict = {}
        for electricity_code in lcia_electricity(year, scenario):
            new_db_dict.update(create_cooling_water_activity(new_db_name, electricity_code)[0])
            new_db_dict.update(create_chemical_pretreatment_activitiy(ei, wood_db, new_db_name, electricity_code))
        chemical_update = bd.Database(new_db_name)
        chemical_update.write(new_db_dict)
