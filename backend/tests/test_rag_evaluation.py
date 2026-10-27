import pytest
from typing import List, Dict, Any
from services.rag_retrieval_service import rag_retrieval_service
from services.rag_ingestion_service import resolve_chunk_db
from core.database import get_db, local_db


# ---------------------------------------------------------------------------
# 25 CLINICAL RAG EVALUATION BENCHMARK TEST CASES
# ---------------------------------------------------------------------------
EVALUATION_CASES = [
    {
        "id": "EVAL-01",
        "category": "Exact Fact Retrieval",
        "patient_id": "CLQ-HOSP-0001",
        "query": "Angioplasty procedure for heart disease",
        "expected_terms": ["angioplasty", "heart disease"],
        "expect_hit": True
    },
    {
        "id": "EVAL-02",
        "category": "Semantic Paraphrase",
        "patient_id": "CLQ-HOSP-0001",
        "query": "Prior cardiac revascularization procedure and coronary vessel catheterization",
        "expected_terms": ["angioplasty", "heart disease"],
        "expect_hit": True
    },
    {
        "id": "EVAL-03",
        "category": "Condition & Procedure",
        "patient_id": "CLQ-HOSP-0002",
        "query": "Diabetes management with daily insulin therapy",
        "expected_terms": ["diabetes", "insulin therapy"],
        "expect_hit": True
    },
    {
        "id": "EVAL-04",
        "category": "Semantic Paraphrase",
        "patient_id": "CLQ-HOSP-0002",
        "query": "Glycemic control and subcutaneous hormone replacement regimen",
        "expected_terms": ["insulin", "diabetes"],
        "expect_hit": True
    },
    {
        "id": "EVAL-05",
        "category": "Orthopedic Procedure",
        "patient_id": "CLQ-HOSP-0003",
        "query": "Upper limb bone fracture requiring radiographic diagnostic X-ray and immobilization splint",
        "expected_terms": ["fractured arm", "x-ray and splint"],
        "expect_hit": True
    },
    {
        "id": "EVAL-06",
        "category": "Neurological / Inpatient Stay",
        "patient_id": "CLQ-HOSP-0004",
        "query": "Acute cerebrovascular accident with CT brain scan and prolonged hospital admission",
        "expected_terms": ["stroke", "ct scan"],
        "expect_hit": True
    },
    {
        "id": "EVAL-07",
        "category": "Readmission Fact",
        "patient_id": "CLQ-HOSP-0004",
        "query": "Was this stroke patient readmitted to the hospital within 30 days of discharge?",
        "expected_terms": ["readmission: yes", "stroke"],
        "expect_hit": True
    },
    {
        "id": "EVAL-08",
        "category": "Oncology Regimen",
        "patient_id": "CLQ-HOSP-0005",
        "query": "Malignant neoplasm requiring surgical resection and adjuvant systemic chemotherapy regimen",
        "expected_terms": ["cancer", "surgery and chemotherapy"],
        "expect_hit": True
    },
    {
        "id": "EVAL-09",
        "category": "Cardiovascular Counseling",
        "patient_id": "CLQ-HOSP-0006",
        "query": "Essential arterial hypertension treated with pharmacological medication and lifestyle counseling",
        "expected_terms": ["hypertension", "medication and counseling"],
        "expect_hit": True
    },
    {
        "id": "EVAL-10",
        "category": "Emergency Surgery",
        "patient_id": "CLQ-HOSP-0007",
        "query": "Acute lower right quadrant inflammation requiring surgical appendectomy",
        "expected_terms": ["appendicitis", "appendectomy"],
        "expect_hit": True
    },
    {
        "id": "EVAL-11",
        "category": "Orthopedic Rehabilitation",
        "patient_id": "CLQ-HOSP-0008",
        "query": "Lower extremity long bone fracture treated with cast immobilization and physical therapy",
        "expected_terms": ["fractured leg", "cast and physical therapy"],
        "expect_hit": True
    },
    {
        "id": "EVAL-12",
        "category": "Acute Myocardial Infarction",
        "patient_id": "CLQ-HOSP-0009",
        "query": "Acute myocardial infarction evaluated via invasive cardiac catheterization",
        "expected_terms": ["heart attack", "cardiac catheterization"],
        "expect_hit": True
    },
    {
        "id": "EVAL-13",
        "category": "Emergency Allergy",
        "patient_id": "CLQ-HOSP-0010",
        "query": "Acute systemic anaphylactoid allergic episode managed with emergency epinephrine injection",
        "expected_terms": ["allergic reaction", "epinephrine injection"],
        "expect_hit": True
    },
    {
        "id": "EVAL-14",
        "category": "Respiratory Infection",
        "patient_id": "CLQ-HOSP-0011",
        "query": "Lower respiratory tract pulmonary infection managed with antibiotics and bed rest",
        "expected_terms": ["respiratory infection", "antibiotics and rest"],
        "expect_hit": True
    },
    {
        "id": "EVAL-15",
        "category": "Urological Oncology",
        "patient_id": "CLQ-HOSP-0012",
        "query": "Prostatic adenocarcinoma undergoing localized radiation oncology treatment",
        "expected_terms": ["prostate cancer", "radiation therapy"],
        "expect_hit": True
    },
    {
        "id": "EVAL-16",
        "category": "Obstetrics & Delivery",
        "patient_id": "CLQ-HOSP-0013",
        "query": "Obstetric labor delivery and routine postpartum inpatient nursery care",
        "expected_terms": ["childbirth", "delivery and postnatal care"],
        "expect_hit": True
    },
    {
        "id": "EVAL-17",
        "category": "Nephrology Procedure",
        "patient_id": "CLQ-HOSP-0014",
        "query": "Renal calculus nephrolithiasis fragmentation via shockwave lithotripsy",
        "expected_terms": ["kidney stones", "lithotripsy"],
        "expect_hit": True
    },
    {
        "id": "EVAL-18",
        "category": "Rheumatology Degenerative",
        "patient_id": "CLQ-HOSP-0015",
        "query": "Chronic degenerative osteoarthritis managed with physical therapy and analgesia",
        "expected_terms": ["osteoarthritis", "physical therapy and pain management"],
        "expect_hit": True
    },
    {
        "id": "EVAL-19",
        "category": "Demographics Query",
        "patient_id": "CLQ-HOSP-0002",
        "query": "Senior 60 year old male demographic clinical chart profile",
        "expected_terms": ["gender male", "clq-hosp-0002"],
        "expect_hit": True
    },
    {
        "id": "EVAL-20",
        "category": "Multi-Field Query",
        "patient_id": "CLQ-HOSP-0001",
        "query": "Female patient admitted for 5 days with coronary heart disease who recovered without readmission",
        "expected_terms": ["5 days", "recovered", "heart disease"],
        "expect_hit": True
    },
    {
        "id": "EVAL-21",
        "category": "Ambiguous Query",
        "patient_id": "CLQ-HOSP-0007",
        "query": "Abdominal complaints and past hospital encounters",
        "expected_terms": ["appendicitis"],
        "expect_hit": True
    },
    {
        "id": "EVAL-22",
        "category": "Nonexistent Medical Fact",
        "patient_id": "CLQ-HOSP-0001",
        "query": "Bilateral lung transplant and immunosuppression rejection therapy",
        "expected_terms": ["lung transplant"],
        "expect_hit": False  # Must NOT find this nonexistent fact in P1's record
    },
    {
        "id": "EVAL-23",
        "category": "No Relevant Evidence",
        "patient_id": "CLQ-HOSP-0003",
        "query": "Pediatric liver transplantation with biliary atresia",
        "expected_terms": ["liver transplantation"],
        "expect_hit": False  # Must NOT find this in P3's fractured arm record
    },
    {
        "id": "EVAL-24",
        "category": "Cross-Patient Fact Query",
        "patient_id": "CLQ-HOSP-0001",
        "query": "Lithotripsy for kidney stones with 4-day stay",  # Actually belongs to P14!
        "expected_terms": ["kidney stones", "lithotripsy"],
        "expect_hit": False  # Must strictly isolate: P1 has Heart Disease, NOT Kidney Stones!
    },
    {
        "id": "EVAL-25",
        "category": "Misleading Clinical Assumption",
        "patient_id": "CLQ-HOSP-0001",
        "query": "Severe anaphylactic penicillin allergy history",
        "expected_terms": ["penicillin allergy"],
        "expect_hit": False  # Must NOT fabricate allergy fact for P1
    }
]


