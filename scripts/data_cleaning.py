import pandas as pd
import numpy as np


class DataCleaning:

    MISSING_TOKENS = {
        "",
        "unknown",
        "na",
        "n/a",
        "null",
        "none",
        "nan",
        "-",
    }

    # =========================
    # 🔹 HANDLE MISSING VALUES
    # =========================
    def handle_missing_values(self, df, strategy="mean"):
        """
        Handles missing values by filling with mean, median, mode, or dropping.
        """
        if strategy == "mean":
            df.fillna(df.mean(numeric_only=True), inplace=True)

        elif strategy == "median":
            df.fillna(df.median(numeric_only=True), inplace=True)

        elif strategy == "mode":
            df.fillna(df.mode().iloc[0], inplace=True)

        elif strategy == "drop":
            df.dropna(inplace=True)

        return df

    def standardize_missing_values(self, df):
        """Converts common placeholder strings to NaN in object columns."""
        for col in df.columns:
            if df[col].dtype == object:
                normalized = (
                    df[col]
                    .astype(str)
                    .str.strip()
                    .replace({"": np.nan})
                )
                df[col] = normalized.mask(normalized.str.lower().isin(self.MISSING_TOKENS), np.nan)
        return df

    # =========================
    # 🔹 REMOVE DUPLICATES
    # =========================
    def remove_duplicates(self, df):
        """Removes duplicate rows."""
        return df.drop_duplicates()

    # =========================
    # 🔹 FIX DATA TYPES
    # =========================
    def fix_data_types(self, df):
        """Attempts to convert columns to appropriate data types."""
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except ValueError:
                pass
        return df

    def fill_missing_values(self, df):
        """Fills missing values using median for numeric and mode for categorical columns."""
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                median_value = df[col].median(skipna=True)
                if pd.notna(median_value):
                    df[col] = df[col].fillna(median_value)
            else:
                mode = df[col].mode(dropna=True)
                fill_value = mode.iloc[0] if not mode.empty else "Unknown"
                df[col] = df[col].fillna(fill_value)
        return df

    def normalize_integer_like_columns(self, df):
        """Rounds and casts integer-like numeric columns to clean whole numbers."""
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            series = df[col].dropna()
            if series.empty:
                continue

            is_integer_like = np.all(np.isclose(series % 1, 0))
            if is_integer_like:
                df[col] = df[col].round().astype("Int64")

        if "quantity" in df.columns and pd.api.types.is_numeric_dtype(df["quantity"]):
            df["quantity"] = df["quantity"].round().astype("Int64")

        return df

    def _normalize_text_number(self, value):
        """Converts simple text numbers (e.g., 'twenty five') to digits; returns NaN on failure."""
        if not isinstance(value, str):
            return value

        text = value.strip().lower().replace("-", " ")
        if not text:
            return np.nan

        base = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
            "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
            "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        }

        parts = text.split()
        if not parts:
            return np.nan

        total = 0
        for part in parts:
            if part not in base:
                return np.nan
            total += base[part]

        return total

    def enforce_strict_rules(self, df):
        """Enforces strict validations for common fields and removes invalid rows."""
        df = df.copy()

        # Normalize common placeholder tokens
        df = self.standardize_missing_values(df)

        # Email validation
        email_cols = [c for c in df.columns if "email" in c.lower()]
        for col in email_cols:
            original = df[col]
            cleaned = df[col].astype(str).str.strip()
            email_mask = cleaned.str.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", na=False)
            df[col] = original.where(email_mask, np.nan)

        # Phone validation (10 digits)
        phone_cols = [c for c in df.columns if "phone" in c.lower()]
        for col in phone_cols:
            original = df[col]
            digits = df[col].astype(str).str.replace(r"\D", "", regex=True)
            phone_mask = digits.str.len().eq(10)
            # Keep original if valid, otherwise try fixed digits
            df[col] = original.where(phone_mask, digits)
            # If still invalid after fix, set to NaN
            df.loc[~phone_mask, col] = np.nan

        # Age validation (18-80)
        age_cols = [c for c in df.columns if c.lower() == "age" or "age" in c.lower()]
        for col in age_cols:
            original = df[col]
            original_numeric = pd.to_numeric(original, errors="coerce")
            normalized = df[col].apply(self._normalize_text_number)
            normalized_numeric = pd.to_numeric(normalized, errors="coerce")

            original_mask = original_numeric.between(18, 80)
            normalized_mask = normalized_numeric.between(18, 80)

            # Keep valid numeric originals, otherwise use normalized numeric if valid
            df[col] = original_numeric.where(original_mask, normalized_numeric)
            df.loc[~(original_mask | normalized_mask), col] = np.nan

        # Salary/amount validation
        amount_cols = [c for c in df.columns if "salary" in c.lower() or "amount" in c.lower()]
        for col in amount_cols:
            original = df[col]
            numeric = pd.to_numeric(df[col], errors="coerce")
            valid_mask = numeric.notna()
            df[col] = original.where(valid_mask, numeric)
            df.loc[~valid_mask, col] = np.nan

        # Date validation
        date_cols = [c for c in df.columns if "date" in c.lower()]
        for col in date_cols:
            original = df[col]
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            parsed_alt = pd.to_datetime(df[col], errors="coerce", dayfirst=False)
            fixed = parsed.fillna(parsed_alt)
            fixed_str = fixed.dt.strftime("%Y-%m-%d")
            valid_mask = fixed.notna()
            # Keep original if valid; otherwise use fixed string
            df[col] = original.where(valid_mask, fixed_str)
            df.loc[~valid_mask, col] = np.nan

        # Normalize department-like columns
        dept_cols = [c for c in df.columns if "department" in c.lower()]
        for col in dept_cols:
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col].str.lower().isin({"unknown", "nan", "none"}), col] = np.nan

        # Do NOT drop rows here; keep data and null out invalid fields only

        df = self.remove_duplicates(df)
        return df.reset_index(drop=True)

    # =========================
    # 🔹 MAIN CLEAN FUNCTION
    # =========================
    def clean_data(self, df, impute_missing: bool = False):
        """Applies core cleaning steps. Imputation is optional."""
        df = df.copy()
        df = self.standardize_missing_values(df)
        df = self.fix_data_types(df)
        if impute_missing:
            df = self.fill_missing_values(df)
        df = self.normalize_integer_like_columns(df)
        df = self.remove_duplicates(df)
        return df.reset_index(drop=True)