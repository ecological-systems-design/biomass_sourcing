import pandas as pd
import numpy as np
import os

from src.other.read_globiom_data import (read_globiom_forest_energy_consumption_r_data,
                                         read_globiom_forest_net_export_r_data,
                                         read_globiom_forest_total_production_r_data,
                                         read_globiom_forest_total_material_consumption_r_data,
                                         read_globiomfor_forest_production_c_data,
                                         read_globiom_forest_data_g,
                                         read_globiom_crop_data_g)
from src.other.name_match import get_country_match_df, get_country_match_df_globiom


def globiomfor_cnc_ratio():
    df = read_globiomfor_forest_production_c_data()
    df['CNC'] = 'NC'
    df = df.loc[df.PRODUCT.isin(['PW_Biomass', 'SW_Biomass'])].copy()
    df.loc[df.TYPE.str.contains('CurC'), 'CNC'] = 'C'
    df = pd.pivot_table(df, columns='CNC', index=['COUNTRY', 'UNIT', 'PRODUCT', 'SCENARIO', 'YEAR'],
                        values='VALUE', aggfunc='sum')
    df = df.fillna(0)
    df.reset_index(inplace=True)
    df['RATIO_C'] = df['C'] / (df['C'] + df['NC'])
    return df


def compile_globiom_forest_r_data():
    df_ec = read_globiom_forest_energy_consumption_r_data()
    df_mc = read_globiom_forest_total_material_consumption_r_data()
    df_tp = read_globiom_forest_total_production_r_data()
    df_ne = read_globiom_forest_net_export_r_data()
    df = pd.concat([df_tp, df_ne, df_ec, df_mc], axis=1)
    df = df.fillna(0)
    df.reset_index(inplace=True)
    product_list1 = ['SW_Biomass', 'PW_Biomass']
    product_list2 = ['Sawdust', 'WoodChips']
    df_swpw = df.loc[df.PRODUCT.isin(product_list1)].copy()
    df_swpw['ratio_material'] = df_swpw['VALUE_MC'] / (df_swpw['VALUE_EC'] + df_swpw['VALUE_MC'])
    df_swpw = df_swpw.fillna(1)
    df_swpw['PRODUCTION_M'] = df_swpw['VALUE_TP'] * df_swpw['ratio_material']
    df_pr = df.loc[df.PRODUCT.isin(product_list2)].copy()
    df['check'] = df['VALUE_TP'] - df['VALUE_NE'] - df['VALUE_EC'] - df['VALUE_MC']
    return df_swpw, df_pr


