import requests
import urllib3
import folium
from branca.element import Template, MacroElement
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# STEALING THIS FROM GITHUB (LOL) ----------------------------------------------
# https://github.com/geodav-tech/decode-google-maps-polyline/blob/master/polyline_decoder.py


def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {"latitude": 0, "longitude": 0}
    while index < len(polyline_str):
        for unit in ["latitude", "longitude"]:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            if result & 1:
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = result >> 1
        lat += changes["latitude"]
        lng += changes["longitude"]
        coordinates.append((lat / 100000.0, lng / 100000.0))
    return coordinates


# End STEALING THIS FROM GITHUB (LOL) ------------------------------------------

###

# Requests section -------------------------------------------------------------


def return_activity_dataset(auth_url, activities_url, payload):
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()["access_token"]
    header = {"Authorization": "Bearer " + access_token}
    param = {"per_page": 1, "page": 1}
    activities_dataset = requests.get(
        activities_url, headers=header, params=param
    ).json()
    # Only works for mapped activities, will need to remediate later
    return activities_dataset


# End requests section -------------------------------------------------------


def create_basemap_from_polyline(activity_polyline):
    # activities_dataset[0]["map"]["summary_polyline"] for dataset
    coords_list = decode_polyline(activity_polyline)

    center_coords = (
        sum([coords[0] for coords in coords_list]) / len(coords_list),
        sum([coords[1] for coords in coords_list]) / len(coords_list),
    )
    bounds = [
        [
            min([coords[0] for coords in coords_list]),
            max([coords[1] for coords in coords_list]),
        ],
        [
            max([coords[0] for coords in coords_list]),
            min([coords[1] for coords in coords_list]),
        ],
    ]
    m = folium.Map(
        location=center_coords,
        tiles="CartoDB Voyager",
    )
    m.fit_bounds(bounds)

    # Methods -> https://python-visualization.github.io/folium/latest/user_guide/vector_layers/polyline.html

    return folium.PolyLine(locations=coords_list, color="orange", weight=10).add_to(m)


def create_formatted_map_from_template_and_dataset(template, dataset, map: folium.Map):
    dto = datetime.strptime(dataset[0]["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")
    # STEALING THIS TEMPLATE FROM GITHUB TOO --------------------------------
    # https://nbviewer.org/gist/talbertc-usgs/18f8901fc98f109f2b71156cf3ac81cd
    # https://github.com/python-visualization/folium/issues/528#issuecomment-421445303
    formatted_template = template.format(
        Title=str(dataset[0]["name"]),
        date_time=dto.strftime(format="%m/%d %H:%M"),
        dist=str(float(dataset[0]["distance"]) / 1609)[0:4] + " miles",
        time=str(int(dataset[0]["moving_time"]) // 60)
        + " mins "
        + str(int(dataset[0]["elapsed_time"]) % 60)
        + " secs",
        kudos=dataset[0]["kudos_count"] * "\U0001f44d",
        heart_rate=f"{dataset[0]['average_heartrate']} BPM",
    )
    macro = MacroElement()
    macro._template = Template(formatted_template)

    map.get_root().add_child(macro)

    return map
