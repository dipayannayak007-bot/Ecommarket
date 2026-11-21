"""
ILLUSTRATIVE SYNTHETIC DEMONSTRATION DATA -- NOT REAL SURVEY RESPONSES
=====================================================================

This script generates a fictional, deterministic sample survey for an
academic e-commerce project. Every respondent and every answer is
produced locally by ``random.Random(20241120)``. No human took this
survey, no responses were collected, and no network access is performed.

The resulting ``data/sample_survey_responses.csv`` must always be
labelled as ILLUSTRATIVE SYNTHETIC DEMONSTRATION DATA. It exists only to
exercise a data-cleaning / encoding / K-means demonstration pipeline:
three latent behavioural groups (deal-driven, EMI aspirants, cautious)
are planted with realistic noise so clustering has genuine structure to
recover. It must NOT be reported as evidence about real consumers and
must NOT be mixed with real or restricted microdata.

Re-running this script overwrites the sample CSV with byte-identical
output.
"""

import csv
import random
from pathlib import Path

SEED = 20241120
N_PER_GROUP = 20
# Exactly 3 or 4 of each group's 20 answers per behavioural field are
# randomly selected as noise: 15%-20% deviation, as intended for a
# realistic but clearly structured demonstration sample.
NOISE_COUNTS = {
    "spend_band_inr": 3,
    "price_sensitivity": 3,
    "discount_importance": 3,
    "emi_influence": 4,
    "exchange_influence": 4,
    "delivery_cost_influence": 4,
}

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "data" / "sample_survey_responses.csv"

# Must match data/survey_template.csv exactly, including order.
HEADER = [
    "respondent_id",
    "state_ut",
    "residence_type",
    "age_band",
    "online_purchase_12m",
    "preferred_category",
    "purchase_frequency_12m",
    "spend_band_inr",
    "price_sensitivity",
    "discount_importance",
    "emi_influence",
    "exchange_influence",
    "delivery_cost_influence",
    "consent",
]

GROUP_ORDER = ("deal-driven", "EMI aspirants", "cautious")

STATES_UT = [
    ("Uttar Pradesh", 15),
    ("Maharashtra", 13),
    ("Bihar", 0),  # placeholder removed below; kept out of output
    ("Karnataka", 9),
    ("Tamil Nadu", 9),
    ("Telangana", 6),
    ("West Bengal", 7),
    ("Gujarat", 7),
    ("Kerala", 5),
    ("Rajasthan", 6),
    ("Punjab", 4),
    ("Odisha", 4),
    ("Assam", 3),
    ("Delhi", 8),
    ("Chandigarh", 2),
]
# Only the 14 sanctioned states/UTs are used; the placeholder above is
# filtered so the allowed-value list stays explicit and auditable.
STATES_UT = [(name, weight) for name, weight in STATES_UT if weight > 0]

AGE_BANDS = ["Under 18", "18-24", "25-34", "35-44", "45-54", "55+"]

SPEND_BANDS = [
    "Below 1000",
    "1000-4999",
    "5000-14999",
    "15000-29999",
    "30000-59999",
    "60000+",
]

CATEGORIES = [
    "Smartphone",
    "Laptop or Computer",
    "TV",
    "Large Appliance",
    "Small Appliance",
    "Accessories",
    "Other",
    "Not Applicable",
]

PRICE_LEVELS = ["Not at all", "Slightly", "Moderately", "Very", "Extremely"]
EMI_LEVELS = ["Not at all", "A little", "Somewhat", "A lot", "Not eligible / Unsure"]
EXCHANGE_LEVELS = ["Not at all", "A little", "Somewhat", "A lot", "Not applicable"]
DELIVERY_LEVELS = ["Not at all", "A little", "Somewhat", "A lot"]

