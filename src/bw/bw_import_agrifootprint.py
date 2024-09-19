import bw2data as bd
import bw2io as bi
import json
import re


location_pattern = r"\{(.*?)\}"


def change_ei_name(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if (
                "ecoinvent" in exc.get('name')
                and 'production' not in exc.get('type')
            ):
                if 'Saw dust' in exc.get('name'):
                    act_name = 'market for sawdust, wet, measured as dry mass'
                    location = 'RoW'
                else:
                    x = exc['name'].split("| ")
                    match = re.findall(pattern=location_pattern, string=exc['name'])
                    location = match[0]
                    if (
                        x[1] == "market for "
                        or x[1] == "market group for "
                       ):
                        x1 = x[0].split(" {")
                        act_name = f"{x[1]}{x1[0].lower()}"
                    else:
                        act_name = x[1].rstrip()
                exc['name'] = act_name
                exc['location'] = location
    return db


def unit_exchange_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if (
                "heat production" in exc.get('name')
                and "kilowatt hour" == exc.get('unit')
            ):
                exc['unit'] = "megajoule"
                exc['amount'] *= 3.6
                exc['loc'] *= 3.6
            elif (
                "electricity, low voltage" in exc.get('name')
                and "megajoule" == exc.get('unit')
            ):
                exc['unit'] = "kilowatt hour"
                exc['amount'] /= 3.6
                exc['loc'] /= 3.6
            elif (
                'market for wastewater' in exc.get('name')
                and 'litre' == exc.get('unit')
            ):
                exc['unit'] = "cubic meter"
                exc['amount'] *= 0.001
                exc['loc'] *= 0.001
    return db


# Change names to contain "in ground"
def change_in_ground_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if (
                    exc.get('type') == 'biosphere'
                    and "in ground" in exc.get('categories')
                    and " " not in exc.get('name')
                    and "in ground" not in exc.get('name')
            ):
                exc['name'] += ", in ground"
    return db


# add "in ground" to "categories"
def change_in_ground_categories_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if (
                    exc.get('type') == 'biosphere'
                    and "in ground" in exc.get('name')
                    and ('natural resource',) == exc.get('categories')
            ):
                exc['categories'] = ('natural resource', 'in ground')
    return db


# change names of unlinked containing "water"
def change_water_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if exc.get('type') == 'biosphere' and "Water, " in exc.get('name'):
                x = exc['name'].split(", ")
                exc_name = f"{x[0]}, {x[1]}"
                if "Water, cooling" in exc_name:
                    exc['name'] = 'Water, cooling, unspecified natural origin'
                    exc['categories'] = ('natural resource', 'in water')
                    if exc['unit'] == "kilogram":
                        exc['amount'] /= 1000
                        exc['unit'] = 'cubic meter'
                elif "Water, turbine use" in exc_name:
                    exc['name'] = 'Water, turbine use, unspecified natural origin'
                    exc['categories'] = ('natural resource', 'in water')
                elif "Water, river" in exc_name or "Water, lake" in exc_name:
                    exc['name'] = exc_name
                    exc['categories'] = ('natural resource', 'in water')
                elif "Water, well" in exc_name:
                    exc['name'] = 'Water, well, in ground'
                    exc['categories'] = ('natural resource', 'in water')
                elif "Water, salt" in exc_name:
                    exc['name'] = 'Water, salt, ocean'
                    exc['categories'] = ('natural resource', 'in water')
                elif exc_name in ['Water, BR-Mid-western grid',
                                  'Water, BR-South-eastern grid',
                                  'Water, Europe without Austria',
                                  'Water, Europe without Switzerland and Austria',
                                  'Water, RER w/o RU',
                                  'Water, unspecified natural origin',
                                  'Water, fresh']:
                    exc['name'] = 'Water, unspecified natural origin'
                    exc['categories'] = ('natural resource', 'in water')
                    if exc['unit'] == "litre":
                        exc['amount'] /= 1000
                        exc['unit'] = 'cubic meter'
    return db


# change names of unlinked containing "nitrogen"
def change_nitrogen_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if exc.get('type') == 'biosphere':
                if (
                        "Nitrogen, atmospheric" in exc.get('name')
                        or "Nitrogen, total" in exc.get('name')
                ):
                    exc['name'] = "Nitrogen"
                elif (
                        "Nitrogen dioxide" in exc.get('name')
                        and exc.get('categories') == ('water', 'ground-')
                ):
                    exc['name'] = "Nitrogen dioxide"
                    exc['categories'] = ('water', 'surface water')
                elif (
                        "Nitrogen monoxide" in exc.get('name')
                        or "Nitrogen oxides" in exc.get('name')
                        or "Nitrogen dioxide" in exc.get('name')
                ):
                    exc['name'] = "Nitrogen oxides"
                elif (
                        "Nitrogen, NO" in exc.get('name')
                        or "Nitrogenous Matter (unspecified, as N)" in exc.get('name')
                ):
                    exc['name'] = "Nitrogen"
    return db


# Change names to contain "NMVOC"
def change_nmvoc_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            exc_name = exc.get('name')
            if (
                    exc.get('type') == 'biosphere'
                    and "NMVOC" in exc_name
                    and ", unspecified origin" not in exc_name
            ):
                exc['name'] += ", unspecified origin"
    return db


# remove locations
def change_remove_location_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            exc_name = exc.get('name')
            if (
                    exc.get('type') == 'biosphere'
                    and ',' in exc_name
                    and ('Ammonia' in exc_name
                         or 'Nitrate' in exc_name
                         or 'Phosphorus' in exc_name
                         or 'Sulfur dioxide' in exc_name)
            ):
                x = exc_name.split(", ")
                exc['name'] = x[0]
    return db


# rename PMs
def change_pm_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            exc_name = exc.get('name')
            if (
                    exc.get('type') == 'biosphere'
                    and exc_name in ['Particulates, < 10 um', 'Particulates, SPM', 'Particulates, unspecified']
            ):
                exc['name'] = 'Particulates, > 2.5 um, and < 10um'
    return db


# remove peat oxidation
def change_remove_peat_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            exc_name = exc.get('name')
            if (
                    exc.get('type') == 'biosphere'
                    and ', peat oxidation' in exc.get('name')
            ):
                x = exc_name.split(", ")
                exc['name'] = x[0]
    return db


# LUC
def change_luc_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            exc_name = exc.get('name')
            if exc.get('type') == 'biosphere':
                if (
                        'land' not in exc.get('categories')
                        and ('Transformation,' in exc.get('name')
                             or 'Occupation,' in exc.get('name'))
                ):
                    exc['categories'] = ('natural resource', 'land')
                if (
                        'Transformation, to annual crop' in exc_name
                        or 'Transformation, to permanent crop' in exc_name
                        or 'Transformation, to grassland/pasture/meadow' in exc_name
                        or 'Transformation, from annual crop' in exc_name
                        or 'Transformation, from permanent crop' in exc_name
                        or 'Transformation, from grassland/pasture/meadow' in exc_name
                        or 'Occupation, permanent crop' in exc_name
                        or 'Occupation, annual crop' in exc_name
                        or 'Occupation, grassland/pasture/meadow' in exc_name
                ):
                    x = exc_name.split(", ")
                    exc['name'] = f"{x[0]}, {x[1]}"
                elif 'Transformation, from forest, extensive' in exc_name:
                    x = exc_name.split(", ")
                    exc['name'] = f"{x[0]}, {x[1]}, {x[2]}"
    return db


# energy
def change_energy_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            exc_name = exc.get('name')
            if exc.get('type') == 'biosphere':
                if (
                        'Energy, potential (in hydropower reservoir), converted' == exc_name
                        or 'Energy, from hydro power' == exc_name
                ):
                    exc['categories'] = ('natural resource', 'in water')
                    exc['name'] = 'Energy, potential (in hydropower reservoir), converted'
                elif 'Energy, from biomass' == exc_name:
                    exc['categories'] = ('natural resource', 'biotic')
                    exc['name'] = 'Energy, gross calorific value, in biomass'
                elif 'Energy, from wood' == exc_name:
                    exc['categories'] = ('natural resource', 'biotic')
                    exc['name'] = 'Energy, gross calorific value, in biomass, primary forest'
    return db


# add elements to categories
def change_add_elements_categories_acts(db, soil_check_list, water_check_list, air_check_list):
    for act in db.data:
        for exc in act.get('exchanges'):
            if exc.get('type') == 'biosphere':
                if (
                        ('soil',) == exc.get('categories')
                        and exc.get('name') in soil_check_list
                ):
                    exc['categories'] = ('soil', 'agricultural')
                elif (
                        ('water',) == exc.get('categories')
                        and exc.get('name') in water_check_list
                ):
                    exc['categories'] = ('water', 'surface water')
                elif (
                        ('air',) == exc.get('categories')
                        and exc.get('name') in air_check_list
                ):
                    exc['categories'] = ('air', 'non-urban air or from high stacks')
    return db


def change_categories_acts(db):
    for act in db.data:
        for exc in act.get('exchanges'):
            if exc.get('type') == 'biosphere':
                if (
                        'Magnesium, 0.13% in water' == exc.get('name')
                        and ('natural resource', 'in ground') == exc.get('categories')
                ):
                    exc['categories'] = ('natural resource', 'in water')
                elif (
                        'Wood, soft, standing' == exc.get('name')
                        and ('natural resource', 'in ground') == exc.get('categories')
                ):
                    exc['categories'] = ('natural resource', 'biotic')
                elif (
                        'Fish' in exc.get('name')
                        and ('natural resource', 'in water') == exc.get('categories')
                ):
                    exc['categories'] = ('natural resource', 'biotic')
                elif (
                        'Methane' == exc.get('name')
                        and ('air',) == exc.get('categories')
                ):
                    exc['categories'] = ('air', 'urban air close to ground')
                elif (
                        'Phosphorus' == exc.get('name')
                        and ('natural resource',) == exc.get('categories')
                ):
                    exc['categories'] = ('natural resource', 'in ground')
                    exc['name'] = 'Phosphorus, in ground'
                elif (
                        'Pyraclostrobin (prop)' == exc.get('name')
                        and 'water' in exc.get('categories')
                ):
                    exc['name'] = 'Pyraclostrobin'
                elif (
                        'Sylvite, 25 % in sylvinite, in ground' == exc.get('name')
                        and ('natural resource',) == exc.get('categories')
                ):
                    exc['categories'] = ('natural resource', 'in ground')
                elif (
                        'Hydrochloric acid' == exc.get('name')
                        and 'water' in exc.get('categories')
                ):
                    exc['categories'] = ('water',)
                elif (
                        exc.get('name') in ['Nitrate', 'Chlorine', 'PAH, polycyclic aromatic hydrocarbons',
                                            'Sulfate']
                        and 'soil' in exc.get('categories')
                ):
                    exc['categories'] = ('soil',)
                elif (
                        exc.get('name') in ['Azoxystrobin', 'Metribuzin', 'Diquat dibromide',
                                            'Chlorpyrifos', 'Imidacloprid']
                        and 'water' in exc.get('categories')
                ):
                    exc['categories'] = ('water', 'ground-')

    return db


def write_unlinked_biosphere(db):
    ag_bio_name = "biosphere agrifootprint unlinked"
    try:
        del bd.databases[ag_bio_name]
    except:
        pass
    bd.Database(ag_bio_name).register()
    db.add_unlinked_flows_to_biosphere_database(ag_bio_name)


def import_agrifootprint(ei_name):
    bio = bd.Database("biosphere3")
    regionalized_db_name = f'{ei_name}_regionalized'
    af_path = "data/external/Agrifootprint6_economic.csv"
    af_name = f"agrifootprint 6 {ei_name}"
    if af_name in bd.databases:
        print(f'{af_name} is already imported.')
    else:
        print(f'start importing {af_name}.')
        af = bi.SimaProCSVImporter(
            filepath=af_path,
            name=af_name,
            delimiter=",",
        )
        soil_agri_list = [act['name'] for act in bio if "agricultural" in act['categories']]
        soil_list = [act['name'] for act in bio if ('soil',) == act['categories']]
        soil_check_list = [x for x in soil_agri_list if x not in soil_list]
        water_surface_list = [act['name'] for act in bio if "surface water" in act['categories']]
        water_list = [act['name'] for act in bio if ('water',) == act['categories']]
        water_check_list = [x for x in water_surface_list if x not in water_list]
        air_high_list = [act['name'] for act in bio if "non-urban air or from high stacks" in act['categories']]
        air_list = [act['name'] for act in bio if ('air',) == act['categories']]
        air_check_list = [x for x in air_high_list if x not in air_list]
        migration_name = "agrifootprint-6-names"
        bi.Migration(migration_name).write(
            json.load(open("data/raw_data/Agrifootprint_6_economic.json")),
            "Change names of agrifootprint activities",
        )

        af = change_ei_name(af)
        af.apply_strategies()
        af = unit_exchange_acts(af)
        af.match_database(regionalized_db_name, fields=("name", "unit", "location"))
        af.match_database("biosphere3", fields=("name", "unit", "categories"))
        af.migrate(migration_name)
        af = change_in_ground_acts(af)
        af = change_in_ground_categories_acts(af)
        af = change_water_acts(af)
        af = change_nitrogen_acts(af)
        af = change_nmvoc_acts(af)
        af = change_remove_location_acts(af)
        af = change_pm_acts(af)
        af = change_remove_peat_acts(af)
        af = change_luc_acts(af)
        af = change_energy_acts(af)
        af = change_categories_acts(af)
        af = change_add_elements_categories_acts(af, soil_check_list, water_check_list, air_check_list)
        af.migrate(migration_name)
        af.match_database("biosphere3", fields=("name", "unit", "categories"))
        write_unlinked_biosphere(af)
        af.match_database("biosphere agrifootprint unlinked", fields=("name", "unit", "categories"))
        af.drop_unlinked(i_am_reckless=True)
        af.write_database()
