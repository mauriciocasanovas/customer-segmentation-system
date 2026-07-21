import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def run_customer_segmentation():
    """Perform customer segmentation using the K-Means clustering algorithm."""

    # ------------------------------------------------------------------
    # DATA EXTRACTION
    # ------------------------------------------------------------------

    # Project paths
    project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    database_path = os.path.join(
        project_root,
        "data",
        "customer_data.db",
    )

    results_path = os.path.join(
        project_root,
        "results",
    )

    images_path = os.path.join(
        project_root,
        "images",
    )

    # Verify that the database file exists
    if not os.path.exists(database_path):
        print(f"Error: '{database_path}' was not found.")
        return

    # Connect to SQLite and load customer data
    conn = sqlite3.connect(database_path)

    df = pd.read_sql_query(
        "SELECT * FROM customers",
        conn,
    )

    conn.close()

    # ------------------------------------------------------------------
    # DATA PREPROCESSING
    # ------------------------------------------------------------------

    # Select features for clustering
    features = df[
        [
            "total_spending",
            "visit_frequency",
        ]
    ]

    # Normalize the features so that both variables contribute equally
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # ------------------------------------------------------------------
    # K-MEANS CLUSTERING
    # ------------------------------------------------------------------

    model = KMeans(
        n_clusters=4,
        random_state=42,
        n_init=10,
    )

    # Assign each customer to a cluster
    df["segment"] = model.fit_predict(
        scaled_features
    )

    # ------------------------------------------------------------------
    # CLUSTER SUMMARY
    # ------------------------------------------------------------------

    # Convert cluster centers back to the original scale
    cluster_centers = scaler.inverse_transform(
        model.cluster_centers_
    )

    cluster_summary = pd.DataFrame(
        cluster_centers,
        columns=[
            "Average Spending",
            "Average Visit Frequency",
        ],
    )

    # ------------------------------------------------------------------
    # EXPORT RESULTS
    # ------------------------------------------------------------------

    os.makedirs(
        results_path,
        exist_ok=True,
    )

    os.makedirs(
        images_path,
        exist_ok=True,
    )

    output_excel = os.path.join(
        results_path,
        "customer_segmentation_report.xlsx",
    )

    try:
        with pd.ExcelWriter(output_excel) as writer:

            df.to_excel(
                writer,
                sheet_name="Customer List",
                index=False,
            )

            cluster_summary.to_excel(
                writer,
                sheet_name="Cluster Statistics",
                index=False,
            )

        print(
            f"Customer segmentation report generated: "
            f"{output_excel}"
        )

    except Exception as e:
        print(
            f"Error exporting Excel report: {e}"
        )

    # ------------------------------------------------------------------
    # DATA VISUALIZATION
    # ------------------------------------------------------------------

    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=df,
        x="visit_frequency",
        y="total_spending",
        hue="segment",
        palette="viridis",
        s=100,
    )
    plt.title("Customer Segmentation Analysis", fontsize=14)
    plt.xlabel("Visit Frequency")
    plt.ylabel("Total Spending")
    plt.savefig(
        os.path.join(images_path, "customer_clusters.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    # ------------------------------------------------------------------
    # BUSINESS VISUALIZATIONS
    # ------------------------------------------------------------------

    segment_metrics = (
        df.groupby("segment")[["total_spending", "visit_frequency"]]
        .mean()
        .reset_index()
    )

    spending_median = segment_metrics["total_spending"].median()
    visits_median = segment_metrics["visit_frequency"].median()

    profiles = []

    for _, row in segment_metrics.iterrows():
        if row["total_spending"] >= spending_median and row["visit_frequency"] >= visits_median:
            profiles.append("High-value frequent customers")
        elif row["total_spending"] >= spending_median:
            profiles.append("Premium occasional customers")
        elif row["visit_frequency"] >= visits_median:
            profiles.append("Frequent low-spending customers")
        else:
            profiles.append("Low-value occasional customers")

    interpretation = segment_metrics.copy()
    interpretation["Customer Profile"] = profiles

    with pd.ExcelWriter(
        output_excel,
        mode="a",
        engine="openpyxl",
        if_sheet_exists="replace",
    ) as writer:
        interpretation.rename(
            columns={
                "segment": "Segment",
                "total_spending": "Average Spending",
                "visit_frequency": "Average Visit Frequency",
            }
        ).to_excel(
            writer,
            sheet_name="Segment Interpretation",
            index=False,
        )

    plt.figure(figsize=(8, 5))
    sns.barplot(
        data=segment_metrics,
        x="segment",
        y="total_spending",
        hue="segment",
        palette="viridis",
        legend=False,
    )
    plt.title("Average Spending by Segment")
    plt.xlabel("Segment")
    plt.ylabel("Average Spending")
    plt.savefig(
        os.path.join(images_path, "average_spending_by_segment.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.barplot(
        data=segment_metrics,
        x="segment",
        y="visit_frequency",
        hue="segment",
        palette="viridis",
        legend=False,
    )
    plt.title("Average Visit Frequency by Segment")
    plt.xlabel("Segment")
    plt.ylabel("Average Visit Frequency")
    plt.savefig(
        os.path.join(images_path, "average_visit_frequency_by_segment.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


if __name__ == "__main__":
    print(
        "Starting customer segmentation process..."
    )
    run_customer_segmentation()