# Behavioural tendencies. Each field has a weighted "tendency" distribution
# and an explicit "noise" pool used on 15%-20% of answers.
TENDENCIES = {
    "deal-driven": {
        "spend_band_inr": {
            "tendency": [("1000-4999", 40), ("5000-14999", 60)],
            "noise": ["Below 1000", "15000-29999", "30000-59999", "60000+"],
        },
        "price_sensitivity": {
            "tendency": [("Very", 55), ("Extremely", 45)],
            "noise": ["Not at all", "Slightly", "Moderately"],
        },
        "discount_importance": {
            "tendency": [("4", 35), ("5", 65)],
            "noise": ["1", "2", "3"],
        },
        "emi_influence": {
            "tendency": [("A little", 55), ("Somewhat", 45)],
            "noise": ["Not at all", "A lot"],
        },
        "exchange_influence": {
            "tendency": [("Somewhat", 35), ("A lot", 65)],
            "noise": ["Not at all", "A little"],
        },
        "delivery_cost_influence": {
            "tendency": [("Somewhat", 40), ("A lot", 60)],
            "noise": ["Not at all", "A little"],
        },
    },
    "EMI aspirants": {
        "spend_band_inr": {
            "tendency": [
                ("15000-29999", 40),
                ("30000-59999", 40),
                ("60000+", 20),
            ],
            "noise": ["Below 1000", "1000-4999", "5000-14999"],
        },
        "price_sensitivity": {
            "tendency": [("Moderately", 55), ("Very", 45)],
            "noise": ["Not at all", "Slightly", "Extremely"],
        },
        "discount_importance": {
            "tendency": [("3", 45), ("4", 55)],
            "noise": ["1", "2", "5"],
        },
        "emi_influence": {
            "tendency": [("Somewhat", 10), ("A lot", 90)],
            "noise": ["Not at all", "A little"],
        },
        "exchange_influence": {
            "tendency": [("A little", 45), ("Somewhat", 55)],
            "noise": ["Not at all", "A lot"],
        },
        "delivery_cost_influence": {
            "tendency": [("Not at all", 45), ("A little", 55)],
            "noise": ["Somewhat", "A lot"],
        },
    },
    "cautious": {
        "spend_band_inr": {
            "tendency": [
                ("Below 1000", 30),
                ("1000-4999", 45),
                ("5000-14999", 25),
            ],
            "noise": ["15000-29999", "30000-59999", "60000+"],
        },
        "price_sensitivity": {
            "tendency": [("Slightly", 55), ("Moderately", 45)],
            "noise": ["Not at all", "Very", "Extremely"],
        },
        "discount_importance": {
            "tendency": [("1", 55), ("2", 45)],
            "noise": ["3", "4", "5"],
        },
        "emi_influence": {
            "tendency": [("Not at all", 60), ("A little", 40)],
            "noise": ["Somewhat", "A lot"],
        },
        "exchange_influence": {
            "tendency": [("Not at all", 60), ("A little", 40)],
            "noise": ["Somewhat", "A lot"],
        },
        "delivery_cost_influence": {
            "tendency": [("Not at all", 55), ("A little", 45)],
            "noise": ["Somewhat", "A lot"],
        },
    },
}

AGE_BY_GROUP = {
    "deal-driven": [
        ("18-24", 15),
        ("25-34", 35),
        ("35-44", 30),
        ("45-54", 15),
        ("55+", 5),
    ],
    "EMI aspirants": [
        ("18-24", 15),
        ("25-34", 40),
        ("35-44", 35),
        ("45-54", 10),
    ],
    "cautious": [
        ("Under 18", 5),
        ("18-24", 15),
        ("25-34", 25),
        ("35-44", 25),
        ("45-54", 20),
        ("55+", 10),
    ],
}

CATEGORY_BY_GROUP = {
    "deal-driven": [
        ("Smartphone", 20),
        ("Laptop or Computer", 10),
        ("TV", 10),
        ("Large Appliance", 5),
        ("Small Appliance", 20),
        ("Accessories", 20),
        ("Other", 15),
    ],
    "EMI aspirants": [
        ("Smartphone", 30),
        ("Laptop or Computer", 30),
        ("TV", 15),
        ("Large Appliance", 15),
        ("Small Appliance", 5),
        ("Accessories", 5),
    ],
    "cautious": [
        ("Smartphone", 10),
        ("Laptop or Computer", 5),
        ("TV", 10),
        ("Small Appliance", 25),
        ("Accessories", 25),
        ("Other", 25),
    ],
}

URBAN_PROBABILITY_BY_SPEND = {
    "Below 1000": 0.40,
    "1000-4999": 0.60,
    "5000-14999": 0.75,
    "15000-29999": 0.90,
    "30000-59999": 0.95,
    "60000+": 0.98,
}

FREQUENCY_BY_SPEND = {
    "Below 1000": [("1", 45), ("2-3", 40), ("4-5", 12), ("6+", 3)],
    "1000-4999": [("1", 30), ("2-3", 45), ("4-5", 20), ("6+", 5)],
    "5000-14999": [("1", 18), ("2-3", 42), ("4-5", 30), ("6+", 10)],
    "15000-29999": [("1", 10), ("2-3", 30), ("4-5", 40), ("6+", 20)],
    "30000-59999": [("1", 5), ("2-3", 25), ("4-5", 40), ("6+", 30)],
    "60000+": [("1", 3), ("2-3", 18), ("4-5", 42), ("6+", 37)],
}

