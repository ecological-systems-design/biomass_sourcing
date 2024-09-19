import pandas as pd

from src.other.name_match import (get_country_match_df, get_country_match_df_globiom,
                                  get_country_match_df_fra, crop_dict)
from src.old.GLOBIOM_residue_potential import pivot_globiom_crop_data_c


def share_harvest_area_annual_crop():
    df_ha = pd.read_csv(r'data/external/FAOSTAT_crop_harvest_area.csv')
    df_map = pd.read_excel(r'data/raw_data/Crop_type_map.xlsx', engine='openpyxl', sheet_name='Crop_type_map')
    df_country = get_country_match_df()
    df_ha["Country"] = df_ha["Area Code (M49)"].map(df_country.set_index('Numeric')['GLOBIOM'])
    df_ha = pd.pivot_table(df_ha, values="Value",
                           index=['Country', 'Item'],
                           columns='Year',
                           aggfunc='sum')
    df_ha['Average'] = df_ha.mean(axis=1)
    df_ha.reset_index(inplace=True)
    df_ha['Crop_type'] = df_ha['Item'].map(df_map.set_index('Crop')['Crop_type'])
    df_ha = pd.pivot_table(df_ha, values="Average",
                           index=['Country'],
                           columns='Crop_type',
                           aggfunc='sum')
    df_ha.reset_index(inplace=True)
    df_ha = df_ha.fillna(0)
    df_ha['t_ratio'] = df_ha['t'] / (df_ha['t'] + df_ha['p'])
    return df_ha


def calculate_soil_organic_carbon():
    df_soc = pd.read_excel(r'data/external/Siegrist_climate_soil_by_country.xlsx',
                           engine='openpyxl', sheet_name='Climate Soil Data per Country')
    df_soc.loc[df_soc.COUNTRY == "Namibia", 'ISO'] = "NA"
    df_soc['Boreal_C'] = df_soc[[x for x in df_soc.columns if "bor" in x]].sum(axis=1)
    df_soc['Temp_cold_dry_C'] = df_soc[[x for x in df_soc.columns if "col_dr" in x]].sum(axis=1)
    df_soc['Temp_cold_moi_C'] = df_soc[[x for x in df_soc.columns if "col_mo" in x]].sum(axis=1)
    df_soc['Temp_warm_dry_C'] = df_soc[[x for x in df_soc.columns if "war_dr" in x]].sum(axis=1)
    df_soc['Temp_warm_moi_C'] = df_soc[[x for x in df_soc.columns if "war_mo" in x]].sum(axis=1)
    df_soc['Trop_dry_C'] = df_soc[[x for x in df_soc.columns if "tro_dr" in x]].sum(axis=1)
    df_soc['Trop_moi_C'] = df_soc[[x for x in df_soc.columns if "tro_mo" in x]].sum(axis=1)
    df_soc['Trop_wet_C'] = df_soc[[x for x in df_soc.columns if "tro_we" in x]].sum(axis=1)
    df_soc['Boreal_P'] = df_soc['Boreal_C'] / df_soc['_count']
    df_soc['Temp_cold_dry_P'] = df_soc['Temp_cold_dry_C'] / df_soc['_count']
    df_soc['Temp_cold_moi_P'] = df_soc['Temp_cold_moi_C'] / df_soc['_count']
    df_soc['Temp_warm_dry_P'] = df_soc['Temp_warm_dry_C'] / df_soc['_count']
    df_soc['Temp_warm_moi_P'] = df_soc['Temp_warm_moi_C'] / df_soc['_count']
    df_soc['Trop_dry_P'] = df_soc['Trop_dry_C'] / df_soc['_count']
    df_soc['Trop_moi_P'] = df_soc['Trop_moi_C'] / df_soc['_count']
    df_soc['Trop_wet_P'] = df_soc['Trop_wet_C'] / df_soc['_count']
    df_soc['FLU'] = df_soc['Boreal_P'] * 0.69 + (df_soc['Temp_cold_dry_P'] + df_soc['Temp_warm_dry_P']) * 0.8 \
                    + (df_soc['Temp_cold_moi_P'] + df_soc['Temp_warm_moi_P']) * 0.69 \
                    + df_soc['Trop_dry_P'] * 0.58 + (df_soc['Trop_moi_P'] + df_soc['Trop_wet_P']) * 0.48
    df_soc['Biomass_Grassland_t_DM_per_ha'] = df_soc['Boreal_P'] * 8.5 \
                                              + df_soc['Temp_cold_dry_P'] * 6.5 + df_soc['Temp_warm_dry_P'] * 6.1 \
                                              + df_soc['Temp_cold_moi_P'] * 13.6 + df_soc['Temp_warm_moi_P'] * 13.5 \
                                              + df_soc['Trop_dry_P'] * 8.7 + (
                                                      df_soc['Trop_moi_P'] + df_soc['Trop_wet_P']) * 16.1
    return df_soc


