import math
import pandas as pd
import plotly.express as px

AIRPORTS_PATH = "../data/airports.csv"


def is_continental_us(lat, lon):
    lat = float(lat)
    lon = float(lon)
    return (24 <= lat <= 49.5) and (-125 <= lon <= -66.5)

def get_airport(df, code):
    rows = df[df["faa"] == code]
    if len(rows) == 0:
        return None
    return rows.iloc[0]


def geodesic_distance(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dphi = lat2 - lat1
    dlambda = lon2 - lon1
    phi_m = (lat1 + lat2) / 2

    part1 = (2 * math.sin(dphi / 2) * math.cos(dlambda / 2)) ** 2
    part2 = (2 * math.cos(phi_m) * math.sin(dlambda / 2)) ** 2

    return R * math.sqrt(part1 + part2)


def plot_route(df, code):
    jfk = get_airport(df, "JFK")
    dest = get_airport(df, code)

    if jfk is None or dest is None:
        print("Airport not found:", code)
        return

    use_us_map = is_continental_us(dest["lat"], dest["lon"])

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        scope="usa" if use_us_map else None,
        title="Route from JFK to " + code
    )

    fig.add_scattergeo(
        lat=[jfk["lat"], dest["lat"]],
        lon=[jfk["lon"], dest["lon"]],
        mode="lines"
    )

    fig.show()


def plot_routes(df, codes):
    jfk = get_airport(df, "JFK")
    if jfk is None:
        print("JFK not found.")
        return

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        title="Multiple routes from JFK"
    )

    for code in codes:
        dest = get_airport(df, code)
        if dest is not None:
            fig.add_scattergeo(
                lat=[jfk["lat"], dest["lat"]],
                lon=[jfk["lon"], dest["lon"]],
                mode="lines",
                name=code
            )

    fig.show()


def main():

    airports = pd.read_csv(AIRPORTS_PATH)

    airports["lat"] = pd.to_numeric(airports["lat"], errors="coerce")
    airports["lon"] = pd.to_numeric(airports["lon"], errors="coerce")
    airports = airports.dropna(subset=["lat", "lon"])

    if "alt" in airports.columns:
        airports["alt"] = pd.to_numeric(airports["alt"], errors="coerce")

    print("Total airports:", len(airports))

  
    fig_world = px.scatter_geo(
        airports,
        lat="lat",
        lon="lon",
        hover_name="name",
        title="World map of airports"
    )
    fig_world.show()

  
    in_us_list = []
    for i in range(len(airports)):
        row = airports.iloc[i]
        in_us_list.append(is_continental_us(row["lat"], row["lon"]))

    airports["in_us"] = in_us_list

    outside = airports[airports["in_us"] == False]
    inside = airports[airports["in_us"] == True]

    fig_outside = px.scatter_geo(
        outside,
        lat="lat",
        lon="lon",
        hover_name="name",
        title="Airports outside US"
    )
    fig_outside.show()

    fig_inside = px.scatter_geo(
        inside,
        lat="lat",
        lon="lon",
        hover_name="name",
        scope="usa",
        title="Airports inside US"
    )
    fig_inside.show()

    if "alt" in airports.columns:
        fig_alt = px.scatter_geo(
            airports.dropna(subset=["alt"]),
            lat="lat",
            lon="lon",
            hover_name="name",
            color="alt",
            title="Airports colored by altitude"
        )
        fig_alt.show()

   
    if "tzone" in airports.columns:
        tz_counts = airports["tzone"].fillna("Unknown").value_counts().reset_index()
        tz_counts.columns = ["tzone", "count"]

        fig_tz = px.bar(
            tz_counts,
            x="tzone",
            y="count",
            title="Number of airports per timezone"
        )
        fig_tz.show()

  
    jfk = get_airport(airports, "JFK")

    if jfk is not None:

        euclid_list = []
        geo_list = []

        for i in range(len(airports)):
            row = airports.iloc[i]

            e = ((row["lat"] - jfk["lat"]) ** 2 +
                 (row["lon"] - jfk["lon"]) ** 2) ** 0.5
            euclid_list.append(e)

       
            g = geodesic_distance(jfk["lat"], jfk["lon"],
                                  row["lat"], row["lon"])
            geo_list.append(g)

        airports["euclidean_dist"] = euclid_list
        airports["geodesic_dist"] = geo_list

        fig_euclid = px.histogram(
            airports,
            x="euclidean_dist",
            nbins=30,
            title="Distribution of Euclidean distances from JFK"
        )
        fig_euclid.show()

        fig_geo = px.histogram(
            airports,
            x="geodesic_dist",
            nbins=30,
            title="Distribution of Geodesic distances from JFK"
        )
        fig_geo.show()


    plot_route(airports, "LAX")
    plot_routes(airports, airports["faa"].head(20).tolist())

if __name__ == "__main__":
    main()