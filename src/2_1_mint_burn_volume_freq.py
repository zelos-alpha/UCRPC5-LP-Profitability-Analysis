import pandas as pd
import matplotlib.pyplot as plt
import os

# List of pools
pools = ['usdc-eth-001', 'usdc-eth-005', 'usdc-eth-03', 'wbtc-eth-03']

# Output directories
csv_output_dir = '/home/zelos/src/UCRPC5/output/csv/2_1/merged_data/'
img_output_dir = '/home/zelos/src/UCRPC5/output/img/2_1/comprehensive_plot/'
special_plot_dir = '/home/zelos/src/UCRPC5/output/img/2_1/mint_burn_volume_frequency_plots/'

# Ensure the output directories exist
os.makedirs(csv_output_dir, exist_ok=True)
os.makedirs(img_output_dir, exist_ok=True)
os.makedirs(special_plot_dir, exist_ok=True)

# Loop over each pool
for pool in pools:
    print(f"Processing pool: {pool}")
    
    # Construct file paths based on the pool name
    first_csv_path = f'../../../../data/research/task2403-uni-profitability/{pool}/2_position_liquidity.csv'
    second_csv_path = f'../../../../data/research/task2403-uni-profitability/{pool}/c-lvr.csv'
    sigma_csv_path = f'../../../../data/research/task2403-uni-profitability/{pool}/sigma.csv'
    
    # Read the CSV files
    first_csv = pd.read_csv(first_csv_path)
    second_csv = pd.read_csv(second_csv_path)
    sigma_csv = pd.read_csv(sigma_csv_path)

    # Remove rows where 'block_number' is 0
    first_csv = first_csv[first_csv['block_number'] != 0]

    # Convert the 'blk_time' and 'date' columns to datetime format and extract only the date part
    first_csv['date'] = pd.to_datetime(first_csv['blk_time'], format='%Y-%m-%d %H:%M:%S').dt.date
    second_csv['date'] = pd.to_datetime(second_csv['date']).dt.date
    sigma_csv['date'] = pd.to_datetime(sigma_csv['time']).dt.date

    # Merge the two DataFrames on the 'date' column (many-to-one)
    merged_df = pd.merge(first_csv, second_csv, on='date', how='left')
    merged_df = pd.merge(merged_df, sigma_csv[['date', 'sigma_ln_r', 'sigma_daily_7', 'mean_price']], on='date', how='left')

    # Calculate the frequency of "MINT" and "BURN" in the "tx_type" column
    mint_counts = merged_df[merged_df['tx_type'] == 'MINT'].groupby('date').size()
    burn_counts = merged_df[merged_df['tx_type'] == 'BURN'].groupby('date').size()

    # Ensure all dates are included, filling in any missing dates with 0 counts
    date_range = pd.date_range(start=merged_df['date'].min(), end=merged_df['date'].max())
    mint_counts = mint_counts.reindex(date_range, fill_value=0)
    burn_counts = burn_counts.reindex(date_range, fill_value=0)

    # Extract the "0" column (c-lvr), reindex to match the date range
    column_0 = merged_df.groupby('date')['0'].first().reindex(date_range)

    # Fill NaN values in 'column_0' with 0
    column_0 = column_0.fillna(0)

    # Extract price data (mean_price)
    mean_price = sigma_csv.groupby('date')['mean_price'].first().reindex(date_range).fillna(0)

    # Extract volume of MINT and BURN by aggregating liquidity
    first_csv['liquidity'] = pd.to_numeric(first_csv['liquidity'], errors='coerce').abs()
    mint_volume_by_date = first_csv[first_csv['tx_type'] == 'MINT'].groupby('date')['liquidity'].sum().reindex(date_range, fill_value=0)
    burn_volume_by_date = first_csv[first_csv['tx_type'] == 'BURN'].groupby('date')['liquidity'].sum().reindex(date_range, fill_value=0)

    # Create specialized plot with three sections: 2:2:1 ratio (MINT/BURN Volume, Frequency, and Price)
    fig, (ax_top, ax_middle, ax_bottom) = plt.subplots(3, 1, figsize=(12, 12), gridspec_kw={'height_ratios': [2, 2, 1]}, sharex=True)

    # Top Plot: MINT and BURN Volume with alpha=0.7
    ax_top.set_ylabel('Volume of MINT and BURN', color='tab:blue')
    ax_top.plot(date_range, mint_volume_by_date, label='MINT Volume', color='tab:green', alpha=0.7)
    ax_top.plot(date_range, burn_volume_by_date, label='BURN Volume', color='tab:red', alpha=0.7)
    ax_top.tick_params(axis='y', labelcolor='tab:blue')
    ax_top.legend(loc='upper left')

    # Middle Plot: MINT and BURN Frequency with alpha=0.7
    ax_middle.set_ylabel('Frequency of MINT and BURN', color='tab:blue')
    ax_middle.plot(date_range, mint_counts, label='MINT Frequency', color='tab:green', alpha=0.7)
    ax_middle.plot(date_range, burn_counts, label='BURN Frequency', color='tab:red', alpha=0.7)
    ax_middle.tick_params(axis='y', labelcolor='tab:blue')
    ax_middle.legend(loc='upper left')

    # Bottom Plot: Price Data
    ax_bottom.set_xlabel('Date')
    ax_bottom.set_ylabel('Mean Price', color='tab:purple')
    ax_bottom.plot(date_range, mean_price, label='Mean Price', color='tab:purple')

    # Format the x-axis dates for readability
    plt.xticks(rotation=45)

    # Adjust the layout to remove space between plots
    plt.subplots_adjust(hspace=0.05)  # Reduce vertical space between subplots

    # Save the specialized plot to a PNG file with the pool name appended, in the special_plot_dir
    img_file_path = f'{special_plot_dir}mint_burn_volume_frequency_{pool}.png'
    plt.savefig(img_file_path, format='png', dpi=300)
    print(f"Specialized plot saved: {img_file_path}")

    # Show the plot
    plt.title(f'MINT and BURN Volume and Frequency for {pool}')
    plt.show()
