import bw2data as bd
from bw2io.utils import activity_hash
import pandas as pd
from copy import deepcopy
import os
import bw2io as bi

from src.other.name_match import get_lca_db_locations
from src.data.lcia_regionalized_cfs import biodiversity_cf_match_locations, calculate_area_weighted_regional_water_cfs

project_name = "biomass_basic"
bd.projects.set_current(project_name)
bio = bd.Database("biosphere3")


# start with biomass_base project, with biosphere3 and ecoinvent3.8
def bw_generate_new_biosphere_data_water(bio_act_list, new_bio_name):
    loc_list = get_lca_db_locations()
    biosphere_data = {}
    for bio_act in bio_act_list:
        for loc in loc_list:
            # print(bio_act, loc)
            bio_act_data = deepcopy(bio_act.as_dict())
            bio_act_data['location'] = loc  # Add location
            bio_act_data['database'] = new_bio_name
            bio_act_code = activity_hash(bio_act_data)
            bio_act_data['code'] = bio_act_code
            dbname_code = (new_bio_name, bio_act_code)
            biosphere_data[dbname_code] = bio_act_data
            bio_act_data_irri = deepcopy(bio_act.as_dict())
            bio_act_data_irri['location'] = loc  # Add location
            bio_act_data_irri['database'] = new_bio_name
            bio_act_data_irri['name'] = f'{bio_act.get("name")}, irrigation'
            bio_act_code_irri = activity_hash(bio_act_data_irri)
            bio_act_data_irri['code'] = bio_act_code_irri
            dbname_code_irri = (new_bio_name, bio_act_code_irri)
            biosphere_data[dbname_code_irri] = bio_act_data_irri
    return biosphere_data


def bw_generate_new_biosphere_data_luluc(bio_act_list, new_bio_name):
    loc_list = get_lca_db_locations()
    biosphere_data = {}
    for bio_act in bio_act_list:
        for loc in loc_list:
            # print(bio_act, loc)
            bio_act_data = deepcopy(bio_act.as_dict())
            bio_act_data['location'] = loc  # Add location
            bio_act_data['database'] = new_bio_name
            bio_act_code = activity_hash(bio_act_data)
            bio_act_data['code'] = bio_act_code
            dbname_code = (new_bio_name, bio_act_code)
            biosphere_data[dbname_code] = bio_act_data
    bio_act_additional_list = [x for x in bio if 'annual crop, irrigated, intensive' in x.get('name')]
    intensity_list = ['intensive', 'extensive', 'minimal']
    loc_list = get_lca_db_locations()
    for bio_act in bio_act_additional_list:
        for intensity in intensity_list:
            bio_act_name = f'{bio_act.get("name").split(", ")[0]}, {bio_act.get("name").split(", ")[1]}, {intensity}'
            for loc in loc_list:
                bio_act_data = deepcopy(bio_act.as_dict())
                bio_act_data['location'] = loc  # Add location
                bio_act_data['name'] = bio_act_name
                bio_act_data['database'] = new_bio_name
                bio_act_code = activity_hash(bio_act_data)
                bio_act_data['code'] = bio_act_code
                dbname_code = (new_bio_name, bio_act_code)
                biosphere_data[dbname_code] = bio_act_data
    return biosphere_data


def bw_add_lcia_method_biodiversity():
    flows_occ_list = []
    flows_tra_list = []
    if os.path.exists(r'data/interim/cf_biodiversity_processed_new.csv'):
        df = pd.read_csv(r'data/interim/cf_biodiversity_processed_new.csv', index_col=0)
        df['Location'] = df['Location'].fillna('NA')
    else:
        df = biodiversity_cf_match_locations()
    new_bio_db = bd.Database('biosphere luluc regionalized')
    df_loc = pd.read_csv(r'data/external/Scherer_land_use_match.csv')
    df_check = pd.DataFrame()
    for flow in new_bio_db:
        loc = flow.get('location')
        flow_name = flow.get('name').replace(',', '')
        index_nr = df_loc.where(df_loc == flow_name).dropna(how='all').index
        if index_nr.shape[0] > 0:
            lu_type = df_loc.loc[index_nr, 'Land use type'].values[0]
            lu_intensity = df_loc.loc[index_nr, 'Land use intensity'].values[0]
            habitat = f'{lu_type}_{lu_intensity}'
            try:
                if 'Occupation' in flow_name:
                    cf = df.loc[(df.Location == loc) & (df.habitat == habitat), 'CF_occ_avg_glo'].iloc[0]
                    flows_occ_list.append([flow.key, cf])
                elif 'Transformation from' in flow_name:
                    cf = -df.loc[(df.Location == loc) & (df.habitat == habitat), 'CF_tra_avg_glo'].iloc[0]
                    flows_tra_list.append([flow.key, cf])
                elif 'Transformation to' in flow_name:
                    cf = df.loc[(df.Location == loc) & (df.habitat == habitat), 'CF_tra_avg_glo'].iloc[0]
                    flows_tra_list.append([flow.key, cf])
            except:
                df_temp = pd.DataFrame([[loc, habitat]], columns=['location', 'habitat'])
                df_check = pd.concat([df_check, df_temp], ignore_index=True)
    occ_tuple = ('Biodiversity regionalized', 'Occupation')
    occ_method = bd.Method(occ_tuple)
    occ_data = {'unit': 'PDF*year/m2a',
                'num_cfs': len(flows_occ_list),
                'description': 'method based on new GLAM Initiative'}
    occ_method.validate(flows_occ_list)
    occ_method.register(**occ_data)
    occ_method.write(flows_occ_list)
    tra_tuple = ('Biodiversity regionalized', 'Transformation')
    tra_method = bd.Method(tra_tuple)
    tra_data = {'unit': 'PDF*year/m2',
                'num_cfs': len(flows_tra_list),
                'description': 'method based on new GLAM Initiative'}
    tra_method.validate(flows_tra_list)
    tra_method.register(**tra_data)
    tra_method.write(flows_tra_list)


