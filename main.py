import parse_map_methods
import vars

payload = {
    "client_id": vars.client_id,
    "client_secret": vars.client_secret,
    "refresh_token": vars.refresh_token,
    "grant_type": "refresh_token",
    "f": "json",
}

dataset = parse_map_methods.return_activity_dataset(
    vars.auth_url, vars.activities_url, payload
)

polyline = dataset[0]["map"]["summary_polyline"]

basemap = parse_map_methods.create_basemap_from_polyline(polyline)

with open("template.html", "r") as t:
    template = t.read()

formatted_map = parse_map_methods.create_formatted_map_from_template_and_dataset(
    template, dataset, basemap
)

formatted_map.save("src/index.html")
