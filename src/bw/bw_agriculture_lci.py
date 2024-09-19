import re
import pandas as pd
import bw2data as bd
from bw2io.utils import activity_hash

from src.other.name_match import crop_list, luluc_list, get_country_match_df, get_luc_dict
from src.data.agriculture_lci import crop_lci_final_output

# pattern codes
NPK_pattern = r"\(NPK (.*?)\)"
location_pattern = r"\{(.*?)\}"

emission_id_dict = {'CO2': ('biosphere3', '349b29d1-3e58-4c66-98b9-9d1a076efd2e'),
                    'N2O direct': ('biosphere3', '20185046-64bb-4c09-a8e7-e8a9e144ca98'),
                    'N2O indirect': ('biosphere3', '20185046-64bb-4c09-a8e7-e8a9e144ca98'),
                    'N2O direct CR': ('biosphere3', '20185046-64bb-4c09-a8e7-e8a9e144ca98'),
                    'N2O indirect CR': ('biosphere3', '20185046-64bb-4c09-a8e7-e8a9e144ca98'),
                    'NH3': ('biosphere3', '87883a4e-1e3e-4c9d-90c0-f1bea36f8014'),
                    'NO': ('biosphere3', 'c1b91234-6f24-417b-8309-46111d09c457'),
                    'P emission': ('biosphere3', '2d4b8ec1-8d53-4e62-8a11-ebc45909b02e'),
                    'NO3': ('biosphere3', '5189de76-6bbb-44ba-8c42-5714f1b4371f'),
                    'NO3 CR': ('biosphere3', '5189de76-6bbb-44ba-8c42-5714f1b4371f'),
                    'CO2 luc': ('biosphere3', 'e4e9febc-07c1-403d-8d3a-6707bb4d96e6')}


def get_agri_product_list(db):
    product_list = []
    for x in crop_list:
        crop_name = x + ", at farm"
        temp_list = [act for act in db if crop_name in act['name']]
        product_list += temp_list
    return product_list


def read_crop_lci_csv(year, scenario, product_list):
    '''
    if os.path.exists(r'data/interim/crop_lci.csv'):
        df = pd.read_csv(r'data/interim/crop_lci.csv', index_col=0)
        df['Country'] = df['Country'].fillna('NA')
    else:
        from src.data.agriculture_lci import add_land_use_intensity
        df = add_land_use_intensity()
    '''
    # new
    df = crop_lci_final_output()
    df_scenario = df.loc[(df.YEAR == year) & (df.SCENARIO == scenario)].copy()
    df_scenario['In_Afdb'] = 'No'
    for act in product_list:
        match = re.findall(pattern=location_pattern, string=act.get('name'))
        location = match[0]
        crop = act.get('name').split(',')[0]
        df_scenario.loc[(df_scenario.Crop == crop) & (df_scenario.Country == location), 'In_Afdb'] = 'Yes'
    df_country = get_country_match_df()
    df_scenario['AFDB_region'] = df_scenario['Country'].map(df_country.set_index('ISO2')['AFDB_region'])
    return df_scenario


def get_seed_amount(product_list):
    seed_amount_dict = {}
    for act in product_list:
        if 'CN' in act.get('name'):
            crop = act.get('name').split(',')[0]
            for exc in act.exchanges():
                if 'start material' in exc.get('name'):
                    seed_amount_dict[crop] = exc.get('amount')
    return seed_amount_dict


def get_water_dict():
    bio_water = bd.Database("biosphere water regionalized")
    water_dict = {}
    for act in bio_water:
        if act.get('name') == 'Water, unspecified natural origin, irrigation':
            act_id = (act.get('database'), act.get('code'))
            water_dict[act.get('location')] = act_id
    return water_dict


