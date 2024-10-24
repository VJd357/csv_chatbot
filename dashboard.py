import pandas as pd
from ydata_profiling import ProfileReport
import streamlit as st
import plotly.express as px

def generate_profile(df):
    profile = ProfileReport(df, title="Pandas Profiling Report", explorative=True)
    return profile

def generate_visualizations_from_profile(df):
    import random
    import plotly.colors as pc

    visualizations = []

    # Function to generate a random color sequence
    def random_color_sequence():
        return random.sample(pc.qualitative.Plotly, len(pc.qualitative.Plotly))

    # Compute correlation heatmap for numerical columns only
    num_cols = df.select_dtypes(include='number').columns
    if len(num_cols) > 1:
        correlations = df[num_cols].corr()
        fig = px.imshow(correlations, text_auto=True, aspect="auto")
        visualizations.append(("Correlation Heatmap", fig))

    # Extract missing values heatmap
    missing_values = df.isnull().sum()
    if missing_values.sum() > 0:
        fig = px.imshow(df.isnull(), aspect="auto")
        visualizations.append(("Missing Values Heatmap", fig))

    # Generate visualizations for numerical columns
    for col in num_cols:
        fig = px.histogram(df, x=col, color_discrete_sequence=random_color_sequence())
        visualizations.append((f"Histogram for {col}", fig))

    # Generate visualizations for categorical columns
    cat_cols = df.select_dtypes(include='object').columns
    for col in cat_cols:
        fig = px.histogram(df, x=col, color_discrete_sequence=random_color_sequence())
        visualizations.append((f"Bar Chart for {col}", fig))

    return visualizations

def main():
    st.title("Automated Dashboard Generator")

    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])  
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # Generate profile report
        profile = generate_profile(df)

        # Generate visualizations based on profile
        visualizations = generate_visualizations_from_profile(df)

        # Display data overview and visualizations
        if len(visualizations) > 0:
            st.subheader("Data Overview")
            st.write(df.head())

            # Display visualizations in a 3-column layout
            for i in range(0, len(visualizations), 3):
                cols = st.columns(3)
                for j, (title, fig) in enumerate(visualizations[i:i+3]):
                    with cols[j]:
                        st.subheader(title)
                        st.plotly_chart(fig, key=f"plot_{i+j}")

if __name__ == "__main__":
    main()