from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIS_PATH = PROJECT_ROOT / "visualizations"

# "Tier 1" is rapid transit (BART)
# "Tier 2" is bus transit (example: AC Transit)

ZONE_ORDER = ["Tier 1 - 200ft", "Tier 1 - Quarter Mile", "Tier 1 - Half Mile",
              "Tier 2 - 200ft", "Tier 2 - Quarter Mile", "Tier 2 - Half Mile"]


def save_fig(ax, name, subdir="charts"):
    # Save the chart drawn on ax as a .PNG in visualizations/charts/.
    folder = VIS_PATH / subdir
    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / (name + ".png")
    ax.figure.savefig(file_path, dpi=200, bbox_inches="tight")
    print("saved to " + str(file_path.relative_to(PROJECT_ROOT)))


def units_by_zone_and_epc(parcels_tod):
    return (parcels_tod.groupby(["epc_class", "zone_label"], observed=True)["max_units"].sum()
            .unstack().reindex(columns=ZONE_ORDER).fillna(0))


def row_share(table):
    return table.div(table.sum(axis=1), axis=0) * 100   # each row sums to 100%


def tier_share_by_epc(parcels_tod):
    tier = parcels_tod["zone_label"].str[:6].rename("tier")
    tier_share = (parcels_tod.groupby(["epc_class", tier], observed=True)["max_units"].sum()
                  .unstack())
    return row_share(tier_share)


def plot_units_by_zone(parcels_tod, name="chart1_units_by_zone"):
    ax = (
        parcels_tod
        .groupby("zone_label")["max_units"]
        .sum()
        .reindex(ZONE_ORDER).plot.bar(rot=45)
    )
    ax.set(title="Allowed housing units by SB 79 zone", xlabel="TOD zone", ylabel="allowed units")
    save_fig(ax, name)
    return ax


def plot_heatmap(grid, title, cbar_label, name, fmt="{:,.0f}"):
    fig, ax = plt.subplots(figsize=(9, 4))
    im = ax.imshow(grid, cmap="Blues")
    ax.set_xticks(range(len(grid.columns)), grid.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(grid.index)), grid.index)
    for (i, j), v in np.ndenumerate(grid.values):
        ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=8)
    fig.colorbar(im, label=cbar_label)
    ax.set(title=title, xlabel="TOD zone", ylabel="EPC level")
    save_fig(ax, name)
    return ax


def plot_allowed_vs_soft(parcels_tod, name="chart4_allowed_vs_soft"):
    g = parcels_tod.groupby("epc_class", observed=True)[["max_units", "soft_units"]].sum()
    y = g.index.astype(str)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hlines(y, g["soft_units"], g["max_units"], color="lightgray", lw=3)
    ax.scatter(g["max_units"], y, label="allowed", zorder=3)
    ax.scatter(g["soft_units"], y, label="on soft sites", zorder=3)
    ax.legend()
    ax.set(title="Gap between allowed and likely-to-redevelop capacity",
           xlabel="housing units", ylabel="EPC level")
    save_fig(ax, name)
    return ax


def plot_density_map(parcels_tod, epc_data, tod_data, name="berkeley_sb79_map_updated", basemap=True):
    parcels_map = parcels_tod.to_crs(3857)
    epc_map = epc_data.to_crs(3857)

    fig, ax = plt.subplots(figsize=(10, 10))
    parcels_map.plot(ax=ax, column="du_per_acre", categorical=True, cmap="YlOrRd",
                     linewidth=0, legend=True,
                     legend_kwds={"title": "SB 79 min. density (du/acre)", "loc": "upper right"})
    epc_map.boundary.plot(ax=ax, color="black", linewidth=0.5)

    xmin, ymin, xmax, ymax = parcels_map.total_bounds
    ax.set_xlim(xmin - 2000, xmax + 2000)
    ax.set_ylim(ymin - 2000, ymax + 2000)

    epc_map.plot(ax=ax, color="none", edgecolor="black", linewidth=0.5, hatch="///", alpha=0.4)  # hatched = epc
    tod_data.to_crs(3857).boundary.plot(ax=ax, color="gray", linewidth=0.3)                        # zone rings
    if basemap:
        import contextily as cx
        cx.add_basemap(ax, source=cx.providers.Esri.WorldGrayCanvas)
    ax.set_axis_off()
    ax.set_title("SB 79 allowed density, Alameda County TOD parcels\n(hatched areas = Equity Priority Communities)\nWe observe the variation and overlap between TOD parcels and EPCs.")
    save_fig(ax, name, subdir="maps")
    return ax