ALLOWED = {
    "state_ut": {name for name, _ in STATES_UT},
    "residence_type": {"Urban", "Rural"},
    "age_band": set(AGE_BANDS),
    "online_purchase_12m": {"Yes", "No"},
    "preferred_category": set(CATEGORIES),
    "purchase_frequency_12m": {"0", "1", "2-3", "4-5", "6+"},
    "spend_band_inr": set(SPEND_BANDS),
    "price_sensitivity": set(PRICE_LEVELS),
    "discount_importance": {"1", "2", "3", "4", "5"},
    "emi_influence": set(EMI_LEVELS),
    "exchange_influence": set(EXCHANGE_LEVELS),
    "delivery_cost_influence": set(DELIVERY_LEVELS),
    "consent": {"Yes"},
}


def weighted_choice(rng, distribution):
    """Pick one value from an explicit list of (value, integer weight)."""
    values, weights = zip(*distribution)
    return rng.choices(values, weights=weights, k=1)[0]


def behavioural_answer(rng, field, group, noisy):
    """Return a group-typical answer, or off-tendency noise when flagged."""
    spec = TENDENCIES[group][field]
    if noisy:
        return rng.choice(spec["noise"])
    return weighted_choice(rng, spec["tendency"])


def make_row(rng, group, respondent_id, noise_flags):
    """Create one fictional respondent as an ordered 14-field record."""
    spend = behavioural_answer(rng, "spend_band_inr", group, noise_flags["spend_band_inr"])
    price_sensitivity = behavioural_answer(
        rng, "price_sensitivity", group, noise_flags["price_sensitivity"]
    )
    discount = behavioural_answer(
        rng, "discount_importance", group, noise_flags["discount_importance"]
    )
    emi = behavioural_answer(rng, "emi_influence", group, noise_flags["emi_influence"])
    exchange = behavioural_answer(
        rng, "exchange_influence", group, noise_flags["exchange_influence"]
    )
    delivery = behavioural_answer(
        rng, "delivery_cost_influence", group, noise_flags["delivery_cost_influence"]
    )

    age = weighted_choice(rng, AGE_BY_GROUP[group])
    online = "Yes" if rng.random() < (0.35 if age == "Under 18" else 0.90) else "No"
    if online == "No":
        # No purchases in 12 months means no online spend to report.
        spend = "Below 1000"
    if online == "No":
        category = (
            "Not Applicable"
            if rng.random() < 0.80
            else weighted_choice(rng, CATEGORY_BY_GROUP[group])
        )
        frequency = "0"
    else:
        category = weighted_choice(rng, CATEGORY_BY_GROUP[group])
        frequency = weighted_choice(rng, FREQUENCY_BY_SPEND[spend])

    residence = (
        "Urban"
        if rng.random() < URBAN_PROBABILITY_BY_SPEND[spend]
        else "Rural"
    )

    values = {
        "respondent_id": respondent_id,
        "state_ut": weighted_choice(rng, STATES_UT),
        "residence_type": residence,
        "age_band": age,
        "online_purchase_12m": online,
        "preferred_category": category,
        "purchase_frequency_12m": frequency,
        "spend_band_inr": spend,
        "price_sensitivity": price_sensitivity,
        "discount_importance": discount,
        "emi_influence": emi,
        "exchange_influence": exchange,
        "delivery_cost_influence": delivery,
        "consent": "Yes",
    }
    return {field: values[field] for field in HEADER}


def choose_missing_markers(rng, groups):
    """Choose 3 EMI-unsure and 3 exchange-not-applicable rows, without overlap."""
    cautious = [i for i, group in enumerate(groups) if group == "cautious"]
    others = [i for i, group in enumerate(groups) if group != "cautious"]

    emi_missing = set(rng.sample(cautious, 2)) | set(rng.sample(others, 1))
    remaining_cautious = [i for i in cautious if i not in emi_missing]
    remaining_others = [i for i in others if i not in emi_missing]
    exchange_missing = set(rng.sample(remaining_cautious, 2)) | set(
        rng.sample(remaining_others, 1)
    )
    return emi_missing, exchange_missing


