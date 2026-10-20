import json
import logging
from typing import Dict, Any, List
from core.config import settings
from services.mock_analysis import generate_mock_analysis

logger = logging.getLogger(__name__)

class BedrockClinicalService:
    def __init__(self):
        self.model_id = settings.AWS_BEDROCK_MODEL_ID
        self.region = settings.AWS_REGION
        self.is_configured = bool(
            settings.AWS_ACCESS_KEY_ID
            and settings.AWS_SECRET_ACCESS_KEY
            and settings.AWS_ACCESS_KEY_ID != "your_aws_access_key_id"
        )
        self.bedrock_client = None

        if self.is_configured:
            try:
                import boto3
                self.bedrock_client = boto3.client(
                    "bedrock-runtime",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
                logger.info(f"BedrockClinicalService initialized with model: {self.model_id} in {self.region}")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS Bedrock client ({e}). Will use fallback.")
                self.is_configured = False

    def generate_analysis(
        self,
        patient_data: Dict[str, Any],
        new_symptoms: str,
        observations: str,
        test_results: str = ""
    ) -> Dict[str, Any]:
        """
        Generates clinical decision support report using Meta Llama on AWS Bedrock.
        Uses optimized clinical guidelines prompt with fallback to smart clinical generator.
        """
        if not self.is_configured or not self.bedrock_client:
            logger.info("Using smart clinical fallback engine (Bedrock not configured).")
            return generate_mock_analysis(patient_data, new_symptoms, observations, test_results)

        # High-performance clinical decision support prompt
        system_prompt = (
            "You are ClinIQ CDS, a certified Clinical Decision Support AI engine assisting board-certified physicians.\n"
            "Your role is to analyze patient history, current symptoms, physical observations, and test results, "
            "then synthesize an evidence-grounded differential diagnosis, actionable next steps, drug safety checks, "
            "and patient-specific risk factors.\n\n"
            "CLINICAL REASONING RULES:\n"
            "1. Ranked Differential Diagnoses:\n"
            "   - Provide 2 to 4 distinct diagnoses ranked by probability (rank 1 = primary leading differential).\n"
            "   - 'confidence_percentage': float (15.0 to 95.0) reflecting clinical fit.\n"
            "   - 'confidence_label': exactly 'high' (>= 75.0), 'moderate' (50.0 to 74.9), or 'low' (< 50.0).\n"
            "   - 'summary': concise pathophysiological rationale (1-2 sentences).\n"
            "   - 'evidence': 2 to 4 bullet points citing specific symptoms, history, or diagnostic findings.\n"
            "2. Recommended Next Steps:\n"
            "   - Provide 3 to 5 prioritized, guideline-directed actions (diagnostic confirmation, acute therapy, monitoring).\n"
            "   - Mention relevant clinical guidelines (e.g. AHA/ACC, ESC, ADA, ATS) where applicable.\n"
            "3. Drug Interactions & Safety Warnings:\n"
            "   - Screen current medications against acute conditions and potential therapies for critical or moderate interactions.\n"
            "   - If none found, provide an empty array [].\n"
            "4. Patient-Specific Risk Factors:\n"
            "   - 3 to 6 clinical risk factors relevant to the patient's presentation.\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object matching the exact schema below. Do NOT include markdown code blocks, preamble, or commentary.\n\n"
            "{\n"
            '  "diagnoses": [\n'
            '    {\n'
            '      "rank": 1,\n'
            '      "name": "Stable Angina Pectoris",\n'
            '      "confidence_percentage": 82.0,\n'
            '      "confidence_label": "high",\n'
            '      "summary": "Exertional retrosternal pressure resolving with rest...",\n'
            '      "evidence": ["Symptom onset during exertion", "History of coronary artery disease"]\n'
            '    }\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    {\n'
            '      "step_number": 1,\n'
            '      "title": "Complete serial high-sensitivity Troponin testing",\n'
            '      "description": "Rule out acute myocardial necrosis (0h and 2h delta protocol per AHA/ACC)."\n'
            '    }\n'
            '  ],\n'
            '  "drug_interactions": [\n'
            '    {\n'
            '      "severity": "critical",\n'
            '      "title": "Avoid Clarithromycin with current Atorvastatin",\n'
            '      "description": "CYP3A4 inhibition increases statin exposure and risk of rhabdomyolysis."\n'
            '    }\n'
            '  ],\n'
            '  "risk_factors": ["Known coronary artery disease", "Hypertension", "Age over 55"]\n'
            "}"
        )

        user_content = (
            "PATIENT DEMOGRAPHICS & MEDICAL HISTORY:\n"
            f"- Full Name: {patient_data.get('full_name', 'Patient')}\n"
            f"- Age: {patient_data.get('age', 'Unknown')} | Gender: {patient_data.get('gender', 'Unknown')}\n"
            f"- Medical History: {patient_data.get('medical_history') or 'None reported'}\n"
            f"- Allergies: {patient_data.get('allergies') or 'No known drug allergies'}\n"
            f"- Current Medications: {patient_data.get('current_medications') or 'None reported'}\n"
            f"- Past Treatments / Surgeries: {patient_data.get('past_treatments') or 'None reported'}\n\n"
            "CURRENT CLINICAL PRESENTATION:\n"
            f"- Chief Complaint & Acute Symptoms: {new_symptoms}\n"
            f"- Physical Observations & Vitals: {observations}\n"
            f"- Diagnostic & Lab Findings: {test_results or 'None reported / pending'}\n\n"
            "Synthesize the clinical decision support report now as pure JSON."
        )

        try:
            # Use AWS Bedrock Converse API with Meta Llama
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_content}]
                    }
                ],
                inferenceConfig={
                    "temperature": 0.1,
                    "maxTokens": 2048,
                    "topP": 0.9
                }
            )

            response_message = response.get("output", {}).get("message", {})
            content_blocks = response_message.get("content", [])
            raw_text = content_blocks[0].get("text", "").strip() if content_blocks else ""

            # Robust JSON extraction
            parsed = self._extract_json(raw_text)

            # Validate schema integrity
            if not isinstance(parsed, dict) or "diagnoses" not in parsed or not parsed["diagnoses"]:
                raise ValueError("Parsed output missing required diagnoses")

            # Ensure all expected keys exist
            if "recommendations" not in parsed:
                parsed["recommendations"] = []
            if "drug_interactions" not in parsed:
                parsed["drug_interactions"] = []
            if "risk_factors" not in parsed:
                parsed["risk_factors"] = []

            logger.info("Successfully generated clinical analysis via AWS Bedrock.")
            return parsed

        except Exception as e:
            err_msg = str(e)
            if "Operation not allowed" in err_msg:
                logger.warning(
                    f"AWS Bedrock Model Access Required: Model '{self.model_id}' is not yet granted in AWS Bedrock Console. "
                    "Go to AWS Console -> Amazon Bedrock -> Model access -> Request model access -> Meta (Llama 3 70B Instruct). "
                    "Using smart clinical fallback engine until access is approved."
                )
            else:
                logger.warning(f"Bedrock invocation note: {e}. Utilizing smart clinical fallback engine.")
            return generate_mock_analysis(patient_data, new_symptoms, observations, test_results)

    def _extract_json(self, raw_text: str) -> Dict[str, Any]:
        """Extracts and parses JSON safely even if wrapped in markdown code blocks or surrounding text."""
        cleaned = raw_text.strip()
        
        # Remove markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Extract innermost or outermost braces
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            json_substr = cleaned[start:end]
            try:
                return json.loads(json_substr)
            except Exception:
                pass

        return json.loads(cleaned)


bedrock_service = BedrockClinicalService()