def globiom_forest_harvest_residue_potential():
    df_forest = read_globiom_forest_data_g()
    df_material_ratio = compile_globiom_forest_r_data()[0]
    df_material_ratio = df_material_ratio[['REGION', 'SCENARIO', 'PRODUCT', 'YEAR', 'ratio_material']].copy()
    df_cnc = globiomfor_cnc_ratio()
    df_cnc = df_cnc[['COUNTRY', 'PRODUCT', 'SCENARIO', 'YEAR', 'RATIO_C']].copy()
    df = pd.pivot_table(df_forest, values=["VALUE"],
                        index=["LU_GRID", "COUNTRY", "YEAR", "SCENARIO"],
                        columns=["ITEM", "PRODUCT", "UNIT"], aggfunc='sum')
    column_list = []
    for i in range(len(df.columns.values)):
        x = df.columns.values[i]
        name = x[1] + "_" + x[2] + "_" + x[3]
        column_list.append(name)

    df = df.droplevel([0, 1, 2], axis=1)
    df.columns = column_list
    df.reset_index(inplace=True)
    df = df.fillna(0)
    df = df[["LU_GRID", "COUNTRY", "YEAR", "SCENARIO",
             "YIELD_LoggingResidues_m3/ha",
             "YIELD_sawlogs+pulpwood_m3/ha_underbark",
             "YIELD_stemwood_m3/ha",
             "harvest_area_allproduct_1000ha/yr",
             "production_LoggingResidues_1000m3/yr",
             "production_PW_Biomass_1000m3/yr",
             "production_SW_Biomass_1000m3/yr"]].copy()
    df["YIELD_Total_harvest_residue_m3/ha"] = (df["YIELD_stemwood_m3/ha"] / 0.6 * 0.85 -
                                               df["YIELD_sawlogs+pulpwood_m3/ha_underbark"] / 0.864) * 0.864  # underbark
    df['ratio_LR_to_SWPW'] = df["YIELD_Total_harvest_residue_m3/ha"] / df["YIELD_sawlogs+pulpwood_m3/ha_underbark"]
    df = df[['LU_GRID', 'COUNTRY', 'YEAR', 'SCENARIO', 'ratio_LR_to_SWPW']].copy()
    df1 = df_forest[df_forest.ITEM == 'production'].copy()
    df1 = df1.loc[df1.PRODUCT.isin(['SW_Biomass', 'PW_Biomass'])].copy()
    df1 = pd.merge(df1, df_material_ratio, how='left', on=['REGION', 'SCENARIO', 'PRODUCT', 'YEAR'])
    df1 = pd.merge(df1, df, how='left', on=['LU_GRID', 'COUNTRY', 'YEAR', 'SCENARIO'])
    df1 = pd.merge(df1, df_cnc, how='left', on=['COUNTRY', 'PRODUCT', 'SCENARIO', 'YEAR'])
    df1 = df1.fillna(0)
    df_c = df1.copy()
    df_c['LR_1000_m3'] = df_c['VALUE'] * df_c['ratio_material'] * df_c['ratio_LR_to_SWPW'] * df_c['RATIO_C']
    df_c["LR_kt_DM"] = df_c['LR_1000_m3'] * 0.45
    df_c = df_c.groupby(by=['LU_GRID', 'COUNTRY', 'Country', 'REGION', 'YEAR', 'SCENARIO']).sum(numeric_only=True)
    df_c = df_c[['LR_kt_DM']].copy()
    df_c.reset_index(inplace=True)
    df_c["PRODUCT"] = "Logging residue, conifer"
    df_c['TYPE'] = 'C'
    df_nc = df1.copy()
    df_nc['LR_1000_m3'] = df_nc['VALUE'] * df_nc['ratio_material'] * df_nc['ratio_LR_to_SWPW'] * (1 - df_nc['RATIO_C'])
    df_nc["LR_kt_DM"] = df_nc['LR_1000_m3'] * 0.56
    df_nc = df_nc.groupby(by=['LU_GRID', 'COUNTRY', 'Country', 'REGION', 'YEAR', 'SCENARIO']).sum(numeric_only=True)
    df_nc = df_nc[['LR_kt_DM']].copy()
    df_nc.reset_index(inplace=True)
    df_nc["PRODUCT"] = "Logging residue, non-conifer"
    df_nc['TYPE'] = 'NC'
    df_output = pd.concat([df_c, df_nc], ignore_index=True)
    df_output['THEO_MIN'] = df_output['LR_kt_DM']
    df_output['THEO_MAX'] = df_output['LR_kt_DM']
    df_output["SUST_MIN"] = df_output["THEO_MIN"] * 0.5
    df_output["SUST_MAX"] = df_output["THEO_MAX"] * 0.5
    df_output["AVAI_MIN"] = df_output["SUST_MIN"]
    df_output["AVAI_MAX"] = df_output["SUST_MAX"]
    df_output["CAT1"] = "Forestry"
    df_output["CAT2"] = "Forestry harvest"
    df_output = df_output[['CAT1', 'CAT2', 'PRODUCT', 'TYPE', 'LU_GRID',
                           'COUNTRY', 'Country', 'REGION', 'YEAR', 'SCENARIO',
                           'THEO_MIN', 'THEO_MAX', 'SUST_MIN', 'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX']].copy()
    return df_output


