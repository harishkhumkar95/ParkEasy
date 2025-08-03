# retrain_model.py
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Load your synthetic or cleaned dataset
df = pd.read_csv("Cleaned_Parking_Dublin_V2_synthetic.csv")  # Or your real dataset

# Extract features
df['hour'] = pd.to_datetime(df['time']).dt.hour
df['weekday'] = pd.to_datetime(df['date']).dt.weekday

X = df[['lat', 'lon', 'hour', 'weekday']]
y = df['availability']

# Train model
model = DecisionTreeClassifier()
model.fit(X, y)

# Save using your scikit-learn version (1.7.1)
joblib.dump(model, "parking_model.pkl")

print("✅ Model retrained and saved using local sklearn version.")
