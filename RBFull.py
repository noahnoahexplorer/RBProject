import streamlit as st
import pandas as pd
import numpy as np
import ast
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Streamlit app layout
st.set_page_config(page_title="Comprehensive Scorecard Generator with Betting Heatmap", layout="wide")

# Function to display a KPI card
def display_kpi_card(title, value, icon=None, color=None):
    st.markdown(
        f"""
        <div style="background-color: {color}; padding: 10px; border-radius: 5px; text-align: center;">
            <h2 style="color: black; margin: 0;">{icon if icon else ''} {value}</h2>
            <h4 style="color: black; margin: 0;">{title}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

# File uploader for the CSV file
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

# Check if a CSV file is uploaded
if uploaded_file is not None:
    # Read the uploaded CSV file into a pandas dataframe
    df = pd.read_csv(uploaded_file, dtype={'username': str})

    # Display the raw data with the total number of rows
    st.write(f"Raw Data (Total number of rows: {df.shape[0]}):")
    st.dataframe(df)

    # Clean column names by stripping any leading/trailing spaces
    df.columns = df.columns.str.strip()

    # Check if the 'number_cost_dict' column exists
    if 'number_cost_dict' in df.columns:
        # Convert the 'number_cost_dict' column from string to dictionary
        df['number_cost_dict'] = df['number_cost_dict'].apply(ast.literal_eval)

        # Initialize an array to store the total bets on each number (from 1 to 100)
        total_bets = np.zeros(100)

        # Loop through each row and aggregate the betting amounts by number
        for _, row in df.iterrows():
            bet_dict = row['number_cost_dict']
            for number, bet_amount in bet_dict.items():
                # Add the bet amount to the corresponding number in total_bets array
                total_bets[int(number) - 1] += bet_amount

        # Create a DataFrame for heatmap visualization
        heatmap_data = pd.DataFrame(total_bets.reshape(10, 10))
        heatmap_data.columns = [f'{i+1}' for i in range(10)]
        heatmap_data.index = [f'{i*10+1}-{(i+1)*10}' for i in range(10)]

        # Visualize the heatmap using Seaborn
        st.subheader("Heatmap of Total Bets by Number (1 to 100) using Seaborn")
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlGnBu', ax=ax)
        plt.tight_layout()  # Ensure the plot fits within the figure area
        st.pyplot(fig)  # Render the heatmap in Streamlit
        plt.close(fig)  # Close the figure to avoid memory leaks

        # Option to use Plotly for heatmap instead of Seaborn
        st.subheader("Heatmap of Total Bets by Number (1 to 100) using Plotly")
        fig = px.imshow(
            heatmap_data.values,
            labels=dict(x="Number", y="Range", color="Total Bets"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale="YlGnBu"
        )
        st.plotly_chart(fig)

    else:
        st.write("The 'number_cost_dict' column is not found in the dataset. Please check your data.")

    # Function to generate scorecard for unique usernames
    def generate_unique_username_scorecard(df):
        unique_usernames = df['username'].nunique()
        display_kpi_card("Active Players", unique_usernames, icon="👥", color="#f4cccc")

    # Function to generate scorecard for total cost
    def generate_total_cost_scorecard(df):
        total_cost = df['total_cost'].sum()
        display_kpi_card("Total Cost", f"${total_cost:,.2f}", icon="💸", color="#cfe2f3")

    # Function to generate scorecard for total reward
    def generate_total_reward_scorecard(df):
        total_reward = df['rewards'].sum()
        display_kpi_card("Total Reward", f"${total_reward:,.2f}", icon="💰", color="#d9ead3")

    # Function to generate scorecard for profit margin
    def generate_profit_margin_scorecard(total_cost, total_reward):
        if total_cost != 0:  # To avoid division by zero error
            profit_margin = ((total_cost - total_reward) / total_cost) * 100
            color = "#ff9999" if profit_margin < 0 else "#b6d7a8"
            display_kpi_card("Profit Margin", f"{profit_margin:.2f}%", icon="📈", color=color)
        else:
            display_kpi_card("Profit Margin", "N/A", icon="📈", color="#c9daf8")

    # Function to generate summary table
    def generate_summary_table(df):
        summary = df.groupby(['ref_provider', 'product_name_en']).agg(
            unique_player_count=pd.NamedAgg(column='username', aggfunc='nunique'),
            total_cost=pd.NamedAgg(column='total_cost', aggfunc='sum'),
            total_reward=pd.NamedAgg(column='rewards', aggfunc='sum')
        )
        summary['total_winloss'] = summary['total_reward'] - summary['total_cost']
        summary = summary.reset_index()
        st.dataframe(summary)

    # Function to generate top 10 winners by net gain/loss
    def generate_top_winners_bar_chart(df):
        user_summary = df.groupby('username').agg(
            total_rewards=pd.NamedAgg(column='rewards', aggfunc='sum'),
            total_cost=pd.NamedAgg(column='total_cost', aggfunc='sum')
        )
        user_summary['net_gain_loss'] = user_summary['total_rewards'] - user_summary['total_cost']
        top_winners = user_summary.sort_values(by='net_gain_loss', ascending=False).head(10).reset_index()
        fig = px.bar(
            top_winners,
            x='net_gain_loss',
            y='username',
            orientation='h',
            title="Top 10 Winners by Net Gain/Loss",
            labels={'net_gain_loss': 'Net Gain/Loss', 'username': 'Username'},
            color='net_gain_loss',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig)

    # Display the summary table
    st.subheader("Summary Table by ref_provider and product_name_en")
    generate_summary_table(df)

    # Create four columns for the scorecards
    col1, col2, col3, col4 = st.columns(4)

    # Place the Total Rewards Amount scorecard in the first column
    with col1:
        generate_total_reward_scorecard(df)

    # Place the Total Costs Amount scorecard in the second column
    with col2:
        generate_total_cost_scorecard(df)

    # Place the unique username scorecard in the third column
    with col3:
        generate_unique_username_scorecard(df)

    # Calculate total cost and total reward
    total_cost = df['total_cost'].sum()
    total_reward = df['rewards'].sum()

    # Place the profit margin scorecard in the fourth column
    with col4:
        generate_profit_margin_scorecard(total_cost, total_reward)

    # Display the top winners bar chart
    st.subheader("Top 10 Winners by Net Gain/Loss")
    generate_top_winners_bar_chart(df)

else:
    st.info("Please upload a CSV file to generate a scorecard.")