def bw_add_lcia_method_aware():
    flows_list = []
    if os.path.exists(r'data/interim/cf_aware_processed.csv'):
        df = pd.read_csv(r'data/interim/cf_aware_processed.csv', index_col=0)
        df['Location'] = df['Location'].fillna('NA')
    else:
        df = calculate_area_weighted_regional_water_cfs()
    new_bio_db = bd.Database('biosphere water regionalized')
    for flow in new_bio_db:
        loc = flow.get('location')
        if 'irrigation' in flow.get('name'):
            cf = df.loc[df.Location == loc, 'Agg_CF_irri'].iloc[0]
        else:
            cf = df.loc[df.Location == loc, 'Agg_CF_non_irri'].iloc[0]
        if 'water' in flow.get('categories'):
            cf *= -1
        flows_list.append([flow.key, cf])
    aware_tuple = ('AWARE regionalized', 'Annual')
    aware_method = bd.Method(aware_tuple)
    aware_data = {'unit': 'm3 world',
                  'num_cfs': len(flows_list),
                  'description': 'AWARE'}
    aware_method.validate(flows_list)
    aware_method.register(**aware_data)
    aware_method.write(flows_list)


def bw_add_lcia_method_ipcc_ar6():
    df = pd.read_excel(r'data/raw_data/ghg_cfs_ipcc_ar6.xlsx', engine='openpyxl', sheet_name='CFs')
    for cf in ['GWP_100a', 'GTP_100a']:
        for cf_type in ['all', 'Biogenic', 'Fossil', 'LUC']:
            flows_list = []
            if cf_type != 'all':
                df1 = df.loc[df.Type == cf_type]
            else:
                df1 = df.copy()
            for flow in bio:
                if flow['name'] in list(df1.Gas.unique()):
                    cf_val = df1.loc[df1.Gas == flow['name'], cf].iloc[0]
                    flows_list.append([flow.key, cf_val])
            ipcc_tuple = ('IPCC_AR6', cf, cf_type)
            ipcc_method = bd.Method(ipcc_tuple)
            ipcc_data = {'unit': 'CO2-eq',
                         'num_cfs': len(flows_list),
                         'description': 'ipcc ar6 cf'}
            ipcc_method.validate(flows_list)
            ipcc_method.register(**ipcc_data)
            ipcc_method.write(flows_list)


def bw_set_up():
    # regionalized biosphere for land occupation and transformation
    luluc_name = "biosphere luluc regionalized"
    water_name = "biosphere water regionalized"
    # del bd.databases[water_name]
    # del bd.databases[luluc_name]
    if luluc_name in bd.databases:
        print(f'Regionalized land use and land use change biosphere database: "{luluc_name}" already exist. No set up '
              f'required.')
    else:
        print(f'Setting up regionalized land use and land use change biosphere database: "{luluc_name}".')
        luluc_list = [act for act in bio if ("occupation" in act['name'].lower()
                                             or 'transformation' in act['name'].lower())
                      and 'non-use' not in act['name']
                      and 'obsolete' not in act['name']]
        biosphere_luluc_data = bw_generate_new_biosphere_data_luluc(luluc_list, luluc_name)
        new_bio_db = bd.Database(luluc_name)
        new_bio_db.write(biosphere_luluc_data)
    if water_name in bd.databases:
        print(f'Regionalized water biosphere database: "{water_name}" already exist. No set up required.')
    else:
        print(f'Setting up regionalized water biosphere database: "{water_name}".')
        water_use_list = [act for act in bio if "Water" in act['name']
                          and 'natural resource' in act['categories']
                          and 'air' not in act['name']
                          and 'ocean' not in act['name']
                          and 'ocean' not in act.get('categories')]
        water_emission_list = [act for act in bio if "Water" in act['name']
                               and 'water' in act['categories']
                               and 'ocean' not in act.get('categories')]
        water_list = water_use_list + water_emission_list
        biosphere_water_data = bw_generate_new_biosphere_data_water(water_list, water_name)
        new_bio_db = bd.Database(water_name)
        new_bio_db.write(biosphere_water_data)
    if ('Biodiversity regionalized', 'Occupation') in list(bd.methods):
        print('Regionalized biodiversity impact assessment methods already set up.')
    else:
        print('Setting up regionalized biodiversity impact assessment methods')
        bw_add_lcia_method_biodiversity()
    if ('AWARE regionalized', 'Annual') in list(bd.methods):
        print('Regionalized AWARE impact assessment methods already set up.')
    else:
        print('Setting up regionalized AWARE impact assessment methods')
        bw_add_lcia_method_aware()
    if ('IPCC_AR6', 'GWP_100a', 'all') in list(bd.methods):
        print('IPCC AR6 impact assessment methods already set up.')
    else:
        print('Setting up IPCC AR6 impact assessment methods')
        bw_add_lcia_method_ipcc_ar6()


def delete_projects():
    delete_list = [pj for pj in bd.databases if 'ele' in pj]
    for pj in delete_list:
        print(f'deleting {pj}')
        del bd.databases[pj]