def calculate_luc_c(focus_year):
    df_luc = pd.read_csv(r'data/external/GLOBIOM_luc_grid.csv', header=None)
    df_luc.columns = ['COUNTRY', 'LU_GRID', 'UNIT', 'LU_FROM', 'LU_TO',
                      'SSP', 'SPA', 'SCENARIO', 'YEAR', 'VALUE']
    df_luc = df_luc[(df_luc.YEAR == focus_year) | (df_luc.YEAR == (focus_year - 10))].copy()
    # df_luc.loc[df_luc.LU_FROM == "NatLnd", 'LU_FROM'] = 'GrsLnd'  # assume to have the same carbon storage
    df_luc.loc[(df_luc.LU_FROM == "MngFor"), "LU_FROM"] = "ForLnd"
    df_luc.loc[(df_luc.LU_TO == "AfrLnd") |
               (df_luc.LU_TO == "MngFor") |
               (df_luc.LU_TO == "PltFor"), "LU_TO"] = "ForLnd"
    df_luc = pd.pivot_table(df_luc, values=["VALUE"],
                            index=['COUNTRY', 'UNIT', 'LU_FROM', 'LU_TO', 'SCENARIO'],
                            aggfunc='sum')
    df_luc.reset_index(inplace=True)
    df_luc['UNIT'] = '1000ha/20yr'
    return df_luc


def calculate_cropland_expansion_contraction(focus_year, change_type):
    if change_type == "EXPANSION":
        col_name = "LU_TO"
    else:
        col_name = "LU_FROM"
    df_luc = calculate_luc_c(focus_year)
    df_cropland_change = df_luc.groupby(by=["COUNTRY", "SCENARIO", col_name]).sum(numeric_only=True)
    df_cropland_change.reset_index(inplace=True)
    df_cropland_change = df_cropland_change.loc[df_cropland_change[col_name] == "CrpLnd",
                                                ["COUNTRY", "SCENARIO", 'VALUE']].copy()
    merge_name = f"CROPLAND_{change_type}_1000_HA_20_YR"
    df_cropland_change.rename(columns={"VALUE": merge_name}, inplace=True)
    return df_cropland_change


def calculate_luc_net_change_c(focus_year):
    df_luc = calculate_luc_c(focus_year)
    df_luc_1 = df_luc.copy()
    df_luc_1["LAND_USE"] = df_luc_1["LU_FROM"]
    df_luc_1["VALUE"] = -df_luc_1["VALUE"]
    df_luc_2 = df_luc.copy()
    df_luc_2["LAND_USE"] = df_luc_2["LU_TO"]
    df_luc_net_change = pd.concat([df_luc_1, df_luc_2], ignore_index=True)
    df_luc_net_change = pd.pivot_table(df_luc_net_change, values=["VALUE"],
                                       index=['COUNTRY', 'UNIT', 'SCENARIO', 'LAND_USE'],
                                       aggfunc='sum')
    df_luc_net_change.reset_index(inplace=True)
    return df_luc_net_change


