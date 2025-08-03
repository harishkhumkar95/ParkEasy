# retrain_model.py
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Load correct CSV
df = pd.read_csv("Cleaned_Parking_Dublin_V2_synthetic.csv")

# Extract features
df['hour'] = pd.to_datetime(df['time'], errors='coerce').dt.hour
df['weekday'] = pd.to_datetime(df['date'], errors='coerce').dt.weekday
df.dropna(subset=['hour', 'weekday', 'lat', 'lon', 'availability'], inplace=True)

X = df[['lat', 'lon', 'hour', 'weekday']]
y = df['availability']

# Train and export using your local env version
model = DecisionTreeClassifier()
model.fit(X, y)

joblib.dump(model, "parking_model.pkl")
print("✅ Model retrained and saved using local sklearn version.")
