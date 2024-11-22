import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from io import StringIO


class GraphPlotter:
    """Class to plot graphs and KPIs based on the type specified in the data_dict."""

    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.figures = []

    def plot_graphs_in_grid(self):
        """Iterate over graphs in the data_dict and plot them in a grid layout."""
        st.markdown("Dashboard: ")
        cols = st.columns(2)
        index = 0
        for graph in self.data_dict.get('graphs', []):
            fig = self._plot_single_graph(graph)
            if fig:
                with cols[index % 2]:
                    st.plotly_chart(fig)
                self.figures.append(fig)
                index += 1

    def _plot_single_graph(self, graph):
        """Plot a single graph based on its type and data."""
        graph_type = graph.get('type')
        data = graph.get('data')
        title = graph.get('title', 'Graph')
        x_axis = graph.get('x_axis')
        y_axis = graph.get('y_axis')
        labels = graph.get('labels', {})
        colors = graph.get('colors', None)

        if data is not None:
            # Check if data is a DataFrame, if not, try to convert it
            if not isinstance(data, pd.DataFrame):
                try:
                    data = pd.DataFrame(data)
                except Exception as e:
                    print(f"Error converting data to DataFrame for graph: {title}\nException: {e}")
                    return None

            data = self._clean_data(data)
            x_axis, y_axis = self._validate_axes(data, x_axis, y_axis)
            if x_axis is None or y_axis is None:
                return None

            try:
                return self._create_figure(graph_type, data, x_axis, y_axis, labels, title, colors)
            except ZeroDivisionError as e:
                print(f"Error plotting {title}: {e}")
                return None
        else:
            print(f"No data available for graph: {title}")
            return None

    def _clean_data(self, data):
        """Replace null values and remove outliers from the data."""
        # Ensure data is a DataFrame before proceeding
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Expected data to be a DataFrame.")

        # Fill NaN values with 0
        data = data.fillna(0)

        # Remove outliers from numerical columns
        numeric_columns = data.select_dtypes(include='number').columns
        if not numeric_columns.empty:
            for column in numeric_columns:
                q1 = data[column].quantile(0.25)
                q3 = data[column].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                data = data[(data[column] >= lower_bound) & (data[column] <= upper_bound)]
        else:
            print("No numeric columns found to clean.")

        print(f"DataFrame columns: {data.columns}")
        return data

    def _validate_axes(self, data, x_axis, y_axis):
        """Validate and clean x_axis and y_axis."""
        x_axis = x_axis.strip('[]') if x_axis else None
        if isinstance(y_axis, list):
            y_axis = [col.strip('[]') for col in y_axis]
        else:
            y_axis = y_axis.strip('[]') if y_axis else None

        if x_axis not in data.columns:
            print(f"Invalid x_axis: {x_axis}")
            return None, None
        if isinstance(y_axis, list):
            y_axis = [col for col in y_axis if col in data.columns]
        elif y_axis not in data.columns:
            print(f"Invalid y_axis: {y_axis}")
            return None, None

        return x_axis, y_axis

    def _create_figure(self, graph_type, data, x_axis, y_axis, labels, title, colors):
        """Create a figure based on the graph type."""
        if graph_type == 'line':
            return px.line(data, x=x_axis, y=y_axis, labels=labels, title=title, color_discrete_sequence=colors)
        elif graph_type == 'bar':
            return px.bar(data, x=x_axis, y=y_axis, labels=labels, title=title, color_discrete_sequence=colors)
        elif graph_type == 'scatter':
            return px.scatter(data, x=x_axis, y=y_axis, labels=labels, title=title, color_discrete_sequence=colors)
        elif graph_type == 'heatmap':
            return px.density_heatmap(data, x=x_axis, y=y_axis, labels=labels, title=title, color_continuous_scale=colors)
        elif graph_type == 'pie':
            return px.pie(data, names=x_axis, values=y_axis, labels=labels, title=title, color_discrete_sequence=colors)
        elif graph_type == 'column':
            return px.bar(data, x=x_axis, y=y_axis, labels=labels, title=title, orientation='v', color_discrete_sequence=colors)
        elif graph_type == 'area':
            return px.area(data, x=x_axis, y=y_axis, labels=labels, title=title, color_discrete_sequence=colors)
        elif graph_type == 'funnel':
            return px.funnel(data, x=x_axis, y=y_axis, labels=labels, title=title)
        elif graph_type == 'gauge':
            return go.Figure(go.Indicator(
                mode="gauge+number",
                value=data[y_axis].sum() if y_axis else 0,
                title={'text': title},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
        elif graph_type == 'combo':
            fig = go.Figure()
            fig.add_trace(go.Bar(x=data[x_axis], y=data[y_axis[0]], name='Bar'))
            fig.add_trace(go.Line(x=data[x_axis], y=data[y_axis[1]], name='Line'))
            fig.update_layout(title=title, barmode='group')
            return fig
        elif graph_type == 'kpi':
            kpi_value = data[y_axis].sum() if y_axis else 0
            return go.Figure(go.Indicator(
                mode="number",
                value=kpi_value,
                title={'text': title},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
        else:
            print(f"Graph type {graph_type} is not supported.")
            return None
        
    def get_figures(self):
        """Return the list of figures."""
        return self.figures
    
def main():
    # Example data_dict for demonstration
    data_dict = {
        'graphs': [
            {
                'type': 'line',
                'data': None,  # Replace with actual DataFrame
                'title': 'Sample Line Graph',
                'x_axis': 'x_column',
                'y_axis': 'y_column',
                'labels': {'x': 'X Axis', 'y': 'Y Axis'},
                'colors': ['#1f77b4']
            }
        ]
    }

    plotter = GraphPlotter(data_dict)
    plotter.plot_graphs_in_grid()

if __name__ == "__main__":
    main()