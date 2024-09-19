import numpy as np
from matplotlib.colors import ListedColormap

from src.other.name_match import residue_list_short

color6_old = ["#6ab33f", "#f2e18b", "#c96420", "#00625a", "#c69b58", '#d8d8d8']

color_for_map = ["#6ab33f", "#f2e18b", "#c96420", "#00625a", "#c69b58", '#9A9EAB']

color_contribution_old = ["#416831", "#6ab33f", "#b3cd7d", "#d9e5c1", "#f2e18b",
                          "#c96420", "#00625a", "#c69b58", '#d8d8d8']

color6 = ["#838bc0", "#bdce37", "#f9eba2", "#53833b", "#40419a", '#d8d8d8']

color6_r = ['#40419a', '#53833b', '#f9eba2', '#bdce37', '#838bc0', '#d8d8d8']

color6_2 = ["#838bc0", '#b84426', "#bdce37", "#40419a", '#f9eba2', '#d8d8d8']

color_contribution_old2 = ["#53833b", "#7c9d63", "#b1c09c", "#d1d9c4",
                           "#f9eba2", "#40419a", "#bdce37", "#838bc0", '#d8d8d8']

color_contribution = ["#53833b", "#6ab33f", "#f9eba2", "#ecf1cd",
                      "#40419a", "#b84426", "#bdce37", "#838bc0", '#d8d8d8']

color_purple = ["#40419a", "#838bc0", "#b6b8d9"]

color_dict_residue = dict(zip(residue_list_short, color6_old))


def color_sankey(opacity=1):
    color_dict = {'Biomass feedstock': f'rgba(65, 104, 49, {opacity})',
                   'Chemical': f'rgba(198, 155, 88, {opacity})',
                   'Electricity': f'rgba(106, 179, 63, {opacity})',
                   'Fuel': f'rgba(178, 205, 126, {opacity})',
                   'Onsite': f'rgba(73, 126, 120, {opacity})',
                   'Other': f'rgba(216, 216, 216, {opacity})',
                   'Compressed air': f'rgba(201, 100, 32, {opacity})',
                   'Other chemicals': f'rgba(242, 225, 139, {opacity})',
                   'Others': f'rgba(216, 216, 216, {opacity})',
                   'Propanol': f'rgba(251, 243, 207, {opacity})',
                   'Biomass fractionation': f'rgba(217, 229, 193, {opacity})'}
    return color_dict


def cmp_green_yellow_orange():
    vals = np.ones((256, 4))
    green_d = [83/256, 131/256, 59/256]
    green_l = [189/256, 206/256, 55/256]
    yellow = [249/256, 235/256, 162/256]
    orange = [184/256, 68/256, 38/256]
    a = 75
    b = 256 - a * 2
    vals[:, 0] = np.concatenate((np.linspace(green_d[0], green_l[0], a),
                                 np.linspace(green_l[0], yellow[0], a),
                                 np.linspace(yellow[0], orange[0], b)))
    vals[:, 1] = np.concatenate((np.linspace(green_d[1], green_l[1], a),
                                 np.linspace(green_l[1], yellow[1], a),
                                 np.linspace(yellow[1], orange[1], b)))
    vals[:, 2] = np.concatenate((np.linspace(green_d[2], green_l[2], a),
                                 np.linspace(green_l[2], yellow[2], a),
                                 np.linspace(yellow[2], orange[2], b)))
    newcmp = ListedColormap(vals)
    return newcmp


def cmp_yellow_green():
    vals = np.ones((256, 4))
    vals[:, 0] = np.concatenate((np.linspace(251/256,247/256, 50),
                                 np.linspace(247/256,191/256, 50),
                                 np.linspace(191/256,65/256,156)))
    vals[:, 1] = np.concatenate((np.linspace(243/256,233/256, 50),
                                 np.linspace(233/256,212/256, 50),
                                 np.linspace(212/256,104/256, 156)))
    vals[:, 2] = np.concatenate((np.linspace(207/256,164/256, 50),
                                 np.linspace(164/256,148/256, 50),
                                 np.linspace(148/256,49/256, 156)))
    newcmp = ListedColormap(vals)
    return newcmp


def cmp_yellow_orange():
    vals = np.ones((256, 4))
    vals[:, 0] = np.concatenate((np.linspace(251 / 256, 242 / 256, 100),
                                 np.linspace(242 / 256, 201 / 256, 156)))
    vals[:, 1] = np.concatenate((np.linspace(243 / 256, 225 / 256, 100),
                                 np.linspace(225 / 256, 100 / 256, 156)))
    vals[:, 2] = np.concatenate((np.linspace(207 / 256, 139 / 256, 100),
                                 np.linspace(139 / 256, 32 / 256, 156)))

    newcmp = ListedColormap(vals)
    return newcmp


from colorsys import rgb_to_hsv, hsv_to_rgb


def hex_to_rgb(hex_color):
    """ Convert hex color to RGB. """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_color):
    """ Convert RGB color to hex. """
    return '#{:02x}{:02x}{:02x}'.format(*rgb_color)


def adjust_color(color, factor):
    """ Adjust the color brightness. """
    rgb = hex_to_rgb(color)
    hsv = rgb_to_hsv(*[x/255.0 for x in rgb])
    new_hsv = (hsv[0], hsv[1], max(0, min(1, hsv[2] * factor)))
    new_rgb = [int(x * 255) for x in hsv_to_rgb(*new_hsv)]
    return rgb_to_hex(new_rgb)


def diverging_colors():
    # Adjust each base color to create 5 diverging colors
    diverging_colors = []
    factors1 = [0.4, 0.6, 0.8, 1, 1.1, 1.2]
    factors2 = [0.4, 0.55, 0.7, 0.85, 1, 1.1, 1.3]# Factors to adjust brightness
    for color in color_for_map:
        if color == color_for_map[0]:
            factors = factors2
        else:
            factors = factors1
        for factor in factors:
            diverging_colors.append(adjust_color(color, factor))
    return diverging_colors


color37 = ['#355a1f',
 '#47772a',
 '#589534',
 '#6ab33f',
 '#7cd14a',
 '#8def54',
 '#97ff5a',
 '#797046',
 '#a1965d',
 '#cabb74',
 '#f2e18b',
 '#ffed92',
 '#643210',
 '#864315',
 '#a7531b',
 '#c96420',
 '#ea7525',
 '#ff7f29',
 '#00312d',
 '#00413c',
 '#00524b',
 '#00625a',
 '#007269',
 '#008378',
 '#009387',
 '#634d2c',
 '#84673b',
 '#a58149',
 '#c69b58',
 '#e7b567',
 '#ffc871',
 '#4d4f56',
 '#676972',
 '#80848e',
 '#9a9eab',
 '#b4b8c7',
 '#cdd3e4']