def globiom_forest_process_residue_potential():
    df_country = get_country_match_df_globiom()
    df_h_g = globiom_forest_harvest_residue_potential()
    df_p_r = compile_globiom_forest_r_data()[1]
    df_h_r = pd.pivot_table(df_h_g, index=['REGION', 'YEAR', 'SCENARIO', 'TYPE'], values='THEO_MIN', aggfunc='sum')
    df_h_r.reset_index(inplace=True)
    df_cnc = globiomfor_cnc_ratio()
    df_cnc = df_cnc[df_cnc.PRODUCT == 'SW_Biomass'].copy()
    df_cnc['REGION'] = df_cnc['COUNTRY'].map(df_country.set_index('GLOBIOM')['GLOBIOM_region'])
    df_cnc = df_cnc.groupby(by=['REGION', 'YEAR', 'SCENARIO']).sum(numeric_only=True)
    df_cnc['RATIO_C'] = df_cnc['C'] / (df_cnc['C'] + df_cnc['NC'])
    df_cnc.reset_index(inplace=True)
    df_p_r = pd.merge(df_p_r, df_cnc, how='left', on=['REGION', 'SCENARIO', 'YEAR'])
    df_p_r = df_p_r.fillna(0)
    df_p_r['ratio_ec'] = df_p_r['VALUE_EC'] / (df_p_r['VALUE_MC'] + df_p_r['VALUE_EC'])
    df_p_r['ratio_ec'] = df_p_r['ratio_ec'].fillna(1)
    df_p_r['AVAI_MIN'] = df_p_r['VALUE_TP'] * df_p_r['ratio_ec']
    df_p_r['THEO_MIN'] = df_p_r['VALUE_TP']
    df_p_r_c = df_p_r.copy()
    df_p_r_c['THEO_MIN'] = df_p_r_c['THEO_MIN'] * df_p_r_c['RATIO_C'] * 450  # kt
    df_p_r_c['AVAI_MIN'] = df_p_r_c['AVAI_MIN'] * df_p_r_c['RATIO_C'] * 450  # kt
    df_p_r_c['TYPE'] = 'C'
    df_p_r_c['PRODUCT'] += f', conifer'
    df_p_r_nc = df_p_r.copy()
    df_p_r_nc['THEO_MIN'] = df_p_r_nc['THEO_MIN'] * df_p_r_nc['RATIO_C'] * 560  # kt
    df_p_r_nc['AVAI_MIN'] = df_p_r_nc['AVAI_MIN'] * df_p_r_nc['RATIO_C'] * 560  # kt
    df_p_r_nc['TYPE'] = 'NC'
    df_p_r_nc['PRODUCT'] += f', non-conifer'
    df_p_r = pd.concat([df_p_r_c, df_p_r_nc], ignore_index=True)
    df_p_r = df_p_r[['REGION', 'SCENARIO', 'PRODUCT', 'YEAR', 'AVAI_MIN', 'THEO_MIN', 'TYPE']].copy()
    df_h_r = df_h_r.rename(columns={'THEO_MIN': 'LR'})
    df_r = pd.merge(df_p_r, df_h_r, how='left', on=['REGION', 'YEAR', 'SCENARIO', 'TYPE'])
    df_r = df_r.dropna()
    df_r['AVAI_to_LR'] = 0
    df_r['THEO_to_LR'] = 0
    df_r.loc[df_r.LR > 0, 'AVAI_to_LR'] = df_r.loc[df_r.LR > 0, 'AVAI_MIN'] / df_r.loc[df_r.LR > 0, 'LR']
    df_r.loc[df_r.LR > 0, 'THEO_to_LR'] = df_r.loc[df_r.LR > 0, 'THEO_MIN'] / df_r.loc[df_r.LR > 0, 'LR']
    df_r = df_r.fillna(0)
    df_r = df_r[['REGION', 'SCENARIO', 'PRODUCT', 'YEAR', 'TYPE', 'AVAI_to_LR', 'THEO_to_LR']]
    df_wc_g = df_h_g.copy()
    df_wc_g['PRODUCT'] = 'WoodChips'
    df_wc_g['CAT2'] = 'Forest process'
    df_sd_g = df_h_g.copy()
    df_sd_g['PRODUCT'] = 'Sawdust'
    df_sd_g['CAT2'] = 'Forest process'
    df_g = pd.concat([df_wc_g, df_sd_g], ignore_index=True)
    df_g.loc[df_g.TYPE == 'C', 'PRODUCT'] += f', conifer'
    df_g.loc[df_g.TYPE == 'NC', 'PRODUCT'] += f', non-conifer'
    df_g = pd.merge(df_g, df_r, how='left', on=['REGION', 'YEAR', 'SCENARIO', 'PRODUCT', 'TYPE'])
    df_g['AVAI_MIN'] = df_g['THEO_MIN'] * df_g['AVAI_to_LR']
    df_g['AVAI_MAX'] = df_g['THEO_MIN'] * df_g['AVAI_to_LR']
    df_g['THEO_MIN'] *= df_g['THEO_to_LR']
    df_g['THEO_MAX'] *= df_g['THEO_to_LR']
    df_g['SUST_MIN'] = df_g['THEO_MIN']
    df_g['SUST_MAX'] = df_g['THEO_MIN']
    df_output = df_g[['CAT1', 'CAT2', 'PRODUCT', 'TYPE', 'LU_GRID',
                      'COUNTRY', 'Country', 'REGION', 'YEAR', 'SCENARIO',
                      'THEO_MIN', 'THEO_MAX', 'SUST_MIN', 'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX']].copy()
    return df_output