def calculate_luc_net_change_by_land_use(focus_year, land_use):
    df_luc_net_change = calculate_luc_net_change_c(focus_year)
    df = df_luc_net_change.loc[df_luc_net_change.LAND_USE == land_use,
                               ["COUNTRY", "SCENARIO", 'VALUE']].copy()
    df.rename(columns={"VALUE": f"{land_use}_NET_EXPANSION_1000_HA_20_YR"}, inplace=True)
    return df


def calculate_crop_luc(focus_year):
    df_crop = pivot_globiom_crop_data_c()
    df_crop = df_crop[(df_crop.YEAR == (focus_year - 20)) | (df_crop.YEAR == focus_year)].copy()
    df = pd.pivot_table(df_crop, values="harvest_area",
                        index=['CROP', 'COUNTRY', 'SCENARIO'],
                        columns='YEAR', aggfunc='sum')
    df.reset_index(inplace=True)
    df = df.fillna(0)
    # check if crop area is expanded
    df["EXPANSION_1000ha"] = df[focus_year] - df[(focus_year - 20)]
    df.loc[df.EXPANSION_1000ha > 0, "LUC_IMPACT"] = 1
    df.loc[df.EXPANSION_1000ha <= 0, "LUC_IMPACT"] = 0
    df["REC"] = df["EXPANSION_1000ha"] / df[focus_year]
    df.loc[df.LUC_IMPACT == 0, "REC"] = 0
    # check if expansion from other land use types
    df_luc_cropland = calculate_luc_net_change_by_land_use(focus_year, "CrpLnd")
    df = pd.merge(df, df_luc_cropland, on=["COUNTRY", "SCENARIO"], how='left')

    df.loc[df.CrpLnd_NET_EXPANSION_1000_HA_20_YR > 0, "CHANGE_FROM_OTHER_LAND"] = 1
    df.loc[df.CrpLnd_NET_EXPANSION_1000_HA_20_YR <= 0, "CHANGE_FROM_OTHER_LAND"] = 0
    # calculate land use change from each land use type
    df_cropland_expansion = calculate_cropland_expansion_contraction(focus_year, "EXPANSION")
    df_cropland_contraction = calculate_cropland_expansion_contraction(focus_year, "CONTRACTION")
    df = pd.merge(df, df_cropland_expansion, on=["COUNTRY", "SCENARIO"], how='left')
    df = pd.merge(df, df_cropland_contraction, on=["COUNTRY", "SCENARIO"], how='left')
    df.fillna(0, inplace=True)
    df_annual_crop_share = share_harvest_area_annual_crop()
    df_annual_crop_share = df_annual_crop_share[["Country", "t_ratio"]].copy()
    df_annual_crop_share.rename(columns={"Country": "COUNTRY"}, inplace=True)
    df = pd.merge(df, df_annual_crop_share, on=["COUNTRY"], how='left')
    df.fillna(1, inplace=True)
    df["CROPLAND_CONTRACTION_AC_1000_HA_20_YR"] = df["CROPLAND_CONTRACTION_1000_HA_20_YR"] * df["t_ratio"]
    df["CROPLAND_CONTRACTION_PC_1000_HA_20_YR"] = df["CROPLAND_CONTRACTION_1000_HA_20_YR"] * (1-df["t_ratio"])
    df_luc_forest = calculate_luc_net_change_by_land_use(focus_year, "ForLnd")
    df_luc_forest["ForLnd_NET_EXPANSION_1000_HA_20_YR"] = -df_luc_forest["ForLnd_NET_EXPANSION_1000_HA_20_YR"]
    df_luc_forest.loc[df_luc_forest.ForLnd_NET_EXPANSION_1000_HA_20_YR < 0, "ForLnd_NET_EXPANSION_1000_HA_20_YR"] = 0
    df_luc_forest.rename(columns={"ForLnd_NET_EXPANSION_1000_HA_20_YR": "ForLnd_NET_CONTRACTION_1000_HA_20_YR"},
                         inplace=True)
    df = pd.merge(df, df_luc_forest, on=["COUNTRY", "SCENARIO"], how='left')
    df_luc_natlnd = calculate_luc_net_change_by_land_use(focus_year, "NatLnd")
    df_luc_natlnd["NatLnd_NET_EXPANSION_1000_HA_20_YR"] = -df_luc_natlnd["NatLnd_NET_EXPANSION_1000_HA_20_YR"]
    df_luc_natlnd.loc[df_luc_natlnd.NatLnd_NET_EXPANSION_1000_HA_20_YR < 0,
                      "NatLnd_NET_EXPANSION_1000_HA_20_YR"] = 0
    df_luc_natlnd.rename(columns={"NatLnd_NET_EXPANSION_1000_HA_20_YR": "NatLnd_NET_CONTRACTION_1000_HA_20_YR"},
                         inplace=True)
    df = pd.merge(df, df_luc_natlnd, on=["COUNTRY", "SCENARIO"], how='left')
    df_luc_grassland = calculate_luc_net_change_by_land_use(focus_year, "GrsLnd")
    df_luc_grassland["GrsLnd_NET_EXPANSION_1000_HA_20_YR"] = -df_luc_grassland["GrsLnd_NET_EXPANSION_1000_HA_20_YR"]
    df_luc_grassland.loc[df_luc_grassland.GrsLnd_NET_EXPANSION_1000_HA_20_YR < 0,
                         "GrsLnd_NET_EXPANSION_1000_HA_20_YR"] = 0
    df_luc_grassland.rename(columns={"GrsLnd_NET_EXPANSION_1000_HA_20_YR": "GrsLnd_NET_CONTRACTION_1000_HA_20_YR"},
                            inplace=True)
    df = pd.merge(df, df_luc_grassland, on=["COUNTRY", "SCENARIO"], how='left')

    df_luc_prifor = calculate_luc_net_change_by_land_use(focus_year, "PriFor")
    df_luc_prifor["PriFor_NET_EXPANSION_1000_HA_20_YR"] = -df_luc_prifor["PriFor_NET_EXPANSION_1000_HA_20_YR"]
    df_luc_prifor.loc[df_luc_prifor.PriFor_NET_EXPANSION_1000_HA_20_YR < 0,
                      "PriFor_NET_EXPANSION_1000_HA_20_YR"] = 0
    df_luc_prifor.rename(columns={"PriFor_NET_EXPANSION_1000_HA_20_YR": "PriFor_NET_CONTRACTION_1000_HA_20_YR"},
                         inplace=True)
    df = pd.merge(df, df_luc_prifor, on=["COUNTRY", "SCENARIO"], how='left')
    df.fillna(0, inplace=True)

    df['SEFG'] = 1 - df['CROPLAND_CONTRACTION_1000_HA_20_YR'] / df['CROPLAND_EXPANSION_1000_HA_20_YR']
    df.loc[df.SEFG <= 0, 'SEFG'] = 0
    df['SEF'] = df['SEFG'] * df['ForLnd_NET_CONTRACTION_1000_HA_20_YR'] / (
                df['ForLnd_NET_CONTRACTION_1000_HA_20_YR'] +
                df['GrsLnd_NET_CONTRACTION_1000_HA_20_YR'] +
                df['PriFor_NET_CONTRACTION_1000_HA_20_YR'] +
                df['NatLnd_NET_CONTRACTION_1000_HA_20_YR'])
    df['SEG'] = df['SEFG'] * df['GrsLnd_NET_CONTRACTION_1000_HA_20_YR'] / (
            df['ForLnd_NET_CONTRACTION_1000_HA_20_YR'] +
            df['GrsLnd_NET_CONTRACTION_1000_HA_20_YR'] +
            df['PriFor_NET_CONTRACTION_1000_HA_20_YR'] +
            df['NatLnd_NET_CONTRACTION_1000_HA_20_YR'])
    df['SEPF'] = df['SEFG'] * df['PriFor_NET_CONTRACTION_1000_HA_20_YR'] / (
            df['ForLnd_NET_CONTRACTION_1000_HA_20_YR'] +
            df['GrsLnd_NET_CONTRACTION_1000_HA_20_YR'] +
            df['PriFor_NET_CONTRACTION_1000_HA_20_YR'] +
            df['NatLnd_NET_CONTRACTION_1000_HA_20_YR'])
    df['SENL'] = df['SEFG'] * df['NatLnd_NET_CONTRACTION_1000_HA_20_YR'] / (
            df['ForLnd_NET_CONTRACTION_1000_HA_20_YR'] +
            df['GrsLnd_NET_CONTRACTION_1000_HA_20_YR'] +
            df['PriFor_NET_CONTRACTION_1000_HA_20_YR'] +
            df['NatLnd_NET_CONTRACTION_1000_HA_20_YR'])
    df.loc[df.CHANGE_FROM_OTHER_LAND == 0, 'SEF'] = 0
    df.loc[df.CHANGE_FROM_OTHER_LAND == 0, 'SEG'] = 0
    df.loc[df.CHANGE_FROM_OTHER_LAND == 0, 'SEPF'] = 0
    df.loc[df.CHANGE_FROM_OTHER_LAND == 0, 'SEFG'] = 0
    df.loc[df.CHANGE_FROM_OTHER_LAND == 0, 'SENL'] = 0
    df['SEP'] = (1 - df['SEFG']) * (df["CROPLAND_CONTRACTION_PC_1000_HA_20_YR"] /
                                    df['CROPLAND_CONTRACTION_1000_HA_20_YR'])
    df['SEA'] = (1 - df['SEFG']) * (df['CROPLAND_CONTRACTION_AC_1000_HA_20_YR'] /
                                    df['CROPLAND_CONTRACTION_1000_HA_20_YR'])
    df.loc[df.SEFG == 1, 'SEP'] = 0
    df.loc[df.SEFG == 1, 'SEA'] = 0
    df.loc[df.SEA.isna(), 'SEP'] = 0
    df.loc[df.SEA.isna(), 'SEF'] = 0
    df.loc[df.SEA.isna(), 'SEPF'] = 0
    df.loc[df.SEA.isna(), 'SENL'] = 0
    df.loc[df.SEA.isna(), 'SEG'] = 0
    df.loc[df.SEA.isna(), 'SEA'] = 1
    df['SF'] = df['SEF'] * df['REC']
    df['SPF'] = df['SEPF'] * df['REC']
    df['SNL'] = df['SENL'] * df['REC']
    df['SG'] = df['SEG'] * df['REC']
    df['SP'] = df['SEP'] * df['REC']
    df['SA'] = df['SEA'] * df['REC']
    return df


