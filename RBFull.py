# Function to display heatmaps based on the betting data
def display_heatmaps(df):
    # Number Betting Heatmap
    st.subheader("Number Betting Heatmap")
    try:
        # Create a DataFrame for betting data
        number_covered = list(range(1, 101))  # Numbers from 1 to 100
        heatmap_matrix = pd.DataFrame(0, index=number_covered, columns=["Betting Coverage"])

        # Flatten and fill the heatmap matrix based on betting data
        for betting_dict in df['number_cost_dict']:
            for number, amount in betting_dict.items():
                heatmap_matrix.loc[int(number)] += amount

        # Visualize the number betting heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(heatmap_matrix.T, cmap='YlGnBu', annot=False, cbar=True, ax=ax)  # Transposed for better display
        plt.title('Number Betting Heatmap')
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