def globiom_crop_data_with_crops_in_scope():
    df_crop = read_globiom_crop_data_g()
    df_crop = df_crop[
        (df_crop.CROP == "Barl") | (df_crop.CROP == "Corn") | (df_crop.CROP == "Rice") | (df_crop.CROP == "Rape") |
        (df_crop.CROP == "Soya") | (df_crop.CROP == "Srgh") | (df_crop.CROP == "SugC") | (df_crop.CROP == "Whea")]
    return df_crop


def pivot_globiom_crop_data_g():
    df_crop = globiom_crop_data_with_crops_in_scope()
    table_crop = pd.pivot_table(df_crop, values=["VALUE"], index=['CROP', 'LU_GRID', 'COUNTRY', 'SCENARIO', 'YEAR'],
                                columns=["ITEM"], aggfunc='sum')
    table_crop = table_crop.droplevel(level=0, axis=1)
    table_crop.reset_index(inplace=True)
    table_crop['YIELD'] = table_crop['production'] / table_crop['harvest_area']
    return table_crop


def crop_residue_potential_g():
    table_crop = pivot_globiom_crop_data_g()
    # RPR parameters
    rpr_br = pd.read_excel(r'data/raw_data/RPR.xlsx', engine='openpyxl', sheet_name='BentsenRonzon')
    rpr_s = pd.read_excel(r'data/raw_data/RPR.xlsx', engine='openpyxl', sheet_name='Scarlat')
    rpr_f = pd.read_excel(r'data/raw_data/RPR.xlsx', engine='openpyxl', sheet_name='Fischer')
    # Residues of rice husks
    '''
    variables from Global Potential of Rice Husk as a Renewable Feedstock for Ethanol Biofuel Production and
    Assessment of Agricultural Biomass Residues for Anaerobic Digestion in Rural Vakinankaratra Region of Madagascar
    '''
    table_rh = table_crop[table_crop.CROP == "Rice"].copy()
    table_rh["THEO_MIN"] = table_rh["production"] * 0.20 * 0.87
    table_rh["THEO_MAX"] = table_rh["production"] * 0.36 * 0.87
    table_rh["CAT2"] = "Agricultural process"
    table_rh["RESIDUE"] = "Rice husks"
    # residues from sugarcane bagasse
    '''
    variables from Energy and GHG emission reduction potential of power generation from sugarcane residues in Thailand
    '''
    table_sb = table_crop[table_crop.CROP == "SugC"].copy()
    table_sb["THEO_MIN"] = table_sb["production"] * 0.23 * 0.5
    table_sb["THEO_MAX"] = table_sb["production"] * 0.37 * 0.5
    table_sb["CAT2"] = "Agricultural process"
    table_sb["RESIDUE"] = "Sugarcane bagasse"
    # residues from sugarcane tops and leaves
    table_st = table_crop[table_crop.CROP == "SugC"].copy()
    table_st["THEO_MIN"] = table_st["production"] * 0.17 * 0.5
    table_st["THEO_MAX"] = table_st["production"] * 0.30 * 0.5
    table_st["CAT2"] = "Agricultural harvest"
    table_st["RESIDUE"] = "Sugarcane tops and leaves"
    # rest residues
    table_crop = table_crop[table_crop.CROP != "SugC"]
    for crop in list(table_crop.CROP.unique()):
        if crop in list(rpr_br.Crop.unique()):
            dm = rpr_br.loc[(rpr_br.Crop == crop), "DM"].iloc[0]
            residue = rpr_br.loc[(rpr_br.Crop == crop), "Residue"].iloc[0]
            a = rpr_br.loc[(rpr_br.Crop == crop), "a"].iloc[0]
            b = rpr_br.loc[(rpr_br.Crop == crop), "b"].iloc[0]
            table_crop.loc[table_crop.CROP == crop, "RPR_BR"] = a * np.exp(
                b * dm * table_crop.loc[table_crop.CROP == crop, "YIELD"])
            table_crop.loc[table_crop.CROP == crop, "RESIDUE"] = residue
        if crop in list(rpr_s.Crop.unique()):
            dm = rpr_s.loc[(rpr_s.Crop == crop), "DM"].iloc[0]
            a = rpr_s.loc[(rpr_s.Crop == crop), "a"].iloc[0]
            b = rpr_s.loc[(rpr_s.Crop == crop), "b"].iloc[0]
            table_crop.loc[table_crop.CROP == crop, "RPR_S"] = a * np.log(
                dm * table_crop.loc[table_crop.CROP == crop, "YIELD"]) + b
        if crop in list(rpr_f.Crop.unique()):
            dm = rpr_f.loc[(rpr_f.Crop == crop), "DM"].iloc[0]
            a = rpr_f.loc[(rpr_f.Crop == crop), "a"].iloc[0]
            b = rpr_f.loc[(rpr_f.Crop == crop), "b"].iloc[0]
            table_crop.loc[table_crop.CROP == crop, "RPR_F"] = a * (
                    dm * table_crop.loc[table_crop.CROP == crop, "YIELD"]) + b
    table_crop.loc[table_crop.RPR_S < 0, "RPR_S"] = np.nan
    table_crop.loc[table_crop.RPR_F < 0, "RPR_F"] = np.nan
    table_crop[["RPR_F", "RPR_S", "RPR_BR"]].min(axis=1)
    table_crop["THEO_MIN"] = table_crop["production"] * table_crop[["RPR_F", "RPR_S", "RPR_BR"]].min(axis=1)
    table_crop["THEO_MAX"] = table_crop["production"] * table_crop[["RPR_F", "RPR_S", "RPR_BR"]].max(axis=1)
    table_crop["CAT2"] = "Agricultural harvest"

    df_residue = pd.concat([table_crop, table_rh, table_sb, table_st])
    df_residue["CAT1"] = "Agricultural"
    df_residue['UNIT'] = "1000ton/year"

    # sustainable potential: 250 ton/km2 = 250/1000 kt / (0.1 kha)
    # from "Projections of the availability and cost of residues from agriculture and forestry"
    df_residue["SUST_MIN"] = df_residue["THEO_MIN"] - (df_residue["harvest_area"] * 250 / 100)
    df_residue["SUST_MAX"] = df_residue["THEO_MAX"] - (df_residue["harvest_area"] * 250 / 100)
    df_residue.loc[df_residue.CAT2 == "Agricultural process", "SUST_MIN"] = \
        df_residue.loc[df_residue.CAT2 == "Agricultural process", "THEO_MIN"]
    df_residue.loc[df_residue.CAT2 == "Agricultural process", "SUST_MAX"] = \
        df_residue.loc[df_residue.CAT2 == "Agricultural process", "THEO_MAX"]

    df_residue.loc[df_residue.SUST_MIN < 0, "SUST_MIN"] = 0
    df_residue.loc[df_residue.SUST_MAX < 0, "SUST_MAX"] = 0

    # available potential: 70% of sustainable potential, rest as animal feed etc (Ronzon et al., 2017)
    df_residue["AVAI_MIN"] = df_residue["SUST_MIN"] * 0.7
    df_residue["AVAI_MAX"] = df_residue["SUST_MAX"] * 0.7
    df_residue.reset_index(inplace=True)
    df_residue.to_csv('data/interim/GLOBIOM_agricultural_residue_g_full.csv')
    df_residue = df_residue[["CAT1", "CAT2", "RESIDUE", "UNIT", "LU_GRID", "COUNTRY", "YEAR", "SCENARIO",
                             "THEO_MIN", "THEO_MAX", "SUST_MIN", "SUST_MAX", "AVAI_MIN", "AVAI_MAX"]].copy()
    return df_residue