def get_fertilizer_input(df_lci, afdb):
    fer_name_list = [fer.split(',')[0] for fer in df_lci.columns if 'NPK' in fer]
    fer_act_list = [act for act in afdb if act['name'].split(',')[0] in fer_name_list]
    afdb_region_list = list(df_lci['AFDB_region'].unique())
    afdb_region_list = [x for x in afdb_region_list if isinstance(x, str)]
    df_fer_id = pd.DataFrame(columns=fer_name_list, index=afdb_region_list)
    for act in fer_act_list:
        fer_name = act['name'].split(',')[0]
        match = re.findall(pattern=location_pattern, string=act.get('name'))
        location = match[0]
        act_id = (act.get('database'), act.get('code'))
        df_fer_id.loc[location, fer_name] = act_id
    return df_fer_id


def exc_direct_copy(exc, crop):
    exc_list = []
    if not (
            'start material' in exc.get('name') or
            'Occupation' in exc.get('name') or
            'Transformation' in exc.get('name') or
            'NPK' in exc.get('name') or
            'Water, unspecified natural origin' in exc.get('name') or
            f'{crop}, at farm' in exc.get('name') or
            ('biosphere' in exc.get('type') and
             ('Fertilizer' in exc.get('comment') or
              'Land use change' in exc.get('comment') or
              'Crop residues' in exc.get('comment')))
    ):
        exc_dict = {
            "amount": exc.get('amount'),
            "input": exc.get('input'),
            "type": exc.get('type'),
            "comment": exc.get('comment'),
            "name": exc.get('name')
        }
        exc_list.append(exc_dict)
    return exc_list


def exc_update(df, df_fer_id, water_id_dict, luc_id_dict):
    exc_list = []
    location = df['Country'].iloc[0]
    region = df['AFDB_region'].iloc[0]
    for y in df.columns:
        if y.split(',')[0] in list(df_fer_id.columns):
            fer_name = y.split(',')[0]
            fer_act_id = df_fer_id.loc[region, fer_name]
            if not isinstance(fer_act_id, tuple):
                fer_act_id = df_fer_id.loc['RER', fer_name]
            exc_amount = df[y].iloc[0]
            exc_dict = {
                "amount": exc_amount,
                "input": fer_act_id,
                "type": 'technosphere',
                "name": bd.get_activity(fer_act_id).get('name'),
                "comment": f'{fer_name}, modified by JH'
            }
            exc_list.append(exc_dict)
        elif y in emission_id_dict.keys():
            exc_amount = df[y].iloc[0]
            exc_dict = {
                "amount": exc_amount,
                "input": emission_id_dict.get(y),
                "type": 'biosphere',
                "name": bd.get_activity(emission_id_dict.get(y)).get('name'),
                "comment": f'Emission {y}, modified by JH'
            }
            exc_list.append(exc_dict)
        elif y == 'Blue_water_m3_per_ha':
            exc_amount = df[y].iloc[0]
            exc_input = water_id_dict[location]
            exc_dict = {
                "amount": exc_amount,
                "input": exc_input,
                "type": 'biosphere',
                "name": bd.get_activity(exc_input).get('name'),
                "comment": f'blue water consumption, modified by JH'
            }
            exc_list.append(exc_dict)
        elif y in luluc_list:
            exc_amount = df[y].iloc[0]
            exc_input = luc_id_dict[y][location]
            exc_dict = {
                "amount": exc_amount,
                "input": exc_input,
                "type": 'biosphere',
                "name": bd.get_activity(exc_input).get('name'),
                "comment": f'{y}, modified by JH'
            }
            exc_list.append(exc_dict)
    return exc_list


def update_unchanged_parts(product_list, new_db_name):
    print(f'------extracting relevant datasets with parts not to be changed------')
    db_dict = {}
    for act in product_list:
        match = re.findall(pattern=location_pattern, string=act.get('name'))
        location = match[0]
        crop = act.get('name').split(',')[0]
        act_dict = {
            "name": f"{crop}, unchanged parts, {{{location}}}",
            'reference product': f"{crop}, unchanged parts",
            'exchanges': [],
            'unit': 'ha',
            'production amount': 1,
            'location': location
        }
        for exc in act.exchanges():
            exc_list = exc_direct_copy(exc, crop)
            if len(exc_list) > 0:
                act_dict.get("exchanges").append(exc_list[0])
        dbname_code = (new_db_name, activity_hash(act_dict))
        db_dict[dbname_code] = act_dict
    return db_dict


