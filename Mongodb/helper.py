import pycountry

def get_country_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3.upper()
    except LookupError:
        return None
