import bw2data as bd
from premise import *
import re
from copy import deepcopy


from src.bw.bw_import_agrifootprint import import_agrifootprint
from src.bw.bw_agriculture_lci import create_crop_lci
from src.bw.bw_forest_lci import create_forest_lci
from src.bw.bw_chemical_lci import create_chemical_lci
from src.bw.bw_base_set_up import bw_add_lcia_method_ipcc_ar6


def import_premise(year, scenario):
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
            source_db="ecoinvent 3.8",  # <-- name of the database in the BW2 project. Must be a string.
            source_version="3.8",  # <-- version of ecoinvent. Can be "3.5", "3.6", "3.7" or "3.8". Must be a string.
            key='tUePmX_S5B8ieZkkM7WUU2CnO8SmShwmAeWK9x2rTFo='  # <-- decryption key
            # to be requested from the library maintainers if you want ot use default scenarios included in `premise`
        )
        ndb.update_all()
        ndb.write_db_to_brightway()


def check_if_act_is_agri(act):
    agri_yes_no = 0
    if 'simapro metadata' in act.as_dict().keys():
        if 'blue water' in act.get('simapro metadata').get('Comment'):
            agri_yes_no += 1
    if 'Farming and supply' in act.get('name'):
        agri_yes_no += 1
    if 'classifications' in act.as_dict().keys():
        for i in act.get('classifications'):
            if i[0] == 'ISIC rev.4 ecoinvent':
                if (
                        ('011' in i[1] or '012' in i[1])
                        and '201' not in i[1]
                        and '301' not in i[1]
                ):
                    agri_yes_no += 1
            elif i[1] == 'agricultural production/plant production':
                agri_yes_no += 1
    return agri_yes_no


def regionalize_ecoinvent(year, scenario):
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    db_name = f'ecoinvent_image_{pathway}_{year}'
    regionalized_db_name = f'{db_name}_regionalized'
    if regionalized_db_name in list(bd.databases):
        print(f'{regionalized_db_name} already exist. No need to copy from {db_name}.')
    else:
        print(f'start copying {db_name} to {regionalized_db_name}.')
        bd.Database(db_name).copy(regionalized_db_name)
        bio = bd.Database("biosphere3")
        ei = bd.Database(regionalized_db_name)
        new_bio_db_luc = bd.Database('biosphere luluc regionalized')
        new_bio_db_water = bd.Database('biosphere water regionalized')
        # flag_db = ei.metadata.get("regionalized", False)
        # if not flag_db:
        print('start regionalizing water and land flows')
        water_use_list = [act for act in bio if "Water" in act['name']
                          and 'natural resource' in act['categories']
                          and 'air' not in act['name']
                          and 'ocean' not in act['name']
                          and 'ocean' not in act.get('categories')]
        water_emission_list = [act for act in bio if "Water" in act['name']
                               and 'water' in act['categories']
                               and 'ocean' not in act.get('categories')]
        water_list = water_use_list + water_emission_list
        luluc_list = [act for act in bio if ("occupation" in act['name'].lower()
                                             or 'transformation' in act['name'].lower())
                      and 'non-use' not in act['name']
                      and 'obsolete' not in act['name']]
        i = 0
        for act in ei:
            i += 1
            if i % 100 == 0:
                print(f'updated {str(i)} activities')
            agri_yes_no = check_if_act_is_agri(act)
            for exc in act.exchanges():
                if exc.input in water_list:
                    flag_replaced = exc.get("replaced with regionalized", False)
                    if not flag_replaced:
                        data = deepcopy(exc.as_dict())
                        try:
                            data.pop('flow')
                        except:
                            pass
                        if agri_yes_no >= 1:
                            exc_name = exc.input['name'] + ', irrigation'
                            bio_act_regionalized = [
                                bio_act for bio_act in new_bio_db_water if
                                bio_act['name'] == exc_name and
                                bio_act['categories'] == exc.input['categories'] and
                                bio_act['location'] == act['location']
                            ]
                            data['name'] += ', irrigation'
                        else:
                            bio_act_regionalized = [
                                bio_act for bio_act in new_bio_db_water if
                                bio_act['name'] == exc.input['name'] and
                                bio_act['categories'] == exc.input['categories'] and
                                bio_act['location'] == act['location']
                            ]
                        assert len(bio_act_regionalized) == 1
                        bio_act_regionalized = bio_act_regionalized[0]
                        data['input'] = (bio_act_regionalized['database'], bio_act_regionalized['code'])
                        act.new_exchange(**data).save()
                        exc['amount'] = 0
                        exc['replaced with regionalized'] = True
                        exc.save()
                elif exc.input in luluc_list:
                    flag_replaced = exc.get("replaced with regionalized", False)
                    if not flag_replaced:
                        data = deepcopy(exc.as_dict())
                        try:
                            data.pop('flow')
                        except:
                            pass
                        bio_act_regionalized = [
                            bio_act for bio_act in new_bio_db_luc if
                            bio_act['name'] == exc.input['name'] and
                            bio_act['categories'] == exc.input['categories'] and
                            bio_act['location'] == act['location']
                        ]
                        assert len(bio_act_regionalized) == 1
                        bio_act_regionalized = bio_act_regionalized[0]
                        data['input'] = (bio_act_regionalized['database'], bio_act_regionalized['code'])
                        act.new_exchange(**data).save()
                        exc['amount'] = 0
                        exc['replaced with regionalized'] = True
                        exc.save()
        # ei.metadata["regionalized"] = True