def create_glo_unchanged_parts(new_db_name, df_lci_in_afdb, temp_dict):
    print(f'------create global average of unchanged parts for each crop------')
    df_new_db_dict = pd.DataFrame.from_dict(temp_dict, orient='index')
    new_db_dict = {}
    for crop in list(df_lci_in_afdb.Crop.unique()):
        act_dict = {
            "name": f"{crop}, unchanged parts, {{GLO}}",
            'reference product': f"{crop}, unchanged parts",
            'exchanges': [],
            'unit': 'ha',
            'production amount': 1,
            'location': 'GLO'
        }
        for country in list(df_lci_in_afdb[df_lci_in_afdb.Crop == crop].Country.unique()):
            amount = df_lci_in_afdb.loc[(df_lci_in_afdb.Crop == crop) &
                                        (df_lci_in_afdb.Country == country), 'harvest_area'].iloc[0] / \
                     df_lci_in_afdb.loc[(df_lci_in_afdb.Crop == crop), 'harvest_area'].sum()
            mask = (df_new_db_dict['reference product'] == f"{crop}, unchanged parts") & (
                    df_new_db_dict['location'] == country)
            input_id = df_new_db_dict[mask].index.tolist()[0]
            exc_dict = {
                "amount": amount,
                "input": input_id,
                "type": 'technosphere',
                "name": f"{crop}, unchanged parts, {{{country}}}",
                "comment": f"share of country {country}"
            }
            act_dict.get('exchanges').append(exc_dict)
        dbname_code = (new_db_name, activity_hash(act_dict))
        new_db_dict[dbname_code] = act_dict
        new_db_dict[dbname_code].get('exchanges').append({"amount": 1,
                                                          "input": dbname_code,
                                                          "type": 'production',
                                                          "name": f"{crop}, unchanged parts, {{GLO}}"
                                                          })
    return new_db_dict


def update_seed(product_list, new_db_name, df_lci, df_fer_id):
    print(f'------update existing start material production------')
    db_dict = {}
    luc_id_dict = get_luc_dict()
    water_id_dict = get_water_dict()
    for act in product_list:
        match = re.findall(pattern=location_pattern, string=act.get('name'))
        location = match[0]
        crop = act.get('name').split(',')[0]
        df = df_lci.loc[(df_lci.Crop == crop) & (df_lci.Country == location)].copy()
        if df.shape[0] == 1:
            production_amount = df['Yield_kg_per_ha'].iloc[0]
            if crop == 'Maize':
                production_amount *= 0.33
            elif crop == 'Soybeans':
                production_amount *= 0.57
            act_dict = {
                "name": f"{crop}, start material, at seed production, {{{location}}}",
                'reference product': f"{crop}, start material, at seed production",
                'exchanges': [],
                'unit': 'kg',
                'production amount': production_amount,
                'location': location
            }
            for exc in act.exchanges():
                exc_list = exc_direct_copy(exc, crop)
                if len(exc_list) > 0:
                    act_dict.get("exchanges").append(exc_list[0])
            exc_list_new = exc_update(df, df_fer_id, water_id_dict, luc_id_dict)
            for exc_dict in exc_list_new:
                act_dict.get("exchanges").append(exc_dict)
            dbname_code1 = (new_db_name, activity_hash(act_dict))
            db_dict[dbname_code1] = act_dict
            db_dict[dbname_code1].get('exchanges').append({
                "amount": production_amount,
                "input": dbname_code1,
                "type": 'production',
                "name": f"{crop}, start material, at seed production, {{{location}}}"
            })
    return db_dict


