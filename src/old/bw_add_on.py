import bw2data as bd
import pandas as pd
import os


from src.bw.bw_base_set_up import bw_set_up
from src.other.name_match import (get_country_match_df, get_country_match_df_globiom,
                                  get_lca_db_locations, lca_loc_dict)
from src.data.lcia_regionalized_cfs import calculate_area_per_country_and_land_use


def bw_add_lcia_method_ipcc_ar6():
    df = pd.read_excel(r'data/raw_data/ghg_cfs_ipcc_ar6.xlsx', engine='openpyxl', sheet_name='CFs')
    for pj in bd.projects:
        if "biomass_" in pj.name:
            print(pj.name)
            project_name = pj.name
            bd.projects.set_current(project_name)
            bio = bd.Database("biosphere3")
            for cf in ['GWP_100a', 'GTP_100a']:
                method_delete = bd.Method(('IPCC_AR6', cf, 'fossil'))
                method_delete.deregister()
                method_delete = bd.Method(('IPCC_AR6', cf, 'biogenic'))
                method_delete.deregister()
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
                    try:
                        ipcc_method.deregister()
                    except:
                        pass
                    ipcc_data = {'unit': 'CO2-eq',
                                 'num_cfs': len(flows_list),
                                 'description': 'ipcc ar6 cf'}
                    ipcc_method.validate(flows_list)
                    ipcc_method.register(**ipcc_data)
                    ipcc_method.write(flows_list)
    return df


def calculate_area_weighted_regional_biodiversity_cfs_new():
    cf_o = pd.read_csv(r'data/external/biodiversity_CF_country_domain.csv', encoding='ISO-8859-1')
    df_country = get_country_match_df()
    df_country_globiom = get_country_match_df_globiom()
    df_area = calculate_area_per_country_and_land_use()
    df_cf = cf_o.copy()
    df_cf['Country'] = df_cf['iso3cd'].map(df_country.set_index('ISO3')['ISO2']).copy()
    df_cf = df_cf.dropna(subset=['Country'])
    df_area['Country'] = df_area['COUNTRY'].map(df_country_globiom.set_index('GLOBIOM')['ISO2']).copy()
    df_cf = df_cf[df_cf.Country.isin(list(df_area['Country'].unique()))]
    for x in df_cf.index:
        country = df_cf.loc[x, 'Country']
        hab_id = df_cf.loc[x, 'habitat_id']
        area = df_area.loc[df_area.Country == country, hab_id].iloc[0]
        df_cf.loc[x, 'Area'] = area
    df_cf = df_cf[['Country', 'habitat', 'CF_occ_avg_glo', 'CF_tra_avg_glo', 'Area']].copy()
    df_cf = df_cf.rename(columns={'Country': 'Location'})

    df_cf_r = df_cf.copy()
    df_cf_r['AFDB_region'] = df_cf_r['Location'].map(df_country.set_index('ISO2')['AFDB_region']).copy()
    df_cf_r['IMAGE_region'] = df_cf_r['Location'].map(df_country.set_index('ISO2')['IMAGE_region']).copy()
    df_cf_r['Ecoinvent_region'] = df_cf_r['Location'].map(df_country.set_index('ISO2')['Ecoinvent_region']).copy()
    df_cf_r['CF_occ_X_area'] = df_cf_r['CF_occ_avg_glo'] * df_cf_r['Area']
    df_cf_r['CF_tra_X_area'] = df_cf_r['CF_tra_avg_glo'] * df_cf_r['Area']
    for x in ['AFDB_region', 'IMAGE_region', 'Ecoinvent_region']:
        df_temp = pd.pivot_table(df_cf_r, index=[x, 'habitat'],
                                 values=['Area', 'CF_occ_X_area', 'CF_tra_X_area'], aggfunc='sum')
        df_temp.reset_index(inplace=True)
        df_temp = df_temp.rename(columns={x: 'Location'})
        df_temp = df_temp.loc[~df_temp.Location.isin(list(df_cf.Location.unique()))]
        df_temp['CF_occ_avg_glo'] = df_temp['CF_occ_X_area'] / df_temp['Area']
        df_temp['CF_tra_avg_glo'] = df_temp['CF_tra_X_area'] / df_temp['Area']
        df_cf = pd.concat([df_cf, df_temp[['Location', 'habitat', 'CF_occ_avg_glo', 'CF_tra_avg_glo', 'Area']]],
                          ignore_index=True)

    df_cf_g = pd.pivot_table(df_cf_r, index=['habitat'],
                             values=['Area', 'CF_occ_X_area', 'CF_tra_X_area'], aggfunc='sum')
    df_cf_g['CF_occ_avg_glo'] = df_cf_g['CF_occ_X_area'] / df_cf_g['Area']
    df_cf_g['CF_tra_avg_glo'] = df_cf_g['CF_tra_X_area'] / df_cf_g['Area']
    df_cf_g.reset_index(inplace=True)
    df_cf_g['Location'] = 'GLO'
    df_cf = pd.concat([df_cf, df_cf_g[['Location', 'habitat', 'CF_occ_avg_glo', 'CF_tra_avg_glo', 'Area']]],
                      ignore_index=True)
    df_cf = df_cf.dropna()
    return df_cf


def biodiversity_cf_match_locations_new():
    df_cf = calculate_area_weighted_regional_biodiversity_cfs_new()
    loc_list = get_lca_db_locations()
    for loc in loc_list:
        if loc not in list(df_cf.Location.unique()):
            if loc in lca_loc_dict.keys():
                loc2 = lca_loc_dict[loc]
            elif '-' in loc:
                loc2 = loc.split('-')[0]
                if loc2 not in loc_list:
                    print(loc2)
            else:
                loc2 = 'TBD'
                print(loc)
            df_temp = df_cf[df_cf.Location == loc2].copy()
            df_temp['Location'] = loc
            df_cf = pd.concat([df_cf, df_temp], ignore_index=True)
    df_cf.to_csv('data/interim/cf_biodiversity_processed_new.csv')
    return df_cf


def bw_add_lcia_method_biodiversity():
    flows_occ_list = []
    flows_tra_list = []
    if os.path.exists(r'data/interim/cf_biodiversity_processed_new.csv'):
        df = pd.read_csv(r'data/interim/cf_biodiversity_processed_new.csv', index_col=0)
        df['Location'] = df['Location'].fillna('NA')
    else:
        df = biodiversity_cf_match_locations_new()
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
    return flows_occ_list, flows_tra_list


def biodiversity_update_to_projects():
    flows_occ_list, flows_tra_list = bw_add_lcia_method_biodiversity()
    for pj in bd.projects:
        if "biomass_" in pj.name:
            print(pj.name)
            project_name = pj.name
            bd.projects.set_current(project_name)
            try:
                method_delete = bd.Method(('Biodiversity regionalized', 'Transformation'))
                method_delete.deregister()
                method_delete = bd.Method(('Biodiversity regionalized', 'Occupation'))
                method_delete.deregister()
            except:
                pass
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
    a=0