from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import by_product, by_year, outlier_rows, product_by_year, top_zips, zip_product_summary
from src.clean_data import clean_foundation_data
from src.geo import add_zip_centroids
from src.load_data import DATA_PATH, load_foundation_data
from src.metrics import build_metrics

st.set_page_config(
    page_title="Blackhawks Foundation Ticket Dashboard",
    page_icon="🏒",
    layout="wide",
)


@st.cache_data(show_spinner="Loading Blackhawks foundation data…")
def get_data(path: str) -> pd.DataFrame:
    cleaned = clean_foundation_data(load_foundation_data(Path(path)))
    return add_zip_centroids(cleaned)


def fmt_int(value: int | float) -> str:
    return f"{value:,.0f}"


def fmt_float(value: int | float) -> str:
    return f"{value:,.1f}"


def weighted_zip_map_data(df: pd.DataFrame) -> pd.DataFrame:
    # Collapse to ZIP, keeping centroid metadata.
    group = (
        df.groupby(["POSTAL_CODE", "place_name", "state_code", "county_name", "latitude", "longitude"], dropna=False, as_index=False)
        .agg(TOTAL_SEATS=("TOTAL_SEATS", "sum"), TOTAL_ACCOUNTS=("TOTAL_ACCOUNTS", "sum"), ROWS=("POSTAL_CODE", "size"))
    )
    group["SEATS_PER_ACCOUNT"] = group["TOTAL_SEATS"] / group["TOTAL_ACCOUNTS"].where(group["TOTAL_ACCOUNTS"] != 0, pd.NA)

    # Raw metrics are very skewed. Percentiles and log values make hotspot-style
    # comparisons less likely to collapse into one huge outlier.
    for col in ["TOTAL_SEATS", "TOTAL_ACCOUNTS", "SEATS_PER_ACCOUNT"]:
        safe = group[col].fillna(0).clip(lower=0)
        group[f"{col}_PERCENTILE"] = safe.rank(pct=True, method="max") * 100
        group[f"LOG_{col}"] = safe.apply(lambda x: pd.NA if pd.isna(x) else __import__("math").log10(x + 1))

    return group.dropna(subset=["latitude", "longitude"])