def build_rows():
    """Generate the shuffled 60-row sample plus its hidden group labels."""
    rng = random.Random(SEED)
    groups = (
        ["deal-driven"] * N_PER_GROUP
        + ["EMI aspirants"] * N_PER_GROUP
        + ["cautious"] * N_PER_GROUP
    )
    rng.shuffle(groups)
    assert len(set(groups[:6])) >= 2, "latent groups must be interleaved"

    # Choose which rows carry noise for each field, per latent group.
    noise_rows = {}
    for group in GROUP_ORDER:
        positions = [i for i, label in enumerate(groups) if label == group]
        noise_rows[group] = {
            field: set(rng.sample(positions, quota))
            for field, quota in NOISE_COUNTS.items()
        }

    rows = []
    for number, group in enumerate(groups, start=1):
        flags = {
            field: (number - 1) in noise_rows[group][field] for field in NOISE_COUNTS
        }
        rows.append(make_row(rng, group, f"R{number:03d}", flags))

    emi_missing, exchange_missing = choose_missing_markers(rng, groups)
    for index in emi_missing:
        rows[index]["emi_influence"] = "Not eligible / Unsure"
    for index in exchange_missing:
        rows[index]["exchange_influence"] = "Not applicable"

    return rows, groups


def validate(rows):
    """Fail loudly if the generated sample breaks the published contract."""
    assert len(rows) == 60, f"expected 60 rows, got {len(rows)}"
    assert all(list(row.keys()) == HEADER for row in rows), "column order changed"
    assert [row["respondent_id"] for row in rows] == [
        f"R{number:03d}" for number in range(1, 61)
    ], "respondent IDs are not R001..R060"

    for field, allowed in ALLOWED.items():
        offenders = [
            (row["respondent_id"], row[field])
            for row in rows
            if row[field] not in allowed
        ]
        assert not offenders, f"invalid {field} values: {offenders}"

    assert sum(r["consent"] == "Yes" for r in rows) == 60, "consent must be Yes"
    assert (
        sum(r["emi_influence"] == "Not eligible / Unsure" for r in rows) == 3
    ), "expected exactly 3 EMI-unsure rows"
    assert (
        sum(r["exchange_influence"] == "Not applicable" for r in rows) == 3
    ), "expected exactly 3 exchange-not-applicable rows"


def print_summary(rows, groups):
    """Print compact, human-readable evidence of the planted group tendencies."""
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT).as_posix()} (60 rows, {len(HEADER)} columns)")
    for group in GROUP_ORDER:
        subset = [row for row, label in zip(rows, groups) if label == group]
        n = len(subset)
        if group == "deal-driven":
            detail = (
                f"discount 4-5={sum(r['discount_importance'] in {'4', '5'} for r in subset)}, "
                f"exchange high={sum(r['exchange_influence'] in {'Somewhat', 'A lot'} for r in subset)}, "
                f"delivery high={sum(r['delivery_cost_influence'] in {'Somewhat', 'A lot'} for r in subset)}, "
                f"price high={sum(r['price_sensitivity'] in {'Very', 'Extremely'} for r in subset)}, "
                f"low/mid spend={sum(r['spend_band_inr'] in {'Below 1000', '1000-4999', '5000-14999'} for r in subset)}"
            )
        elif group == "EMI aspirants":
            detail = (
                f"EMI A lot={sum(r['emi_influence'] == 'A lot' for r in subset)}, "
                f"discount 3-4={sum(r['discount_importance'] in {'3', '4'} for r in subset)}, "
                f"delivery low={sum(r['delivery_cost_influence'] in {'Not at all', 'A little'} for r in subset)}, "
                f"high spend={sum(r['spend_band_inr'] in {'15000-29999', '30000-59999', '60000+'} for r in subset)}"
            )
        else:
            detail = (
                f"discount 1-2={sum(r['discount_importance'] in {'1', '2'} for r in subset)}, "
                f"low influences={sum(r['delivery_cost_influence'] in {'Not at all', 'A little'} for r in subset)}, "
                f"price low={sum(r['price_sensitivity'] in {'Slightly', 'Moderately'} for r in subset)}, "
                f"low spend={sum(r['spend_band_inr'] in {'Below 1000', '1000-4999', '5000-14999'} for r in subset)}"
            )
        print(f"  {group:<14} n={n:>2}  {detail}")
    print(
        "  special handling: emi 'Not eligible / Unsure'=3, "
        "exchange 'Not applicable'=3, consent=Yes 60/60"
    )
    print("  DATA ARE ILLUSTRATIVE SYNTHETIC DEMONSTRATION DATA -- NOT REAL RESPONSES")


def main():
    rows, groups = build_rows()
    validate(rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    # Read the file back so validation covers bytes on disk, not just memory.
    with OUTPUT_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == HEADER, "on-disk header does not match template"
        reread = list(reader)
    assert reread == rows, "on-disk rows differ from generated rows"
    validate(reread)

    print_summary(reread, groups)


if __name__ == "__main__":
    main()
