import bw2io as bi
import bw2data as bd
from premise import *
from src.bw.bw_base_set_up import (bw_generate_new_biosphere_data_luluc, bw_generate_new_biosphere_data_water,
                                   bw_add_lcia_method_biodiversity, bw_add_lcia_method_aware,
                                   bw_add_lcia_method_ipcc_ar6)
from src.bw.bw_scenario_set_up import regionalize_db, import_agrifootprint, create_crop_lci, create_forest_lci


def import_premise_310(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    newdb_name = f'ecoinvent_image_{pathway}_{year}'
    if newdb_name in list(bd.databases):
        print(f'{newdb_name} already exist. No need to set up with premise')
    else:
        ndb = NewDatabase(
            scenarios=[
                {"model": "image", "pathway": pathway, "year": year},
            ],
            source_db="'ecoinvent-3.10-cutoff'",  # <-- name of the database in the BW2 project. Must be a string.
            source_version="3.10",  # <-- version of ecoinvent. Can be "3.5", "3.6", "3.7" or "3.8". Must be a string.
            key='tUePmX_S5B8ieZkkM7WUU2CnO8SmShwmAeWK9x2rTFo='  # <-- decryption key
            # to be requested from the library maintainers if you want ot use default scenarios included in `premise`
        )
        ndb.update_all()
        ndb.write_db_to_brightway()


def import_ecoinvent_310():
    bd.projects.set_current('base_ecoinvent_310')
    if 'ecoinvent-3.10-biosphere' not in bd.databases:
        bi.import_ecoinvent_release('3.10', 'cutoff', 'studentethz', 'AwqaDd4E9VLnu-)')
    else:
        print('ecoinvent 3.10 is already imported')
    bio = bd.Database("ecoinvent-3.10-biosphere")
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
    bi.backup_project_directory('base_ecoinvent_310')
    year = 2050
    scenario = 'scenRCP1p9'
    project_name = f'plastics310_{year}_{scenario}'
    project_list = list(bd.projects)
    if project_name not in [x.name for x in project_list]:
        bd.projects.copy_project(project_name)
    else:
        bd.projects.set_current(project_name)
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    ei_name = f'ecoinvent_image_{pathway}_{year}'
    af_name = f"agrifootprint 6 {ei_name}"
    import_premise_310(year, scenario)
    regionalize_db(ei_name)
    import_agrifootprint(ei_name)
    regionalize_db(af_name)
    create_crop_lci(year, scenario)
    create_forest_lci(year, scenario)
    # create_chemical_lci(year, scenario)
    # df = lcia_all(year, scenario)
    # bi.backup_project_directory(project_name)
    a = 0
