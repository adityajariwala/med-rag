import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Med-RAG: Evidence-Based Q&A",
    page_icon="🏥",
    layout="wide"
)

# Title and description
st.title("🏥 Med-RAG: Evidence-Based Medical Q&A")
st.markdown("""
Ask clinical or research questions and get answers grounded in PubMed literature.
All responses are backed by retrieved scientific evidence.
""")

# Sidebar with info
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Med-RAG** uses:
    - 🔍 PubMed literature retrieval
    - 🧬 Biomedical embeddings (PubMedBERT)
    - 🤖 LLM-based synthesis
    - 📊 Faithfulness evaluation
    """)

    st.header("Settings")
    api_url = st.text_input("API URL", value=API_URL)

    # Check API health
    try:
        health_response = requests.get(f"{api_url}/health", timeout=2)
        if health_response.status_code == 200:
            health_data = health_response.json()
            if health_data.get("index_ready"):
                st.success("✅ API is healthy and index is ready")
            else:
                st.warning("⚠️ API is running but index is not ready")
        else:
            st.error("❌ API is not responding correctly")
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API. Is it running?")
        st.code("uvicorn src.api:app --reload", language="bash")

# Main content
st.divider()

# Example questions
st.subheader("Example Questions")
example_cols = st.columns(3)

with example_cols[0]:
    if st.button("GLP-1 & Cardiovascular Outcomes"):
        st.session_state.question = "What evidence exists linking GLP-1 agonists to cardiovascular outcomes?"

with example_cols[1]:
    if st.button("Metformin Side Effects"):
        st.session_state.question = "What are the most common side effects of metformin?"

with example_cols[2]:
    if st.button("Aspirin for CVD Prevention"):
        st.session_state.question = "What is the evidence for aspirin in primary prevention of cardiovascular disease?"

st.divider()

# Question input
question = st.text_area(
    "Ask a medical question:",
    value=st.session_state.get("question", ""),
    height=100,
    placeholder="e.g., What are the benefits and risks of statins for primary prevention?"
)

# Advanced options
with st.expander("Advanced Options"):
    ground_truth_pmids = st.text_input(
        "Ground Truth PMIDs (optional, comma-separated)",
        help="Provide known relevant PMIDs to calculate retrieval recall"
    )

# Submit button
col1, col2 = st.columns([1, 5])
with col1:
    submit = st.button("🔍 Submit", type="primary", use_container_width=True)

if submit and question:
    with st.spinner("Searching PubMed and generating answer..."):
        try:
            # Prepare request
            payload = {"question": question}
            if ground_truth_pmids:
                payload["ground_truth_pmids"] = [
                    pmid.strip() for pmid in ground_truth_pmids.split(",")
                ]

            # Make API request
            response = requests.post(
                f"{api_url}/query",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                answer = data["answer"]
                metrics = data["metrics"]

                # Display answer
                st.success("✅ Answer generated successfully!")

                # Metrics in columns
                metric_cols = st.columns(3)
                with metric_cols[0]:
                    confidence_pct = int(answer["confidence"] * 100)
                    st.metric(
                        "Confidence",
                        f"{confidence_pct}%",
                        delta=None,
                        help="Model's confidence in the answer"
                    )

                with metric_cols[1]:
                    if metrics["retrieval_recall"] >= 0:
                        recall_pct = int(metrics["retrieval_recall"] * 100)
                        st.metric(
                            "Retrieval Recall",
                            f"{recall_pct}%",
                            delta=None,
                            help="Percentage of ground truth PMIDs retrieved"
                        )
                    else:
                        st.metric("Retrieval Recall", "N/A", help="No ground truth provided")

                with metric_cols[2]:
                    faithful_icon = "✅" if metrics["faithful"] else "❌"
                    st.metric(
                        "Faithfulness",
                        faithful_icon,
                        delta=None,
                        help="Whether answer is grounded in retrieved evidence"
                    )

                st.divider()

                # Answer summary
                st.subheader("📝 Answer Summary")
                st.write(answer["answer_summary"])

                # Evidence
                st.subheader("📚 Supporting Evidence")
                if answer["evidence"]:
                    for i, ev in enumerate(answer["evidence"], 1):
                        with st.expander(f"Evidence {i} - PMID: {ev['pmid']}", expanded=(i == 1)):
                            st.markdown(f"**PMID:** [{ev['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{ev['pmid']}/)")
                            st.markdown(f"**Excerpt:** {ev['excerpt']}")
                else:
                    st.info("No specific evidence excerpts were extracted.")

                # Raw JSON (for debugging)
                with st.expander("🔧 Raw Response (Debug)"):
                    st.json(data)

            elif response.status_code == 503:
                st.error("⚠️ The API index is not ready yet. Please wait a moment and try again.")
            else:
                st.error(f"❌ Error: {response.status_code}")
                st.code(response.text)

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. The query may be too complex or the API is slow.")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to API: {e}")
            st.info("Make sure the API is running: `uvicorn src.api:app --reload`")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

elif submit and not question:
    st.warning("⚠️ Please enter a question first!")

# Footer
st.divider()
st.caption("""
**Disclaimer:** This is a research prototype. Do not use for clinical decision-making.
Always consult healthcare professionals for medical advice.
""")
