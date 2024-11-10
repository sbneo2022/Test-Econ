from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple


@dataclass
class StakingData:
    FYAP: float  # Fixed Yearly Annual Percentage (e.g., 0.08 for 8%)
    BBN_TS: float  # Total Supply of BBN (e.g., 10_000_000_000)
    BTC_Stake: float  # Total BTC Staked (e.g., 10_000_000_000)
    BBN_SR: float  # Current BBN Staking Rate (e.g., 0.4001)
    Price_BBN: float  # Price of BBN (e.g., $1.0)
    Price_BTC: float  # Price of BTC (e.g., $30,000)


@dataclass
class APYResults:
    BBN_APY: float
    BTC_APY: float


class StakingAPYCalculator(ABC):
    @abstractmethod
    def calculate_beta(self, staking_data: StakingData) -> float:
        pass

    @abstractmethod
    def calculate_gamma(self, beta: float) -> float:
        pass

    @abstractmethod
    def calculate_splits(self, gamma: float):
        pass

    @abstractmethod
    def calculate_BBN_APY(self, staking_data: StakingData) -> float:
        pass

    @abstractmethod
    def calculate_BTC_APY(self, staking_data: StakingData) -> float:
        pass

    @abstractmethod
    def calculate_APYs(self, staking_data: StakingData) -> APYResults:
        pass


class BBNBTCStakingAPYCalculator(StakingAPYCalculator):
    def calculate_beta(self, staking_data: StakingData) -> float:
        """Calculate the staking ratio beta."""
        beta = staking_data.BBN_SR / 0.4  # Stake Target is assumed to be 0.4
        print(f"Calculated Beta (β): {beta}")
        return beta

    def calculate_gamma(self, beta: float) -> float:
        """Calculate Gamma based on beta."""
        if beta < 1:
            gamma = (1 / 4) / (3 / 4)  # 1/3
        elif 1 <= beta <= 2.4:
            gamma = 0.4 / 0.6  # 2/3
        elif beta > 2.4:
            gamma = 0.5 / 0.5  # 1
        print(f"Calculated Gamma (Γ): {gamma}")
        return gamma

    def calculate_splits(self, gamma: float):
        """Calculate the split between BBN and BTC based on gamma."""
        # Split_BBN / Split_BTC = gamma
        # Split_BBN + Split_BTC = 1
        # Solve for Split_BTC: Split_BTC = 1 / (gamma + 1)
        if gamma + 1 == 0:
            raise ValueError("Invalid Gamma value leading to division by zero.")
        Split_BTC = 1 / (gamma + 1)
        Split_BBN = 1 - Split_BTC
        print(f"Calculated Splits: Split_BBN = {Split_BBN}, Split_BTC = {Split_BTC}")
        return Split_BBN, Split_BTC

    def calculate_BBN_APY(self, staking_data: StakingData) -> float:
        """Calculate the APY for BBN stakers."""
        BBN_APY = (
            staking_data.FYAP * staking_data.split_BBN / staking_data.BBN_SR
        ) * 100
        print(f"Calculated BBN_APY: {BBN_APY}%")
        return BBN_APY

    def calculate_BTC_APY(self, staking_data: StakingData) -> float:
        """Calculate the APY for BTC stakers."""
        # Calculate BBN Fully Diluted Valuation (BBN_FDV)
        BBN_FDV = staking_data.BBN_TS * staking_data.Price_BBN
        print(f"Calculated BBN_FDV: ${BBN_FDV}")
        # Calculate Amount_of_BTC distributed
        Amount_of_BTC = (
            staking_data.FYAP
            * staking_data.split_BTC
            * BBN_FDV
            / staking_data.Price_BTC
        )
        print(f"Calculated Amount_of_BTC: {Amount_of_BTC} BTC")

        # Calculate BTC_APY
        #                btc_apy = amount_of_btc / (self.BTC_stake / btc_price) * 100

        BTC_APY = (
            Amount_of_BTC / (staking_data.BTC_Stake / staking_data.Price_BTC)
        ) * 100
        print(f"Calculated BTC_APY: {BTC_APY}%")
        return BTC_APY

    def calculate_APYs(self, staking_data: StakingData) -> APYResults:
        """Calculate both BBN and BTC APYs."""
        beta = self.calculate_beta(staking_data)
        gamma = self.calculate_gamma(beta)
        # Optionally, recalculate splits if needed
        Split_BBN, Split_BTC = self.calculate_splits(gamma)
        staking_data.split_BBN = Split_BBN
        staking_data.split_BTC = Split_BTC
        # Update splits in staking_data if using dynamic splits
        # For now, using provided splits
        BBN_APY = self.calculate_BBN_APY(staking_data)
        BTC_APY = self.calculate_BTC_APY(staking_data)
        return APYResults(BBN_APY=BBN_APY, BTC_APY=BTC_APY)


def simulate_staking_apy(staking_data: StakingData) -> APYResults:
    """Simulate the staking APY calculations."""
    calculator = BBNBTCStakingAPYCalculator()
    results = calculator.calculate_APYs(staking_data)
    return results


# Example Usage
if __name__ == "__main__":
    bbn_sr_list = [0.2]  # , 0.5, 1]
    for bbn_sr in bbn_sr_list:
        for price_bbn in [0.1]:  # , 0.5, 0.8, 1.5]:
            for btc_stake in [
                2_000_000_000,
                5_000_000_000,
                8_000_000_000,
                10_000_000_000,
            ]:
                print(
                    f"___Beta: {bbn_sr / 0.4 }, Price_BBN: {price_bbn}, BTC_Stake: {btc_stake}___"
                )
                # Initialize the staking data with provided values
                staking_data = StakingData(
                    FYAP=0.08,  # 8%
                    BBN_TS=10_000_000_000,  # 10,000,000,000 BBN
                    BTC_Stake=btc_stake,  # Variable BTC staked
                    BBN_SR=bbn_sr,  # Current BBN Staking Rate
                    Price_BBN=price_bbn,  # Variable price per BBN
                    Price_BTC=75_000,  # $75,000 per BTC
                )

                # Run the simulation
                apy_results = simulate_staking_apy(staking_data)
                # Display the results
                print("\n--- APY Results ---")
                print(f"BBN APY: {apy_results.BBN_APY:.4f}%")
                print(f"BTC APY: {apy_results.BTC_APY:.4f}%\n")