def calculate_crop_luc_ghg(focus_year):
    df_luc = calculate_crop_luc(focus_year)
    df_impact = df_luc[['CROP', 'COUNTRY', 'SCENARIO', focus_year-20, focus_year,
                        'SPF', 'SNL', 'SF', 'SG', 'SP', 'SA', 'REC']].copy()
    df_soc = calculate_soil_organic_carbon()
    df_soc.rename(columns={'Organic C Stock Mineral Soils (Tonnes C / ha) - with others (cells marked as others '
                           'recieved the average soil org C value of all soil types of that climate)':
                               "SOC_NON_A_t_per_ha"}, inplace=True)
    df_soc = df_soc[["ISO", "SOC_NON_A_t_per_ha", 'FLU', "Biomass_Grassland_t_DM_per_ha"]].copy()
    df_soc = df_soc.drop_duplicates(subset=['ISO'])
    df_country = get_country_match_df_globiom()
    df_impact["ISO"] = df_impact["COUNTRY"].map(df_country.set_index('GLOBIOM')['ISO2'])
    df_impact = pd.merge(df_impact, df_soc, on=["ISO"], how='left')
    df_impact.loc[df_impact.CROP == "Rice", "FLU"] = 1.1
    df_impact["SOC_EMISSION_kg_CO2_per_ha_per_year"] = ((1 - df_impact["FLU"]) *
                                                        df_impact["SOC_NON_A_t_per_ha"] *
                                                        (df_impact["SF"] + df_impact["SPF"] + df_impact["SNL"] +
                                                         df_impact["SG"] + df_impact["SP"]) *
                                                        44 / 12 * 1000 / 20)
    df_impact.loc[df_impact.SOC_EMISSION_kg_CO2_per_ha_per_year < 0, "SOC_EMISSION_kg_CO2_per_ha_per_year"] = 0
    df_forest_biomass = pd.read_excel(r'data/external/FRA_biomass_stock.xlsx', engine='openpyxl',
                                            sheet_name='FRA_biomass_stock')
    df_country_fra = get_country_match_df_fra()
    df_forest_biomass["ISO"] = df_forest_biomass["COUNTRY"].map(df_country_fra.set_index('FRA')['ISO2'])
    df_forest_biomass.rename(columns={'Above-ground biomass (tonnes/ha)': "AGB",
                                      'Below-ground biomass (tonnes/ha)': "BGB"},
                             inplace=True)
    df_forest_biomass["Biomass_Forest_t_DM_per_ha"] = df_forest_biomass["AGB"] + df_forest_biomass["BGB"]
    df_forest_biomass = df_forest_biomass[["ISO", "Biomass_Forest_t_DM_per_ha"]].copy()
    df_impact = pd.merge(df_impact, df_forest_biomass, on=["ISO"], how='left')
    df_impact['BIOMASS_DIFFERENCE_kg_CO2_per_ha_per_year'] = (((df_impact['SF'] + df_impact['SPF']) *
                                                              (df_impact['Biomass_Forest_t_DM_per_ha'] - 4) +
                                                               (df_impact['SG'] + df_impact['SNL']) *
                                                              (df_impact['Biomass_Grassland_t_DM_per_ha'] - 4) +
                                                               df_impact['SP'] *
                                                              (20 - 4)) * 0.47 * 44 / 12 / 20 * 1000)
    df_impact['TOTAL_LUC_kg_CO2_per_ha'] = (df_impact['BIOMASS_DIFFERENCE_kg_CO2_per_ha_per_year'] +
                                            df_impact["SOC_EMISSION_kg_CO2_per_ha_per_year"])
    df_impact['YEAR'] = focus_year
    df_impact['Crop'] = df_impact['CROP'].map(crop_dict)
    df_impact['Transformation, from forest, primary (non-use)'] = df_impact['SPF'] * 10000 / 20  # m2/ha/year
    df_impact['Transformation, from forest, extensive'] = df_impact['SF'] * 10000 / 20  # m2/ha/year
    df_impact['Transformation, from grassland, natural, for livestock grazing'] = df_impact['SG'] * 10000 / 20  # m2/ha/year
    df_impact['Transformation, from permanent crop'] = df_impact['SP'] * 10000 / 20  # m2/ha/year
    df_impact['Transformation, from annual crop'] = df_impact['SA'] * 10000 / 20  # m2/ha/year
    df_impact['Transformation, to annual crop'] = df_impact['REC'] * 10000 / 20  # m2/ha/year
    df_impact.rename(columns={'ISO': 'Country'}, inplace=True)
    df_impact = df_impact[['Crop', 'Country', 'SCENARIO', 'YEAR',
                           'Transformation, from forest, primary (non-use)',
                           'Transformation, from forest, extensive',
                           'Transformation, from grassland, natural, for livestock grazing',
                           'Transformation, from permanent crop',
                           'Transformation, from annual crop',
                           'Transformation, to annual crop',
                           'SOC_EMISSION_kg_CO2_per_ha_per_year',
                           'BIOMASS_DIFFERENCE_kg_CO2_per_ha_per_year',
                           'TOTAL_LUC_kg_CO2_per_ha']].copy()
    return df_impact


def calculate_crop_luc_ghg_all_years():
    df = pd.DataFrame()
    for focus_year in range(2020, 2060, 10):
        df = pd.concat([df, calculate_crop_luc_ghg(focus_year)], ignore_index=True)
        df.to_csv(r'data/interim/crop_lci_luc.csv')
    return df