class TestRagRetrievalEvaluation:
    """Phase 4: Quantitative Evaluation Suite for Patient-Centric RAG Retrieval Quality."""

    def test_run_retrieval_benchmark_and_compute_metrics(self):
        """
        Executes the 25-query benchmark against the live retrieval engine.
        Calculates and asserts IR metrics: Precision@k, Recall@k, MRR, Hit Rate@k.
        """
        db = get_db()
        doctor_user = {"id": 1, "role": "doctor"}
        k = 4
        min_sim = 0.15

        hits = 0
        reciprocal_ranks = []
        precision_scores = []
        recall_scores = []
        evaluated_cases = 0

        print("\n" + "=" * 75)
        print("CLINIQ RAG RETRIEVAL-QUALITY BENCHMARK RESULTS (25 TEST QUERIES)")
        print("=" * 75)

        for case in EVALUATION_CASES:
            case_id = case["id"]
            cat = case["category"]
            pid = case["patient_id"]
            query = case["query"]
            expected_terms = case["expected_terms"]
            expect_hit = case["expect_hit"]

            results = rag_retrieval_service.retrieve_patient_evidence(
                patient_id=pid,
                query_text=query,
                current_user=doctor_user,
                top_k=k,
                min_similarity=min_sim,
                db=db
            )

            # Check if any retrieved chunk contains any of the expected terms
            hit_found = False
            first_hit_rank = 0
            relevant_retrieved = 0

            for rank, item in enumerate(results, 1):
                content_lower = item.content.lower()
                # Check for term match
                is_relevant = any(term in content_lower for term in expected_terms)
                if is_relevant:
                    relevant_retrieved += 1
                    if not hit_found:
                        hit_found = True
                        first_hit_rank = rank

            if expect_hit:
                evaluated_cases += 1
                if hit_found:
                    hits += 1
                    reciprocal_ranks.append(1.0 / first_hit_rank)
                    p_at_k = relevant_retrieved / max(1, len(results))
                    r_at_k = relevant_retrieved / 1.0  # At least 1 expected source chunk
                else:
                    reciprocal_ranks.append(0.0)
                    p_at_k = 0.0
                    r_at_k = 0.0

                precision_scores.append(p_at_k)
                recall_scores.append(min(1.0, r_at_k))
                status = f"PASS (Rank {first_hit_rank}, Sim {results[0].similarity if results else 0:.3f})" if hit_found else "FAIL (Missed)"
            else:
                # Negative or Isolation test: expect_hit is False
                # If no chunks contain the false/cross-patient terms, it is a SUCCESS
                if not hit_found:
                    status = "PASS (Correctly Rejected/Isolated)"
                else:
                    status = f"FAIL (Unexpected Leakage or False Positive at Rank {first_hit_rank})"
                assert not hit_found, f"{case_id} failed: Retrieved ungrounded terms for negative case: {expected_terms}"

            print(f"[{case_id}] {cat:<26} | P: {pid} | {status}")

        hit_rate = hits / evaluated_cases if evaluated_cases > 0 else 0
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0
        avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0

        print("-" * 75)
        print(f"EVALUATED CASES (Positive Queries): {evaluated_cases}")
        print(f"NEGATIVE / ISOLATION CASES        : {len(EVALUATION_CASES) - evaluated_cases}")
        print(f"HIT RATE @ {k}                        : {hit_rate * 100:.2f}% ({hits}/{evaluated_cases})")
        print(f"MEAN RECIPROCAL RANK (MRR)        : {mrr:.4f}")
        print(f"MEAN PRECISION @ {k}                  : {avg_precision:.4f}")
        print(f"MEAN RECALL @ {k}                     : {avg_recall:.4f}")
        print("=" * 75)

        # Assert benchmark thresholds:
        # For a high-quality clinical RAG system:
        assert hit_rate >= 0.85, f"Hit Rate {hit_rate:.2f} is below target threshold 0.85"
        assert mrr >= 0.70, f"MRR {mrr:.4f} is below target threshold 0.70"
