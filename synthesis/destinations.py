import pandas as pd
import numpy as np
import data.spatial.utils


def configure(context):
    context.stage("data.spatial.zones")
    context.stage("data.opportunities.extract_roads_osm")


def execute(context):
    # -----------------------------
    # ZONES
    # -----------------------------
    df_zones = context.stage("data.spatial.zones")

    # -----------------------------
    # OSM OPPORTUNITIES
    # -----------------------------
    df_opportunities = context.stage("data.opportunities.extract_roads_osm")
    df_opportunities = df_opportunities[["x", "y", "purpose"]].copy()

    df_opportunities["offers_work"] = df_opportunities["purpose"].str.contains("work", na=False)
    df_opportunities["offers_other"] = True
    df_opportunities["offers_leisure"] = df_opportunities["purpose"].str.contains("leisure", na=False)
    df_opportunities["offers_shop"] = df_opportunities["purpose"].str.contains("shop", na=False)
    df_opportunities["offers_education"] = False
    df_opportunities["offers_home"] = df_opportunities["purpose"].str.contains("home", na=False)

    df_opportunities = df_opportunities.drop(columns=["purpose"])

    # Geo transform
    df_opportunities = data.spatial.utils.to_gpd(
        df_opportunities, crs={"init": "EPSG:4326"}
    ).to_crs({"init": "EPSG:29183"})

    # -----------------------------
    # EDUCATION (CSV)
    # -----------------------------
    df_education = pd.read_csv(
        "%s/escolas_enderecos.csv" % context.config("data_path"),
        encoding="latin1",
        sep=";"
    )

    # 🔥 Corrige decimal com vírgula
    df_education["LATITUDE"] = df_education["LATITUDE"].astype(str).str.replace(",", ".").astype(float)
    df_education["LONGITUDE"] = df_education["LONGITUDE"].astype(str).str.replace(",", ".").astype(float)

    df_education.rename(columns={"LATITUDE": "y", "LONGITUDE": "x"}, inplace=True)

    df_facilities_education = df_education[["x", "y"]].copy()

    df_facilities_education["offers_work"] = True
    df_facilities_education["offers_other"] = True
    df_facilities_education["offers_leisure"] = False
    df_facilities_education["offers_shop"] = False
    df_facilities_education["offers_education"] = True
    df_facilities_education["offers_home"] = False

    df_facilities_education = data.spatial.utils.to_gpd(
        df_facilities_education, crs={"init": "EPSG:4326"}
    ).to_crs({"init": "EPSG:29183"})

    # -----------------------------
    # MERGE
    # -----------------------------
    df_opportunities = pd.concat(
        [df_opportunities, df_facilities_education],
        ignore_index=True,
        sort=False
    )

    # -----------------------------
    # EXTRACT XY + LOCATION_ID
    # -----------------------------
    df_opportunities["x"] = df_opportunities.geometry.x
    df_opportunities["y"] = df_opportunities.geometry.y
    df_opportunities["location_id"] = np.arange(len(df_opportunities))

    # -----------------------------
    # SPATIAL JOIN (ZONE)
    # -----------------------------
    df_opportunities = data.spatial.utils.impute(
        df_opportunities,
        df_zones,
        "location_id",
        "zone_id",
        fix_by_distance=False
    )

    df_opportunities = df_opportunities.dropna(subset=["zone_id"])

    # -----------------------------
    # 🔥 GARANTIR COBERTURA DE TODAS AS ZONAS
    # -----------------------------
    zones_without_points = set(df_zones["zone_id"]) - set(df_opportunities["zone_id"])

    if len(zones_without_points) > 0:
        print("Fixing zones without opportunities:", len(zones_without_points))

        fallback = df_zones[df_zones["zone_id"].isin(zones_without_points)].copy()

        # usa centroide da zona
        fallback["geometry"] = fallback["geometry"].centroid

        fallback["x"] = fallback.geometry.x
        fallback["y"] = fallback.geometry.y

        # todas as categorias ativas (fallback genérico)
        fallback["offers_work"] = True
        fallback["offers_other"] = True
        fallback["offers_leisure"] = True
        fallback["offers_shop"] = True
        fallback["offers_education"] = True
        fallback["offers_home"] = True

        fallback["location_id"] = np.arange(len(fallback)) + df_opportunities["location_id"].max() + 1

        df_opportunities = pd.concat([df_opportunities, fallback], ignore_index=True)

    # -----------------------------
    # FINAL
    # -----------------------------
    return df_opportunities