def crop_residue_potential_c():
    if os.path.exists(r'data/interim/GLOBIOM_agricultural_residue_g_full.csv'):
        df = pd.read_csv(r'data/interim/GLOBIOM_agricultural_residue_g_full.csv')
    else:
        df = crop_residue_potential_g()
    df_c = pd.pivot_table(df, values=["THEO_MIN", "THEO_MAX", "SUST_MIN", "SUST_MAX", "AVAI_MIN", "AVAI_MAX"],
                          index=['RESIDUE', 'COUNTRY', 'YEAR', 'SCENARIO'],
                          aggfunc='sum')
    df_c.reset_index(inplace=True)
    df_c.to_csv("data/interim/GLOBIOM_agricultural_residue_c.csv")
    return df_c


def all_residue_potential_g():
    dfc = crop_residue_potential_g()
    dff1 = globiom_forest_harvest_residue_potential()
    dff2 = globiom_forest_process_residue_potential()
    dff = pd.concat([dff1, dff2], ignore_index=True)
    dff = dff.rename(columns={'PRODUCT': 'RESIDUE'})
    dff['UNIT'] = '1000ton/year'
    dff = dff[['CAT1', 'CAT2', 'RESIDUE', 'UNIT', 'LU_GRID', 'COUNTRY', 'YEAR', 'SCENARIO',
               'THEO_MIN', 'THEO_MAX', 'SUST_MIN', 'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX']].copy()
    df = pd.concat([dfc, dff], ignore_index=True)
    return df


