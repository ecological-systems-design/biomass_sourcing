import pandas as pd


def get_country_match_df():
    df_country = pd.read_excel(r'data/raw_data/Country.xlsx', engine='openpyxl', sheet_name='Sheet1')
    df_country.loc[df_country.Country == "Namibia", "ISO2"] = "NA"
    return df_country


def get_country_match_df_globiom():
    df_country = get_country_match_df()
    df_country_unique = df_country.drop_duplicates(subset='GLOBIOM', keep='first')
    return df_country_unique