def regionalize_db(db_name):
    regionalized_db_name = f'{db_name}_regionalized'
    if regionalized_db_name in list(bd.databases):
        print(f'{regionalized_db_name} already exist. No need to copy from {db_name}.')
    else:
        print(f'start copying {db_name} to {regionalized_db_name}.')
        bd.Database(db_name).copy(regionalized_db_name)
        bio = bd.Database("biosphere3")
        db_to_regionalize = bd.Database(regionalized_db_name)
        new_bio_db_luc = bd.Database('biosphere luluc regionalized')
        new_bio_db_water = bd.Database('biosphere water regionalized')
        # flag_db = ei.metadata.get("regionalized", False)
        # if not flag_db:
        print('start regionalizing water and land flows')
        water_use_list = [act for act in bio if "Water" in act['name']
                          and 'natural resource' in act['categories']
                          and 'air' not in act['name']
                          and 'ocean' not in act['name']
                          and 'ocean' not in act.get('categories')]
        water_emission_list = [act for act in bio if "Water" in act['name']
                               and 'water' in act['categories']
                               and 'ocean' not in act.get('categories')]
        water_list = water_use_list + water_emission_list
        luluc_list = [act for act in bio if ("occupation" in act['name'].lower()
                                             or 'transformation' in act['name'].lower())
                      and 'non-use' not in act['name']
                      and 'obsolete' not in act['name']]
        i = 0
        for act in db_to_regionalize:
            if 'Copied from ecoinvent' not in act.get('name') and \
                    'Evonik' not in act.get('name') and \
                    'Emulsifier, proxy' not in act.get('name'):
                if 'agrifootprint' in db_name:
                    location_pattern = r"\{(.*?)\}"
                    match = re.findall(pattern=location_pattern, string=act['name'])
                    location = match[0]
                else:
                    location = act['location']
                i += 1
                if i % 100 == 0:
                    print(f'updated {str(i)} activities')
                agri_yes_no = check_if_act_is_agri(act)
                for exc in act.exchanges():
                    if exc.input in water_list:
                        flag_replaced = exc.get("replaced with regionalized", False)
                        if not flag_replaced:
                            data = deepcopy(exc.as_dict())
                            try:
                                data.pop('flow')
                            except:
                                pass
                            if agri_yes_no >= 1:
                                exc_name = exc.input['name'] + ', irrigation'
                                bio_act_regionalized = [
                                    bio_act for bio_act in new_bio_db_water if
                                    bio_act['name'] == exc_name and
                                    bio_act['categories'] == exc.input['categories'] and
                                    bio_act['location'] == location
                                ]
                                data['name'] += ', irrigation'
                            else:
                                bio_act_regionalized = [
                                    bio_act for bio_act in new_bio_db_water if
                                    bio_act['name'] == exc.input['name'] and
                                    bio_act['categories'] == exc.input['categories'] and
                                    bio_act['location'] == location
                                ]
                            assert len(bio_act_regionalized) == 1
                            bio_act_regionalized = bio_act_regionalized[0]
                            data['input'] = (bio_act_regionalized['database'], bio_act_regionalized['code'])
                            act.new_exchange(**data).save()
                            exc['amount'] = 0
                            exc['replaced with regionalized'] = True
                            exc.save()
                    elif exc.input in luluc_list:
                        flag_replaced = exc.get("replaced with regionalized", False)
                        if not flag_replaced:
                            data = deepcopy(exc.as_dict())
                            try:
                                data.pop('flow')
                            except:
                                pass
                            bio_act_regionalized = [
                                bio_act for bio_act in new_bio_db_luc if
                                bio_act['name'] == exc.input['name'] and
                                bio_act['categories'] == exc.input['categories'] and
                                bio_act['location'] == location
                            ]
                            assert len(bio_act_regionalized) == 1
                            bio_act_regionalized = bio_act_regionalized[0]
                            data['input'] = (bio_act_regionalized['database'], bio_act_regionalized['code'])
                            act.new_exchange(**data).save()
                            exc['amount'] = 0
                            exc['replaced with regionalized'] = True
                            exc.save()
            # ei.metadata["regionalized"] = True


def bw_scenario_set_up(year, scenario):
    base_project_name = "biomass_basic"
    bd.projects.set_current(base_project_name)
    project_name = f'biomass_{year}_{scenario}'
    project_list = list(bd.projects)
    if project_name not in [x.name for x in project_list]:
        bd.projects.copy_project(project_name)
    else:
        bd.projects.set_current(project_name)
    if scenario == 'scenRCP1p9':
        pathway = 'SSP2-RCP19'
    else:
        pathway = 'SSP2-Base'
    if ('IPCC_AR6', 'GWP_100a', 'all') in list(bd.methods):
        print('IPCC AR6 impact assessment methods already set up.')
    else:
        print('Setting up IPCC AR6 impact assessment methods')
        bw_add_lcia_method_ipcc_ar6()
    ei_name = f'ecoinvent_image_{pathway}_{year}'
    af_name = f"agrifootprint 6 {ei_name}"
    import_premise(year, scenario)
    # regionalize_db(ei_name)
    # import_agrifootprint(ei_name)
    regionalize_db(af_name)
    # create_crop_lci(year, scenario)
    # create_forest_lci(year, scenario)
    # create_chemical_lci(year, scenario)
    # df = lcia_all(year, scenario)
    # bi.backup_project_directory(project_name)
