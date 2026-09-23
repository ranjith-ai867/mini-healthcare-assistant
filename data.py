"""
data.py
-------
Generates and loads the synthetic healthcare dataset used by the
Mini Healthcare Assistant. All data is fictional (created with Faker) —
no real patient information is used anywhere in this project.
"""

import os
import random

import pandas as pd
from faker import Faker

DIETARY_PREFERENCES = ["veg", "non-veg", "vegan"]

MEDICAL_CONDITIONS = [
    "Type 2 Diabetes",
    "Hypertension",
    "Prediabetes",
    "Obesity",
    "High Cholesterol",
    "No known condition",
]

CGM_MIN, CGM_MAX = 80, 300


def generate_dataset(n: int = 20, seed: int = 42) -> pd.DataFrame:
    """Create `n` synthetic user profiles as a DataFrame."""
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    rows = []
    for i in range(1, n + 1):
        rows.append(
            {
                "user_id": f"U{i:03d}",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "city": fake.city(),
                "dietary_preference": random.choice(DIETARY_PREFERENCES),
                "medical_condition": random.choice(MEDICAL_CONDITIONS),
                "cgm_reading": random.randint(CGM_MIN, CGM_MAX),
            }
        )
    return pd.DataFrame(rows)


def ensure_dataset(path: str = "data/synthetic_users.csv", n: int = 20) -> str:
    """Create the CSV dataset if it doesn't already exist. Returns the path."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(path):
        df = generate_dataset(n)
        df.to_csv(path, index=False)

    return path


def load_users(path: str = "data/synthetic_users.csv") -> pd.DataFrame:
    """Load the dataset, keeping user_id as a string (e.g. 'U001')."""
    return pd.read_csv(path, dtype={"user_id": str})


def get_user(df: pd.DataFrame, user_id: str):
    """Look up a single user by ID. Returns a dict, or None if not found."""
    if not user_id:
        return None
    match = df[df["user_id"] == user_id.strip().upper()]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


if __name__ == "__main__":
    # Quick manual run: `python data.py` regenerates the CSV and prints it.
    path = ensure_dataset()
    print(f"Dataset written to {path}\n")
    print(load_users(path).to_string(index=False))
