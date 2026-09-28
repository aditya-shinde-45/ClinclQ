"""Mock AI analysis generator for clinical decision support"""
import random
from typing import List
from models.schemas import DiagnosisResponse, RecommendationResponse, DrugInteractionResponse


def generate_mock_analysis(patient_data: dict, symptoms: str, observations: str) -> dict:
    """Generate mock clinical analysis data"""
    
    # Sample diagnoses pool
    diagnoses_pool = [
        {
            "name": "Stable angina",
            "summary": "Exertional chest pressure resolving with rest is consistent with chronic coronary syndrome.",
            "evidence": ["Known coronary artery disease", "Symptoms are exertional and resolve with rest", "Nonspecific ST changes without acute ischemic pattern"]
        },
        {
            "name": "Heart failure exacerbation",
            "summary": "Dyspnea and peripheral edema may indicate early volume overload; BNP and imaging are pending.",
            "evidence": ["Dyspnea on exertion", "Mild bilateral ankle edema", "Previous ejection fraction 52%"]
        },
        {
            "name": "Symptomatic anemia",
            "summary": "Prior iron-deficiency anemia could contribute to dyspnea; current blood count is not available.",
            "evidence": ["History of iron-deficiency anemia", "Hemoglobin 11.2 g/dL in February", "Fatigue reported during exertion"]
        },
        {
            "name": "Acute coronary syndrome",
            "summary": "Chest pain with risk factors requires urgent evaluation to exclude acute MI.",
            "evidence": ["Cardiovascular risk factors present", "New-onset chest pain", "Troponin testing needed"]
        },
        {
            "name": "Pulmonary embolism",
            "summary": "Acute dyspnea with risk factors warrants PE evaluation.",
            "evidence": ["Sudden onset dyspnea", "Risk factors for thrombosis", "D-dimer and imaging needed"]
        },
        {
            "name": "Pneumonia",
            "summary": "Respiratory symptoms with fever suggest possible pulmonary infection.",
            "evidence": ["Productive cough", "Elevated temperature", "Chest X-ray shows infiltrate"]
        }
    ]
    
    # Pick 3 random diagnoses
    selected = random.sample(diagnoses_pool, min(3, len(diagnoses_pool)))
    
    diagnoses = []
    for i, diag in enumerate(selected):
        confidence = random.randint(45, 85) if i > 0 else random.randint(70, 90)
        
        if confidence >= 70:
            label = "high"
        elif confidence >= 50:
            label = "needs_review"
        else:
            label = "low"
        
        diagnoses.append(DiagnosisResponse(
            rank=i + 1,
            name=diag["name"],
            confidence_percentage=float(confidence),
            confidence_label=label,
            summary=diag["summary"],
            evidence=diag["evidence"]
        ))
    
    # Sample recommendations
    recommendations_pool = [
        ("Complete serial high-sensitivity troponin testing", "Exclude acute myocardial injury before outpatient management."),
        ("Obtain BNP and chest radiograph", "Assess possible volume overload given dyspnea and peripheral edema."),
        ("Continue current aspirin and statin therapy", "Review antianginal optimization after acute causes are excluded."),
        ("Order complete blood count and iron studies", "Evaluate for anemia as contributing factor to symptoms."),
        ("Arrange stress echocardiography", "Assess for inducible ischemia and ventricular function under stress."),
        ("Schedule pulmonary function testing", "Rule out chronic obstructive pulmonary disease or restrictive lung disease."),
        ("Initiate diuretic therapy", "Consider low-dose furosemide if volume overload is confirmed."),
        ("Consult cardiology for risk stratification", "Specialist evaluation recommended given symptom progression.")
    ]
    
    selected_recs = random.sample(recommendations_pool, min(3, len(recommendations_pool)))
    recommendations = [
        RecommendationResponse(
            step_number=i + 1,
            title=rec[0],
            description=rec[1]
        ) for i, rec in enumerate(selected_recs)
    ]
    
    # Drug interactions (randomly include or not)
    drug_interactions = []
    if random.random() > 0.5:
        interactions_pool = [
            {
                "severity": "critical",
                "title": "Avoid adding clarithromycin with current atorvastatin 40 mg",
                "description": "Concurrent use can substantially increase atorvastatin exposure and risk of myopathy. Choose an alternative antibiotic or temporarily withhold atorvastatin under clinician guidance."
            },
            {
                "severity": "caution",
                "title": "Monitor potassium with ACE inhibitor and potassium supplements",
                "description": "Combination may lead to hyperkalemia. Check serum potassium levels within 1-2 weeks."
            },
            {
                "severity": "critical",
                "title": "Contraindication: NSAIDs with warfarin therapy",
                "description": "Concurrent use significantly increases bleeding risk. Use alternative analgesic such as acetaminophen."
            }
        ]
        selected_interaction = random.choice(interactions_pool)
        drug_interactions.append(DrugInteractionResponse(**selected_interaction))
    
    # Risk factors
    risk_factors_pool = [
        "Known coronary artery disease",
        "Hypertension",
        "Hyperlipidemia",
        "Age over 55",
        "Type 2 diabetes",
        "Smoking history",
        "Family history of CAD",
        "Obesity (BMI > 30)"
    ]
    risk_factors = random.sample(risk_factors_pool, min(4, len(risk_factors_pool)))
    
    return {
        "diagnoses": [d.model_dump() for d in diagnoses],
        "recommendations": [r.model_dump() for r in recommendations],
        "drug_interactions": [di.model_dump() for di in drug_interactions],
        "risk_factors": risk_factors
    }
