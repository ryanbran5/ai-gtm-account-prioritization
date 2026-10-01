import pandas as pd
from pathlib import Path


# -----------------------------
# File paths
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "accounts.csv"
OUTPUT_FILE = BASE_DIR / "data" / "scored_accounts.csv"


# -----------------------------
# Helper functions
# -----------------------------

def is_yes(value):
    return str(value).strip().lower() == "yes"


def has_value(value):
    return pd.notna(value) and str(value).strip() != ""


# -----------------------------
# ICP Fit Score — 50 points
# -----------------------------

def score_retailer_complexity(retailer_count):
    if pd.isna(retailer_count):
        return 0

    count = int(retailer_count)

    if count >= 4:
        return 15
    elif count == 3:
        return 10
    elif count == 2:
        return 6
    elif count == 1:
        return 3

    return 0


def score_product_complexity(product_breadth):
    mapping = {
        "Low": 3,
        "Medium": 8,
        "High": 15,
    }

    return mapping.get(str(product_breadth).strip(), 0)


def score_company_scale(company_size):
    mapping = {
        "Mid-Market": 4,
        "Upper Mid-Market": 7,
        "Enterprise": 10,
    }

    return mapping.get(str(company_size).strip(), 0)


def score_use_case_alignment(alignment):
    mapping = {
        "Weak": 2,
        "Moderate": 6,
        "Strong": 10,
    }

    return mapping.get(str(alignment).strip(), 0)


# -----------------------------
# Buying Signal Score — 30 points
# -----------------------------

def score_buying_signals(row):
    score = 0

    # Ecommerce / retail initiative
    if (
        is_yes(row["digital_transformation_signal"])
        or is_yes(row["retail_media_signal"])
    ):
        score += 10

    # AI / data transformation
    if is_yes(row["ai_signal"]):
        score += 8

    # Relevant hiring
    if is_yes(row["ecommerce_hiring_signal"]):
        score += 6

    # Expansion / growth trigger
    if is_yes(row["growth_signal"]):
        score += 6

    return score


# -----------------------------
# Sales Accessibility — 20 points
# -----------------------------

def score_sales_accessibility(row):
    score = 0

    if has_value(row["primary_persona"]):
        score += 8

    if has_value(row["secondary_persona"]):
        score += 5

    if str(row["personalization_trigger"]).strip() == "Strong":
        score += 4

    if str(row["evidence_quality"]).strip() == "High":
        score += 3

    return score


# -----------------------------
# Priority Tier
# -----------------------------

def assign_priority_tier(total_score):
    if total_score >= 85:
        return "Tier 1A"
    elif total_score >= 75:
        return "Tier 1B"
    elif total_score >= 60:
        return "Tier 2"
    else:
        return "Tier 3"


# -----------------------------
# Score one account
# -----------------------------

def score_account(row):

    # Do not score unverified research
    if str(row["research_status"]).strip().lower() != "verified":
        return pd.Series({
            "icp_fit_score": pd.NA,
            "buying_signal_score": pd.NA,
            "sales_accessibility_score": pd.NA,
            "total_score": pd.NA,
            "priority_tier": "Not Scored"
        })

    icp_fit_score = (
        score_retailer_complexity(row["retailer_count"])
        + score_product_complexity(row["product_breadth"])
        + score_company_scale(row["company_size_band"])
        + score_use_case_alignment(row["use_case_alignment"])
    )

    buying_signal_score = score_buying_signals(row)

    sales_accessibility_score = score_sales_accessibility(row)

    total_score = (
        icp_fit_score
        + buying_signal_score
        + sales_accessibility_score
    )

    priority_tier = assign_priority_tier(total_score)

    return pd.Series({
        "icp_fit_score": icp_fit_score,
        "buying_signal_score": buying_signal_score,
        "sales_accessibility_score": sales_accessibility_score,
        "total_score": total_score,
        "priority_tier": priority_tier
    })


# -----------------------------
# Main program
# -----------------------------

def main():

    accounts = pd.read_csv(INPUT_FILE)

    scoring_results = accounts.apply(score_account, axis=1)

    for column in scoring_results.columns:
        accounts[column] = scoring_results[column]

    accounts.to_csv(OUTPUT_FILE, index=False)

    verified_count = (
        accounts["research_status"]
        .astype(str)
        .str.lower()
        .eq("verified")
        .sum()
    )

    print("GTM account scoring complete.")
    print(f"Accounts loaded: {len(accounts)}")
    print(f"Verified accounts scored: {verified_count}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
