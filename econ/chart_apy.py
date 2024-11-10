import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dynamic_inflation import StakingData, simulate_staking_apy
import numpy as np
import io
import sys
from abc import ABC, abstractmethod


class PlotCreator(ABC):
    @abstractmethod
    def create_plot(self, results_df):
        pass


class APYPlotCreator(PlotCreator):
    def create_plot(self, results_df):
        """Create a plotly figure with the simulation results."""
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=("BBN APY Results", "BTC APY Results"),
            vertical_spacing=0.1,
            row_heights=[0.5, 0.5],
        )

        # Add BBN APY trace
        fig.add_trace(
            go.Scatter(
                x=results_df["BBN_SR"],
                y=results_df["BBN_APY"],
                name="BBN APY",
                line=dict(color="#00ff9f", width=2),
                mode="lines+markers",
            ),
            row=1,
            col=1,
        )

        # Add BTC APY trace
        fig.add_trace(
            go.Scatter(
                x=results_df["BBN_SR"],
                y=results_df["BTC_APY"],
                name="BTC APY",
                line=dict(color="#00c3ff", width=2),
                mode="lines+markers",
            ),
            row=2,
            col=1,
        )

        # Update layout
        fig.update_layout(
            template="plotly_dark",
            height=800,
            showlegend=True,
            paper_bgcolor="rgba(30,30,30,0.8)",
            plot_bgcolor="rgba(30,30,30,0.8)",
            margin=dict(l=50, r=50, t=50, b=50),
        )

        # Update x-axes labels
        fig.update_xaxes(title_text="BBN_SR", row=1, col=1)
        fig.update_xaxes(title_text="BBN_SR", row=2, col=1)
        # Update y-axes labels
        fig.update_yaxes(title_text="BBN_APY (%)", row=1, col=1)
        fig.update_yaxes(title_text="BTC_APY (%)", row=2, col=1)

        return fig


class PrintCapture(ABC):
    @abstractmethod
    def capture_prints(self):
        pass


class PrintCaptureImpl(PrintCapture):
    def capture_prints(self):
        """Context manager to capture print statements."""
        output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output
        return output, old_stdout


class DynamicInflationApp:
    def __init__(self):
        self.plot_creator = APYPlotCreator()
        self.print_capture = PrintCaptureImpl()

    def main(self):
        st.set_page_config(page_title="Dynamic Inflation Calculator", layout="wide")
        st.title("Dynamic Inflation Calculator")

        # Sidebar inputs
        st.sidebar.header("Parameters")

        fyap = st.sidebar.number_input(
            "FYAP (Fixed Yearly Annual Percentage)",
            min_value=0.0,
            max_value=1.0,
            value=0.08,
            format="%.3f",
            help="e.g., 0.08 for 8%",
        )

        bbn_ts = st.sidebar.number_input(
            "BBN Total Supply",
            min_value=1_000_000_000,
            max_value=100_000_000_000,
            value=10_000_000_000,
            format="%d",
        )

        price_bbn = st.sidebar.number_input(
            "BBN Price ($)", min_value=0.0, max_value=1000.0, value=1.0, format="%.3f"
        )

        price_btc = st.sidebar.number_input(
            "BTC Price ($)",
            min_value=1000.0,
            max_value=1000000.0,
            value=75000.0,
            format="%.2f",
        )

        # BBN_SR range inputs in sidebar
        st.sidebar.subheader("BBN_SR Range Settings")
        bbn_sr_start = st.sidebar.number_input(
            "Start BBN_SR",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            format="%.3f",
            help="Starting value for BBN_SR range",
        )

        bbn_sr_end = st.sidebar.number_input(
            "End BBN_SR",
            min_value=bbn_sr_start,
            max_value=1.0,
            value=1.0,
            format="%.3f",
            help="Ending value for BBN_SR range",
        )

        bbn_sr_steps = st.sidebar.number_input(
            "Number of Steps",
            min_value=2,
            max_value=100,
            value=10,
            help="Number of points to calculate between start and end",
        )

        # Create range of BBN_SR values for simulation
        bbn_sr_range = pd.Series(np.linspace(bbn_sr_start, bbn_sr_end, bbn_sr_steps))

        # BTC_Stake range inputs in sidebar
        st.sidebar.subheader("BTC_Stake Range Settings")
        btc_stake_start = st.sidebar.number_input(
            "Start BTC_Stake",
            min_value=1_000_000_000,
            max_value=100_000_000_000,
            value=2_000_000_000,
            format="%d",
            help="Starting value for BTC_Stake range",
        )

        btc_stake_end = st.sidebar.number_input(
            "End BTC_Stake",
            min_value=btc_stake_start,
            max_value=100_000_000_000,
            value=10_000_000_000,
            format="%d",
            help="Ending value for BTC_Stake range",
        )

        btc_stake_steps = st.sidebar.number_input(
            "Number of Steps",
            min_value=2,
            max_value=10,
            value=5,
            help="Number of points to calculate between start and end",
        )

        # Create range of BTC_Stake values for simulation
        btc_stake_range = pd.Series(
            np.linspace(btc_stake_start, btc_stake_end, btc_stake_steps)
        )

        # Run simulations for each BTC_Stake value
        for btc_stake in btc_stake_range:
            st.subheader(f"Results for BTC_Stake = {btc_stake:,}")

            results = []
            all_debug_output = []

            # Run simulations for different BBN_SR values
            for bbn_sr in bbn_sr_range:
                staking_data = StakingData(
                    FYAP=fyap,
                    BBN_TS=bbn_ts,
                    BTC_Stake=btc_stake,
                    BBN_SR=bbn_sr,
                    Price_BBN=price_bbn,
                    Price_BTC=price_btc,
                )

                try:
                    # Capture print output
                    output, old_stdout = self.print_capture.capture_prints()

                    apy_results = simulate_staking_apy(staking_data)

                    # Restore stdout and get the captured output
                    sys.stdout = old_stdout
                    debug_output = output.getvalue()
                    all_debug_output.append(f"\nFor BBN_SR = {bbn_sr}:\n{debug_output}")

                    results.append(
                        {
                            "BBN_SR": bbn_sr,
                            "Beta": bbn_sr / 0.4,
                            "BBN_APY": apy_results.BBN_APY,
                            "BTC_APY": apy_results.BTC_APY,
                        }
                    )
                except Exception as e:
                    st.error(f"Error in simulation for BBN_SR={bbn_sr}: {str(e)}")
                    continue

            # Create DataFrame from results for this BTC_Stake
            results_df = pd.DataFrame(results)

            # Display plots for this BTC_Stake
            if not results_df.empty:

                # Display calculation details in an expander
                with st.expander(
                    f"Show Calculation Details for BTC_Stake = {btc_stake:,}",
                    expanded=False,
                ):
                    # Create tabs for different BBN_SR ranges
                    tab_size = 10
                    num_tabs = len(all_debug_output) // tab_size + (
                        1 if len(all_debug_output) % tab_size else 0
                    )

                    tabs = st.tabs([f"BBN_SR Range {i+1}" for i in range(num_tabs)])

                    for tab_idx, tab in enumerate(tabs):
                        with tab:
                            start_idx = tab_idx * tab_size
                            end_idx = min(start_idx + tab_size, len(all_debug_output))

                            for i in range(start_idx, end_idx):
                                st.text(all_debug_output[i])
                fig = self.plot_creator.create_plot(results_df)
                st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    app = DynamicInflationApp()
    app.main()
