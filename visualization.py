import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import plotly.express as px
import networkx as nx


def plot_boxplot(data):
    """
    Boxplot of daily returns to visualize outliers.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(y=data['Return'], ax=ax, showfliers=True)
    ax.set_title("Boxplot of Daily Returns with Outliers")
    ax.set_ylabel("Daily Return")
    plt.tight_layout()
    return fig


def plot_guideline_scatter(data):
    """
    Scatter plot of Volume vs Daily Return with guideline boundaries.
    """
    # Compute guideline boundaries
    volume_min, volume_max = data['Volume'].quantile([0.25, 0.75])
    mean_return, std_return = data['Return'].mean(), data['Return'].std()
    return_min, return_max = mean_return - 2 * std_return, mean_return + 2 * std_return

    # Scatter plot with color mapping
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = data['deviates_guideline'].map({True: 'red', False: 'blue'})
    ax.scatter(data['Return'], data['Volume'], c=colors, alpha=0.6)

    # Labels and title
    ax.set_xlabel('Daily Return')
    ax.set_ylabel('Volume')
    ax.set_title('Trade Volume vs Daily Return\nRed = Deviation from Guidelines')

    # Add guideline boundaries
    for y in [volume_min, volume_max]:
        ax.axhline(y=y, color='green', linestyle='--', label='Volume Boundaries')
    for x in [return_min, return_max]:
        ax.axvline(x=x, color='orange', linestyle='--', label='Return Boundaries')

    ax.legend()
    return fig


def view_graph(path, title):
    """
    Load an image from a file and create an interactive Plotly figure.
    """
    img = Image.open(path)
    fig = px.imshow(img, title=title)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    fig.update_layout(width=1200, height=800)
    return fig


class Chart:
    """
    Encapsulates multiple trade visualization charts.
    """

    def __init__(self, data):
        # Select first 100 rows for visualization
        self.df = data.head(100)
        self.G = nx.DiGraph()

        # Construct nodes from "Gmt time"
        for _, row in self.df.iterrows():
            trade_id = row["Gmt time"].isoformat()
            self.G.add_node(
                trade_id,
                timestamp=row["Gmt time"],
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                is_outlier=row["is_outlier"],
                deviates_guideline=row["deviates_guideline"]
            )

        # Create edges in sorted time order
        trade_ids = self.df.sort_values(by="Gmt time")["Gmt time"].apply(lambda x: x.isoformat()).tolist()
        nx.add_path(self.G, trade_ids)

    def line_chart(self):
        """
        Plotly line chart of trade volume over time.
        """
        return px.line(self.df, x="Gmt time", y="Volume",
                       title="Trade Volume Over Time",
                       labels={"Gmt time": "Time", "Volume": "Volume"})

    def betweeness_centrality(self):
        """
        Histogram of betweenness centrality for trade graph nodes.
        """
        centrality_values = list(nx.betweenness_centrality(self.G).values())
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(centrality_values, bins=30, color="purple", alpha=0.7)
        ax.set_title("Betweenness Centrality Distribution of Trade Nodes")
        ax.set_xlabel("Betweenness Centrality")
        ax.set_ylabel("Frequency")
        return fig

    def scatter_plot(self):
        """
        Scatter plot of close price over time, highlighting outlier trades.
        """
        return px.scatter(self.df, x="Gmt time", y="Close", color="is_outlier",
                          title="Close Price Over Time (Outliers Highlighted)",
                          labels={"Gmt time": "Time", "Close": "Close Price", "is_outlier": "Is Outlier"},
                          color_discrete_map={True: "red", False: "blue"})

    def bar_chart(self):
        """
        Plotly bar chart summarizing trade status counts.
        """
        status_counts = {
            "Outlier": self.df["is_outlier"].sum(),
            "Guideline Deviation": self.df["deviates_guideline"].sum(),
            "Normal": len(self.df) - self.df["is_outlier"].sum() - self.df["deviates_guideline"].sum()
        }
        return px.bar(pd.DataFrame(status_counts.items(), columns=["Status", "Count"]),
                      x="Status", y="Count", title="Trade Status Counts",
                      labels={"Count": "Number of Trades"}, color="Status",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