def create_new_seed(new_db_name, df_lci_not_in_afdb, new_db_dict, df_fer_id):
    print(f'------create new start material production------')
    luc_id_dict = get_luc_dict()
    water_id_dict = get_water_dict()
    df_new_db_dict = pd.DataFrame.from_dict(new_db_dict, orient='index')
    db_dict = {}
    for x in df_lci_not_in_afdb.index:
        df = df_lci_not_in_afdb.loc[[x], :].copy()
        crop = df['Crop'].iloc[0]
        location = df['Country'].iloc[0]
        production_amount = df['Yield_kg_per_ha'].iloc[0]
        if crop == 'Maize':
            production_amount *= 0.33
        elif crop == 'Soybeans':
            production_amount *= 0.57
        mask = (df_new_db_dict['reference product'] == f"{crop}, unchanged parts") & \
               (df_new_db_dict['location'] == 'GLO')
        input_id = df_new_db_dict[mask].index.tolist()[0]
        exc_dict_unchanged = {
            "amount": 1,
            "input": input_id,
            "type": 'technosphere',
            "comment": 'modified by JH',
            "name": f"{crop}, unchanged parts, {{GLO}}"
        }
        act_dict = {
            "name": f"{crop}, start material, at seed production, {{{location}}}",
            'reference product': f"{crop}, start material, at seed production",
            'exchanges': [exc_dict_unchanged],
            'unit': 'kg',
            'production amount': production_amount,
            'location': location
        }
        exc_list_new = exc_update(df, df_fer_id, water_id_dict, luc_id_dict)
        for exc_dict in exc_list_new:
            act_dict.get("exchanges").append(exc_dict)
        dbname_code = (new_db_name, activity_hash(act_dict))
        db_dict[dbname_code] = act_dict
        db_dict[dbname_code].get('exchanges').append({"amount": production_amount,
                                                      "input": dbname_code,
                                                      "type": 'production',
                                                      "name": f"{crop}, start material, at seed production, "
                                                              f"{{{location}}}"
                                                      })
    return db_dict


def update_crop(product_list, new_db_name, df_lci, new_db_dict, df_fer_id):
    print(f'------update existing crop production------')
    db_dict = {}
    luc_id_dict = get_luc_dict()
    water_id_dict = get_water_dict()
    df_new_db_dict = pd.DataFrame.from_dict(new_db_dict, orient='index')
    seed_amount_dict = get_seed_amount(product_list)
    for act in product_list:
        match = re.findall(pattern=location_pattern, string=act.get('name'))
        location = match[0]
        crop = act.get('name').split(',')[0]
        df = df_lci.loc[(df_lci.Crop == crop) & (df_lci.Country == location)].copy()
        if df.shape[0] == 1:
            mask = (df_new_db_dict['reference product'] == f"{crop}, start material, at seed production") & (
                    df_new_db_dict['location'] == location)
            input_id = df_new_db_dict[mask].index.tolist()[0]
            exc_dict_seed = {
                "amount": seed_amount_dict[crop],
                "input": input_id,
                "type": 'technosphere',
                "comment": 'seed, updated by JH',
                "name": f"{crop}, start material, at seed production, {{{location}}}"
            }
            act_dict = {
                "name": f"{crop}, {{{location}}}",
                'reference product': f"{crop}",
                'exchanges': [exc_dict_seed],
                'unit': 'ha',
                'production amount': 1,
                'location': location
            }
            for exc in act.exchanges():
                exc_list = exc_direct_copy(exc, crop)
                if len(exc_list) > 0:
                    act_dict.get("exchanges").append(exc_list[0])
            exc_list_new = exc_update(df, df_fer_id, water_id_dict, luc_id_dict)
            for exc_dict in exc_list_new:
                act_dict.get("exchanges").append(exc_dict)
            dbname_code1 = (new_db_name, activity_hash(act_dict))
            db_dict[dbname_code1] = act_dict
            db_dict[dbname_code1].get('exchanges').append({"amount": 1, "input": dbname_code1,
                                                           "type": 'production', "name": f"{crop}, {{{location}}}"})
    return db_dict


