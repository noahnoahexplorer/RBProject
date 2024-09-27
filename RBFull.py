import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import ast

# Streamlit app settings
st.set_page_config(page_title="Comprehensive Lottery Analysis", layout="wide")

# Title of the app
st.title("Comprehensive Lottery Analysis & Scorecard Generator")

# File upload section
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])


# Function to validate if a dataframe is empty or not
def is_valid_dataframe(df):
    return not df.empty and len(df.columns) > 0


# Function to display KPI cards
def display_kpi_card(title, value, delta=None, delta_color="normal", icon=None, color="lightblue"):
    st.markdown(
        f"""
        <div style="background-color: {color}; padding: 10px; border-radius: 5px;">
            <div style="font-size: 20px; color: black;">{title}</div>
            <div style="font-size: 28px; font-weight: bold; color: black;">{value}</div>
            {'<div style="font-size: 16px; color: green;">' + icon + '</div>' if icon else ''}
            {'<div style="font-size: 16px; color:' + delta_color + ';">' + delta + '</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


# Function to generate scorecard for unique usernames
def generate_unique_username_scorecard(df):
    unique_usernames = df['username'].nunique()
    display_kpi_card("Active Players", unique_usernames, icon="👤", color="#6fa8dc")


# Function to generate scorecard for total cost
def generate_total_cost_scorecard(df):
    total_cost = df['total_cost'].sum()
    display_kpi_card("Total Cost", f"${total_cost:,.2f}", icon="💰", color="#ff9999")
    return total_cost


# Function to generate scorecard for total reward
def generate_total_reward_scorecard(df):
    total_reward = df['rewards'].sum()
    display_kpi_card("Total Reward", f"${total_reward:,.2f}", icon="🏆", color="#b6d7a8")
    return total_reward


# Function to generate scorecard for profit margin
def generate_profit_margin_scorecard(total_cost, total_reward):
    if total_cost != 0:
        profit_margin = ((total_reward - total_cost) / total_cost) * 100
        # Set color based on profit margin
        color = "#b6d7a8" if profit_margin >= 0 else "#ff9999"
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


def display_heatmaps(df):
    # Number Betting Heatmap
    st.subheader("Number Betting Heatmap")
    try:
        # Convert string dictionaries to actual dictionaries
        df['number_cost_dict'] = df['number_cost_dict'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        
        # Create a DataFrame for betting data
        number_covered = list(range(1, 101))  # Numbers from 1 to 100
        heatmap_matrix = pd.DataFrame(0, index=number_covered, columns=["Betting Coverage"])

        # Fill the heatmap matrix based on betting data
        for betting_dict in df['number_cost_dict']:
            for number, amount in betting_dict.items():
                heatmap_matrix.loc[int(number)] += amount

        # Visualize the number betting heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(heatmap_matrix, cmap='YlGnBu', annot=False, cbar=True, ax=ax)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error in number betting heatmap: {e}")

    # 30-minute Interval Heatmap Based on 'created_at'
    st.subheader("30-Minute Interval Heatmap Based on Created At")
    try:
        # Convert 'created_at' to datetime with the correct format
        df['created_at'] = pd.to_datetime(df['created_at'], format='%d/%m/%Y %H:%M', errors='coerce')

        # Remove rows with invalid 'created_at' (NaT values)
        df.dropna(subset=['created_at'], inplace=True)

        # Create a new column for 30-minute intervals
        df['30min_interval'] = df['created_at'].dt.floor('30T')

        # Aggregate data for the heatmap
        interval_data = df.groupby(['30min_interval']).size().reset_index(name='num_bets')
        interval_data['day'] = interval_data['30min_interval'].dt.day_name()
        interval_data['time_slot'] = interval_data['30min_interval'].dt.strftime('%H:%M')

        # Create pivot table for heatmap
        heatmap_data_time = interval_data.pivot(index='day', columns='time_slot', values='num_bets').fillna(0)

        # Plotting the heatmap with larger font size and rounded values
        fig, ax = plt.subplots(figsize=(14, 8))  # Adjust the figure size for more space
        sns.heatmap(heatmap_data_time, cmap='YlGnBu', annot=True, fmt=".0f", ax=ax,
                    annot_kws={"size": 10},  # Increase font size for annotation
                    cbar_kws={'label': 'Number of Bets'})  # Colorbar label
        plt.title('Number of Bets by 30-Minute Intervals')
        plt.xlabel('Time Slot (30 min intervals)')
        plt.ylabel('Day of the Week')
        plt.xticks(rotation=45, ha='right', fontsize=10)  # Rotate and adjust font size for x-axis labels
        plt.yticks(rotation=0, fontsize=10)  # Adjust font size for y-axis labels
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error in 30-minute interval heatmap: {e}")


# Main app logic
if uploaded_file is not None:
    try:
        # Read the uploaded CSV file
        df = pd.read_csv(uploaded_file)

        # Validate the dataframe
        if not is_valid_dataframe(df):
            st.error("Uploaded file is empty or does not contain valid data.")
        else:
            # Display the raw data
            st.write("Uploaded Data")
            st.dataframe(df)

            # Display summary table
            st.subheader("Summary Table by ref_provider and product_name_en")
            generate_summary_table(df)

            # Create four columns for KPI cards
            col1, col2, col3, col4 = st.columns(4)

            # Place the Total Rewards Amount scorecard in the first column
            with col1:
                total_reward = generate_total_reward_scorecard(df)

            # Place the Total Costs Amount scorecard in the second column
            with col2:
                total_cost = generate_total_cost_scorecard(df)

            # Place the unique username scorecard in the third column
            with col3:
                generate_unique_username_scorecard(df)

            # Place the profit margin scorecard in the fourth column
            with col4:
                generate_profit_margin_scorecard(total_cost, total_reward)

            # Display the top winners bar chart
            st.subheader("Top 10 Winners by Net Gain/Loss")
            generate_top_winners_bar_chart(df)

            # Convert 'number_cost_dict' column to dictionary
            if 'number_cost_dict' in df.columns:
                df['number_cost_dict'] = df['number_cost_dict'].apply(ast.literal_eval)

                # Display heatmaps for betting data
                display_heatmaps(df)
            else:
                st.warning("The column 'number_cost_dict' is missing in the uploaded CSV.")
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Please upload a CSV file to proceed.")
