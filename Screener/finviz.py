import pandas as pd
from pyfinviz.screener import Screener


class Finviz:
    def __init__(self, log_errors: bool = True):
        self.screener = Screener()
        self.log_errors = log_errors

    def get_low_cap_movers(self):
        options = [
            # Screener.AnalystRecomOption.STRONG_BUY_1,
            Screener.MarketCapOption.SMALL_UNDER_USD2BLN,
            Screener.RelativeVolumeOption.OVER_1,
            Screener.CurrentVolumeOption.SHARES_OVER_1M,
        ]
        screener = Screener(
            filter_options=options,
            view_option=Screener.ViewOption.VALUATION,
            pages=[x for x in range(1, 20)],
        )
        df = screener.data_frames
        df = self._convert_frames_many_to_one(df)
        return df

    def _convert_frames_many_to_one(self, data: dict):
        df = pd.DataFrame()
        for k, v in data.items():
            v = self._format_dataframe(v)
            df = pd.concat([df, v], axis=0)

        df.sort_values("Change", ascending=False, inplace=True)
        df.reset_index(inplace=True, drop=True)
        return df

    def _format_dataframe(self, df: pd.DataFrame):
        df = df.set_index("No")
        df["Marketcap_float"] = df["MarketCap"].apply(self._marketcap_to_float)
        df["Change"] = df["Change"].apply(self._format_value)
        df["Volume"] = df["Volume"].apply(self._format_value)
        df["Salespast5Y"] = df["Salespast5Y"].apply(self._format_value)
        df["EPSthisY"] = df["EPSthisY"].apply(self._format_value)
        df["EPSnextY"] = df["EPSnextY"].apply(self._format_value)
        df["EPSpast5Y"] = df["EPSpast5Y"].apply(self._format_value)
        return df

    def _marketcap_to_float(self, mcap):
        label = mcap[-1]
        stripped = float(mcap[:-1])
        if label.upper() == "K":
            val = stripped * 1_000
        elif label.upper() == "M":
            val = stripped * 1_000_000
        elif label.upper() == "B":
            val = stripped * 1_000_000_000
        return val

    def _format_value(self, val, pct_to_dec: bool = False):
        """
        Logic to convert values from a string to a float through various cases.

        Example:
        90% = 90.0 (.90 if 'pct_to_dec' is True)
        1,000,000 -> 1000000.0
        $13.50 -> 13.50

        Parameters
        ----------
        val : str
            Value to convert
        pct_to_dec : bool, optional
            Determines if a percentage value is converted in terms of decimals, by default False

        Returns
        -------
        float
            Input string returned as float.
        """

        try:
            if "%" in val:
                val = val[:-1]
                if pct_to_dec:
                    val = float(val) / 100
                else:
                    val = float(val)
        except Exception as e:
            if self.log_errors:
                print(f"[_format_values (%)]: {e}")
        try:
            if "," in val:
                val = val.replace(",", "")
                val = float(val)
        except Exception as e:
            if self.log_errors:
                print(f"[_format_values (,)]: {e}")
        try:
            if "$" in val:
                val = val[1:]
                val = float(val)
        except Exception as e:
            if self.log_errors:
                print(f"[_format_values ($)]: {e}")
        return val