def create_new_crop(product_list, new_db_name, df_lci_not_in_afdb, new_db_dict, df_fer_id):
    print(f'------create new crop production------')
    luc_id_dict = get_luc_dict()
    water_id_dict = get_water_dict()
    df_new_db_dict = pd.DataFrame.from_dict(new_db_dict, orient='index')
    db_dict = {}
    for x in df_lci_not_in_afdb.index:
        df = df_lci_not_in_afdb.loc[[x], :].copy()
        crop = df['Crop'].iloc[0]
        location = df['Country'].iloc[0]
        seed_amount_dict = get_seed_amount(product_list)
        mask = (df_new_db_dict['reference product'] == f"{crop}, start material, at seed production") & (
                df_new_db_dict['location'] == location)
        input_id = df_new_db_dict[mask].index.tolist()[0]
        exc_dict_seed = {
            "amount": seed_amount_dict[crop],
            "input": input_id,
            "type": 'technosphere',
            "comment": 'seed, updated by JH',
            "name": f"{crop}, start material, at seed production, {{{location}}}"
        }
        mask = (df_new_db_dict['reference product'] == f"{crop}, unchanged parts") & \
               (df_new_db_dict['location'] == 'GLO')
        input_id = df_new_db_dict[mask].index.tolist()[0]
        exc_dict_unchanged = {
            "amount": 1,
            "input": input_id,
            "type": 'technosphere',
            "comment": 'unchanged parts, modified by JH',
            "name": f"{crop}, unchanged parts, {{GLO}}"
        }
        act_dict = {
            "name": f"{crop}, {{{location}}}",
            'reference product': f"{crop}",
            'exchanges': [exc_dict_seed, exc_dict_unchanged],
            'unit': 'ha',
            'production amount': 1,
            'location': location
        }
        exc_list_new = exc_update(df, df_fer_id, water_id_dict, luc_id_dict)
        for exc_dict in exc_list_new:
            act_dict.get("exchanges").append(exc_dict)
        dbname_code = (new_db_name, activity_hash(act_dict))
        db_dict[dbname_code] = act_dict
        db_dict[dbname_code].get('exchanges').append({"amount": 1,
                                                      "input": dbname_code,
                                                      "type": 'production',
                                                      "name": f"{crop}, {{{location}}}"
                                                      })
    return db_dict


def create_crop_lci(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}'
    af_name = f"agrifootprint 6 {ei_name}_regionalized"
    afdb = bd.Database(af_name)
    new_db_name = f'{af_name}_update'
    #del bd.databases[new_db_name]
    if new_db_name in list(bd.databases):
        print(f'{new_db_name} already exist.')
    else:
        product_list = get_agri_product_list(afdb)
        df_lci = read_crop_lci_csv(year, scenario, product_list)
        df_lci_in_afdb = df_lci[df_lci.In_Afdb == 'Yes'].copy()
        df_lci_not_in_afdb = df_lci[df_lci.In_Afdb != 'Yes'].copy()
        df_fer_id = get_fertilizer_input(df_lci, afdb)
        new_db_dict = {}
        new_db_dict.update(update_unchanged_parts(product_list, new_db_name))
        temp_dict = new_db_dict.copy()
        new_db_dict.update(create_glo_unchanged_parts(new_db_name, df_lci_in_afdb, temp_dict))
        new_db_dict.update(update_seed(product_list, new_db_name, df_lci, df_fer_id))
        temp_dict = new_db_dict.copy()
        new_db_dict.update(create_new_seed(new_db_name, df_lci_not_in_afdb, temp_dict, df_fer_id))
        temp_dict = new_db_dict.copy()
        new_db_dict.update(update_crop(product_list, new_db_name, df_lci, temp_dict, df_fer_id))
        temp_dict = new_db_dict.copy()
        new_db_dict.update(create_new_crop(product_list, new_db_name, df_lci_not_in_afdb, temp_dict, df_fer_id))
        afdb_update = bd.Database(new_db_name)
        afdb_update.write(new_db_dict)