def all_residue_available_potential_g_no_scenario():
    df0 = all_residue_potential_g()
    df = pd.pivot_table(df0, index=['CAT1', 'CAT2', 'RESIDUE', 'UNIT', 'LU_GRID', 'COUNTRY', 'YEAR'],
                        columns='SCENARIO', values=['THEO_MIN', 'THEO_MAX', 'SUST_MIN',
                                                    'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX'], aggfunc='sum')
    df = df.fillna(0)
    df.reset_index(inplace=True)
    '''
    df[('THEO_MIN', '')] = df[('THEO_MIN', 'scenRCP1p9')].copy()
    df[('THEO_MAX', '')] = df[('THEO_MAX', 'scenRCPref')].copy()
    df[('SUST_MIN', '')] = df[('SUST_MIN', 'scenRCP1p9')].copy()
    df[('SUST_MAX', '')] = df[('SUST_MAX', 'scenRCPref')].copy()
    df[('AVAI_MAX', '')] = df[('AVAI_MAX', 'scenRCPref')].copy()
    df[('AVAI_MIN', '')] = df[('AVAI_MIN', 'scenRCP1p9')].copy()
    df.loc[df[('CAT1', '')] == 'Forestry', ('AVAI_MAX', '')] = df.loc[
        df[('CAT1', '')] == 'Forestry', ('AVAI_MAX', 'scenRCP1p9')].copy()
    df.loc[df[('CAT1', '')] == 'Forestry', ('AVAI_MIN', '')] = df.loc[
        df[('CAT1', '')] == 'Forestry', ('AVAI_MIN', 'scenRCPref')].copy()
    df.loc[df[('CAT1', '')] == 'Forestry', ('SUST_MAX', '')] = df.loc[
        df[('CAT1', '')] == 'Forestry', ('SUST_MAX', 'scenRCP1p9')].copy()
    df.loc[df[('CAT1', '')] == 'Forestry', ('SUST_MIN', '')] = df.loc[
        df[('CAT1', '')] == 'Forestry', ('SUST_MIN', 'scenRCPref')].copy()
    df.loc[df[('CAT1', '')] == 'Forestry', ('THEO_MAX', '')] = df.loc[
        df[('CAT1', '')] == 'Forestry', ('THEO_MAX', 'scenRCP1p9')].copy()
    df.loc[df[('CAT1', '')] == 'Forestry', ('THEO_MIN', '')] = df.loc[
        df[('CAT1', '')] == 'Forestry', ('THEO_MIN', 'scenRCPref')].copy()
    '''
    for x in ['THEO_MIN', 'THEO_MAX', 'SUST_MIN', 'SUST_MAX', 'AVAI_MIN', 'AVAI_MAX']:
        df[(x, '')] = (df[(x, 'scenRCP1p9')] + df[(x, 'scenRCPref')]) / 2
        # df[(x, '')] = df[[(x, 'scenRCP1p9'), (x, 'scenRCPref')]].min(axis=1)
    df = df[[('CAT1', ''),  ('CAT2', ''), ('RESIDUE', ''), ('UNIT', ''), ('LU_GRID', ''),
             ('COUNTRY', ''), ('YEAR', ''), ('THEO_MIN', ''), ('THEO_MAX', ''), ('SUST_MIN', ''), ('SUST_MAX', ''),
             ('AVAI_MIN', ''), ('AVAI_MAX', '')]].copy()
    df1 = df.droplevel(1, axis=1)
    return df1


def export_all_residues_c():
    df_g = all_residue_available_potential_g_no_scenario()
    df_country = get_country_match_df_globiom()
    df_g['Country'] = df_g['COUNTRY'].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_g['Product'] = df_g['RESIDUE']
    df_c = df_g.groupby(by=['CAT1', 'CAT2', 'Product', 'Country', 'YEAR']).sum(numeric_only=True)
    df_c.reset_index(inplace=True)
    df_c.to_csv('data/interim/GLOBIOM_all_residue_c_processed.csv')
    return df_c