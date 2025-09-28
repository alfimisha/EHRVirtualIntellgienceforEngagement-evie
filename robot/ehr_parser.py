import pandas as pd


# load Synthea CSVs
patients_df = pd.read_csv("patients.csv")
observations_df = pd.read_csv("observations.csv")
conditions_df = pd.read_csv("conditions.csv")

# demographic info!
patients_df['BIRTHDATE'] = pd.to_datetime(patients_df['BIRTHDATE'])
today = pd.to_datetime("today")
patients_df['age'] = (today - patients_df['BIRTHDATE']).dt.days // 365

# Helper function to format patient's name
def get_full_name(patient_row):
    first = patient_row.get('FIRST', '')
    last = patient_row.get('LAST', '')
    return f"{first} {last}".strip() or "Unknown"

def get_patient_context(patient_id):
    # Make sure that patient_id is a string 
    patient_id = str(patient_id)
    
    patient = patients_df.loc[patients_df["Id"] == patient_id]
    if patient.empty:
        return f"No patient found with ID {patient_id}"
    patient = patient.iloc[0]
    
    name = get_full_name(patient)
    age = patient.get("age", "Unknown")
    gender = patient.get("GENDER", "Unknown")
    race = patient.get("RACE", "Unknown")
    ethnicity = patient.get("ETHNICITY", "Unknown")
    
    # Filter by year!!
    patient_obs = observations_df[observations_df["PATIENT"] == patient_id].copy()
    patient_obs['DATE'] = pd.to_datetime(patient_obs['DATE']).dt.tz_localize(None)
    
    three_years_ago = today - pd.DateOffset(years=3)
    recent_obs = patient_obs[patient_obs['DATE'] >= three_years_ago]
    
    # Keep only relevant measurements
    relevant_codes = [
        "Body mass index (BMI) [Ratio]",
        "Systolic Blood Pressure",
        "Diastolic Blood Pressure",
        "Heart rate",
        "Respiratory rate",
        "Hemoglobin [Mass/volume] in Blood",
        "Platelets [#/volume] in Blood by Automated count"
    ]
    recent_obs = recent_obs[recent_obs['DESCRIPTION'].isin(relevant_codes)]
    
    if not recent_obs.empty:
        vitals_summary = ", ".join(
            f"{row['DESCRIPTION']}: {row['VALUE']}" 
            for _, row in recent_obs.iterrows()
        )
    else:
        vitals_summary = "No relevant vitals recorded in the past 3 years"
    
    patient_conditions = conditions_df[conditions_df["PATIENT"] == patient_id]
    conditions_summary = ", ".join(patient_conditions["DESCRIPTION"].unique()) \
        if not patient_conditions.empty else "No conditions recorded"
    
    # Formatted summary
    summary = f"""
Patient Summary:
Name: {name}
Age: {age}, Gender: {gender}, Race: {race}, Ethnicity: {ethnicity}

Vitals (last 3 years): {vitals_summary}
Conditions: {conditions_summary}
"""
    return summary.strip()

# Sample patient
if __name__ == "__main__":
    # Patient ID from dataset
    example_patient_id = '184668ad-08d8-2c05-cb16-c7040f00b848'
    print(get_patient_context(example_patient_id))