def main() -> None:
    st.markdown(
        """
        <style>
        .bh-hero {
            display: flex;
            align-items: center;
            gap: 1.25rem;
            padding: 1.1rem 1.25rem;
            border-radius: 16px;
            background: linear-gradient(135deg, #000000 0%, #1A1A1A 48%, #CF0A2C 100%);
            border: 1px solid #CF0A2C;
            margin-bottom: 1rem;
        }
        .bh-logo {
            width: 96px;
            min-width: 96px;
            background: white;
            border-radius: 999px;
            padding: 8px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.35);
        }
        .bh-title {
            color: #FFFFFF;
            font-size: 2.25rem;
            font-weight: 800;
            line-height: 1.05;
            margin: 0;
        }
        .bh-subtitle {
            color: #F5D36B;
            font-size: 1rem;
            margin-top: 0.35rem;
        }
        div[data-testid="stMetric"] {
            background: #151515;
            border: 1px solid #333333;
            border-left: 5px solid #CF0A2C;
            padding: 0.75rem;
            border-radius: 12px;
        }
        div[data-testid="stMetricLabel"] p {
            color: #F5D36B;
        }
        </style>
        <div class="bh-hero">
            <img class="bh-logo" src="https://upload.wikimedia.org/wikipedia/en/2/29/Chicago_Blackhawks_logo.svg" alt="Chicago Blackhawks logo">
            <div>
                <div class="bh-title">Blackhawks Foundation Ticket Dashboard</div>
                <div class="bh-subtitle">Ticket seats/accounts by season year, ZIP code, and product type</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not DATA_PATH.exists():
        st.error(f"Could not find data file: {DATA_PATH}")
        return

    df = get_data(str(DATA_PATH))

    with st.sidebar:
        st.header("Filters")
        years = sorted(df["SEASON_YEAR"].dropna().astype(int).unique().tolist())
        products = sorted(df["PRODUCT_TYPE"].dropna().astype(str).unique().tolist())

        selected_years = st.multiselect("Season year", years, default=years)
        selected_products = st.multiselect("Product type", products, default=products)
        zip_search = st.text_input(
            "ZIP code or prefix",
            placeholder="Examples: 606 for Chicago-area ZIPs, 60614 for one ZIP",
            help="Optional. Enter 5 digits for one exact ZIP code, or fewer digits to match ZIPs that start with that prefix. Leave blank to include all ZIPs.",
        )
        st.caption("Leave blank for all ZIPs. `606` = ZIPs starting with 606. `60614` = exact ZIP 60614.")

    filtered = df[
        df["SEASON_YEAR"].astype(int).isin(selected_years)
        & df["PRODUCT_TYPE"].isin(selected_products)
    ].copy()
    if zip_search.strip():
        zip_query = "".join(ch for ch in zip_search.strip() if ch.isdigit())
        if len(zip_query) >= 5:
            zip_query = zip_query[:5]
            filtered = filtered[filtered["POSTAL_CODE"].astype(str) == zip_query]
            st.sidebar.caption(f"Exact ZIP filter active: `{zip_query}`")
        elif zip_query:
            filtered = filtered[filtered["POSTAL_CODE"].astype(str).str.startswith(zip_query, na=False)]
            st.sidebar.caption(f"ZIP prefix filter active: `{zip_query}`")
        else:
            st.sidebar.warning("ZIP filter ignored because it does not contain digits.")

    top_n = 25
    metrics = build_metrics(filtered)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows", fmt_int(metrics["rows"]))
    c2.metric("ZIPs", fmt_int(metrics["zip_count"]))
    c3.metric("Total seats", fmt_int(metrics["total_seats"]))
    c4.metric("Total accounts", fmt_int(metrics["total_accounts"]))
    c5.metric("Seats / account", fmt_float(metrics["seats_per_account"]))

    st.info(
        "Working assumption to verify: for season products, `TOTAL_SEATS` likely means ticketed seat-events across the package/season, not unique physical seats."
    )

    if filtered.empty:
        st.warning("No rows match the current filters.")
        return

    tab_map, tab_overview, tab_zips, tab_outliers, tab_data = st.tabs(
        ["ZIP map", "Overview", "ZIP analysis", "Outliers / QA", "Data"]
    )

    with tab_overview:
        product_summary = by_product(filtered)
        year_summary = by_year(filtered)
        product_year = product_by_year(filtered)

        left, right = st.columns(2)
        with left:
            st.subheader("Seats by product type")
            fig = px.bar(
                product_summary,
                x="PRODUCT_TYPE",
                y="TOTAL_SEATS",
                color="PRODUCT_TYPE",
                text="TOTAL_SEATS",
                hover_data=["TOTAL_ACCOUNTS", "SEATS_PER_ACCOUNT", "ROWS"],
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total seats")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Accounts by product type")
            fig = px.bar(
                product_summary,
                x="PRODUCT_TYPE",
                y="TOTAL_ACCOUNTS",
                color="PRODUCT_TYPE",
                text="TOTAL_ACCOUNTS",
                hover_data=["TOTAL_SEATS", "SEATS_PER_ACCOUNT", "ROWS"],
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total accounts")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Product mix by season")
        fig = px.bar(
            product_year,
            x="SEASON_YEAR",
            y="TOTAL_SEATS",
            color="PRODUCT_TYPE",
            barmode="stack",
            hover_data=["TOTAL_ACCOUNTS", "SEATS_PER_ACCOUNT"],
            labels={"SEASON_YEAR": "Season year", "TOTAL_SEATS": "Total seats"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Summary tables")
        t1, t2 = st.columns(2)
        t1.dataframe(product_summary, use_container_width=True, hide_index=True)
        t2.dataframe(year_summary, use_container_width=True, hide_index=True)

    with tab_map:
        st.subheader("Approximate ZIP centroid map")
        st.caption("This uses ZIP centroid coordinates, not ZIP boundary polygons. Good for quick exploration; a true choropleth can come next.")
        map_metric = st.radio("Map metric", ["TOTAL_SEATS", "TOTAL_ACCOUNTS", "SEATS_PER_ACCOUNT"], horizontal=True)
        color_mode = "Percentile hotspot"
        map_df = weighted_zip_map_data(filtered)
        if map_df.empty:
            st.warning("No ZIP centroid coordinates available for the current filters. Try installing requirements with `pip install -r requirements.txt`.")
        else:
            color_col = f"{map_metric}_PERCENTILE"
            color_label = f"{map_metric.replace('_', ' ').title()} hotspot score"
            size_col = "TOTAL_ACCOUNTS" if map_metric == "SEATS_PER_ACCOUNT" else map_metric
            st.caption(
                "Darker red means the ZIP ranks higher for the selected metric among the currently filtered ZIPs. For seats/account, use the hotspot table below to sanity-check tiny-account ZIPs."
            )

            if zip_search.strip():
                map_center = {
                    "lat": float(map_df["latitude"].mean()),
                    "lon": float(map_df["longitude"].mean()),
                }
                unique_map_zips = map_df["POSTAL_CODE"].nunique()
                lat_span = float(map_df["latitude"].max() - map_df["latitude"].min()) if unique_map_zips > 1 else 0
                lon_span = float(map_df["longitude"].max() - map_df["longitude"].min()) if unique_map_zips > 1 else 0
                max_span = max(lat_span, lon_span)
                if unique_map_zips == 1:
                    map_zoom = 12
                elif max_span < 0.35:
                    map_zoom = 9
                elif max_span < 0.8:
                    map_zoom = 8
                elif max_span < 1.8:
                    map_zoom = 7
                else:
                    map_zoom = 5
                st.caption(f"Map focused on {unique_map_zips:,} matching ZIP code(s).")
            else:
                map_center = {"lat": 41.8781, "lon": -87.6298}
                map_zoom = 8

            fig = px.scatter_map(
                map_df,
                lat="latitude",
                lon="longitude",
                size=size_col,
                color=color_col,
                hover_name="POSTAL_CODE",
                hover_data={
                    "place_name": True,
                    "county_name": True,
                    "TOTAL_SEATS": ":,",
                    "TOTAL_ACCOUNTS": ":,",
                    "SEATS_PER_ACCOUNT": ":.1f",
                    f"{map_metric}_PERCENTILE": ":.1f",
                    "latitude": False,
                    "longitude": False,
                },
                labels={color_col: color_label},
                center=map_center,
                zoom=map_zoom,
                height=650,
                color_continuous_scale="Reds",
                range_color=(0, 100),
            )
            fig.update_layout(map_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Top map hotspots")
            hotspot_cols = [
                "POSTAL_CODE",
                "place_name",
                "county_name",
                "TOTAL_SEATS",
                "TOTAL_ACCOUNTS",
                "SEATS_PER_ACCOUNT",
                f"{map_metric}_PERCENTILE",
            ]
            st.dataframe(
                map_df.sort_values(map_metric, ascending=False)[hotspot_cols].head(top_n),
                use_container_width=True,
                hide_index=True,
            )

    with tab_zips:
        st.subheader("ZIP market concentration")
        st.caption(
            "ZIP codes are treated as categorical market areas. This view focuses on ranking, contribution, and concentration — not numeric ZIP-code trends."
        )

        zip_all = top_zips(filtered, metric="TOTAL_SEATS", limit=max(top_n, 100000))
        zip_all = zip_all.sort_values("TOTAL_SEATS", ascending=False).reset_index(drop=True)
        zip_all["RANK_BY_SEATS"] = zip_all.index + 1
        zip_all["SEAT_SHARE"] = zip_all["TOTAL_SEATS"] / zip_all["TOTAL_SEATS"].sum()
        zip_all["ACCOUNT_SHARE"] = zip_all["TOTAL_ACCOUNTS"] / zip_all["TOTAL_ACCOUNTS"].sum()
        zip_all["CUMULATIVE_SEAT_SHARE"] = zip_all["SEAT_SHARE"].cumsum()

        top_by_seats = zip_all.head(top_n)
        top_by_accounts = top_zips(filtered, metric="TOTAL_ACCOUNTS", limit=top_n)
        top_by_rate = top_zips(filtered[filtered["TOTAL_ACCOUNTS"] >= 5], metric="SEATS_PER_ACCOUNT", limit=top_n)

        concentration_cols = st.columns(4)
        concentration_cols[0].metric("Top ZIP", str(top_by_seats.iloc[0]["POSTAL_CODE"]))
        concentration_cols[1].metric("Top ZIP seat share", f"{top_by_seats.iloc[0]['SEAT_SHARE']:.1%}")
        concentration_cols[2].metric("Top 10 seat share", f"{zip_all.head(10)['SEAT_SHARE'].sum():.1%}")
        concentration_cols[3].metric("ZIPs for 80% of seats", fmt_int((zip_all["CUMULATIVE_SEAT_SHARE"] <= 0.80).sum() + 1))

        st.markdown("**Seat contribution by top ZIPs**")
        treemap_df = top_by_seats.copy()
        treemap_df["ZIP"] = treemap_df["POSTAL_CODE"].astype(str)
        fig = px.treemap(
            treemap_df,
            path=["ZIP"],
            values="TOTAL_SEATS",
            color="SEAT_SHARE",
            color_continuous_scale="Reds",
            hover_data={
                "TOTAL_SEATS": ":,",
                "TOTAL_ACCOUNTS": ":,",
                "SEATS_PER_ACCOUNT": ":.1f",
                "SEAT_SHARE": ":.1%",
            },
        )
        fig.update_traces(textinfo="label+value+percent parent")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Ranked ZIP tables")
        t1, t2, t3 = st.tabs(["By seat contribution", "By account contribution", "By seats/account"])
        with t1:
            cols = ["RANK_BY_SEATS", "POSTAL_CODE", "TOTAL_SEATS", "SEAT_SHARE", "TOTAL_ACCOUNTS", "SEATS_PER_ACCOUNT"]
            st.dataframe(
                top_by_seats[cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "SEAT_SHARE": st.column_config.NumberColumn("Seat share", format="%.1f%%"),
                },
            )
        with t2:
            st.dataframe(top_by_accounts, use_container_width=True, hide_index=True)
        with t3:
            st.caption("Requires at least 5 accounts so one-off tiny ZIPs do not dominate.")
            st.dataframe(top_by_rate, use_container_width=True, hide_index=True)

        st.subheader("ZIP × product breakdown")
        st.caption("Categorical drilldown by ZIP and ticket product.")
        zp = zip_product_summary(filtered)
        st.dataframe(zp.head(500), use_container_width=True, hide_index=True)

    with tab_outliers:
        st.subheader("Business QA overview")
        st.caption("Use these visuals to spot unusually concentrated rows or product types that may need definition checks.")

        hist_df = filtered[filtered["TOTAL_ACCOUNTS"] > 0].copy()
        q1, q2 = st.columns(2)
        with q1:
            st.markdown("**Seats per account by product type**")
            fig = px.box(
                hist_df,
                x="PRODUCT_TYPE",
                y="SEATS_PER_ACCOUNT",
                points="outliers",
                labels={"PRODUCT_TYPE": "Product type", "SEATS_PER_ACCOUNT": "Seats per account"},
            )
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        with q2:
            st.markdown("**ZIP/product combinations by account count**")
            account_bins = hist_df.copy()
            max_accounts = int(account_bins["TOTAL_ACCOUNTS"].max()) if not account_bins.empty else 0
            if max_accounts <= 0:
                st.info("No account-count data available for the current filters.")
            else:
                bucket_defs = [
                    (1, 1, "1"),
                    (2, 2, "2"),
                    (3, 5, "3–5"),
                    (6, 10, "6–10"),
                    (11, 25, "11–25"),
                    (26, 50, "26–50"),
                    (51, 100, "51–100"),
                    (101, float("inf"), "100+"),
                ]

                def account_bucket(value: int) -> str:
                    for low, high, label in bucket_defs:
                        if low <= value <= high:
                            return label
                    return "Other"

                visible_labels = [label for low, _high, label in bucket_defs if low <= max_accounts]
                account_bins["ACCOUNT_BUCKET"] = account_bins["TOTAL_ACCOUNTS"].apply(account_bucket)
                bucket_summary = (
                    account_bins.groupby("ACCOUNT_BUCKET", as_index=False)
                    .size()
                    .assign(ACCOUNT_BUCKET=lambda x: pd.Categorical(x["ACCOUNT_BUCKET"], categories=visible_labels, ordered=True))
                    .sort_values("ACCOUNT_BUCKET")
                )
                fig = px.bar(
                    bucket_summary,
                    x="ACCOUNT_BUCKET",
                    y="size",
                    text="size",
                    labels={"ACCOUNT_BUCKET": "Accounts in ZIP/product combination", "size": "Number of combinations"},
                )
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Rows with high seats per account")
        st.caption("Useful for spotting rows that need business-definition clarification or QA review.")
        outlier_min_accounts = st.slider("Outlier minimum accounts", 1, 50, 5)
        outliers = outlier_rows(filtered, min_accounts=outlier_min_accounts, limit=100)
        st.dataframe(outliers, use_container_width=True, hide_index=True)

        st.subheader("Distribution of seats per account")
        fig = px.histogram(
            hist_df,
            x="SEATS_PER_ACCOUNT",
            color="PRODUCT_TYPE",
            nbins=80,
            marginal="box",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            """
            **Question to confirm with the data owner:** does `TOTAL_SEATS` count ticketed seat-events across all games in a package/season? If so, rows with ~100–150 seats per account can be plausible for full-season products.
            """
        )

    with tab_data:
        st.subheader("Filtered data")
        show_cols = [
            "SEASON_YEAR",
            "POSTAL_CODE",
            "place_name",
            "state_code",
            "PRODUCT_TYPE",
            "TOTAL_SEATS",
            "TOTAL_ACCOUNTS",
            "SEATS_PER_ACCOUNT",
        ]
        existing_cols = [c for c in show_cols if c in filtered.columns]
        st.dataframe(filtered[existing_cols], use_container_width=True, hide_index=True)
        st.download_button(
            "Download filtered CSV",
            filtered.to_csv(index=False).encode("utf-8"),
            file_name="blackhawks_filtered_foundation.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
