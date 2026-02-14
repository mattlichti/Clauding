"""
Streamlit frontend for many-shot jailbreaking experiments.

Run with: uv run streamlit run evals/app.py
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.many_shot.models import get_model
from evals.many_shot.runner import run_single_experiment, compute_stats
from evals.many_shot.prompts import get_test_questions, FAKE_QA_PAIRS
from evals.many_shot import database as db

# Load environment variables
load_dotenv()

# Initialize database
db.init_db()

st.set_page_config(
    page_title="Many-Shot Jailbreaking Eval",
    page_icon="🔓",
    layout="wide"
)

st.title("🔓 Many-Shot Jailbreaking Eval")
st.markdown("""
Evaluate LLM robustness against many-shot jailbreaking attacks.
Based on [Anthropic's research](https://www.anthropic.com/research/many-shot-jailbreaking).
""")

# Sidebar configuration
st.sidebar.header("Configuration")

# Provider selection
provider = st.sidebar.selectbox(
    "Provider",
    ["claude", "openai", "gemini"],
    index=0
)

# Model selection based on provider
model_options = {
    "claude": [
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-3-haiku-20240307",
    ],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-3.5-turbo"],
    "gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
}

model_id = st.sidebar.selectbox(
    "Model",
    model_options.get(provider, []),
    index=0
)

# Shot counts
st.sidebar.subheader("Shot Counts")
shot_options = [0, 4, 8, 16, 32, 64, 128, 256]
selected_shots = st.sidebar.multiselect(
    "Select shot counts to test",
    shot_options,
    default=[0, 4, 16, 32]
)

# Categories
st.sidebar.subheader("Question Categories")
all_categories = ["violence", "illegal", "deception", "regulated", "discrimination"]
selected_categories = st.sidebar.multiselect(
    "Select categories",
    all_categories,
    default=all_categories
)

# Check API key
api_key_env = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}
has_api_key = bool(os.environ.get(api_key_env[provider]))

if not has_api_key:
    st.sidebar.warning(f"⚠️ {api_key_env[provider]} not set in .env")

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧪 Run Experiment", "📊 Results", "📜 History", "📚 About"])

with tab1:
    st.header("Run Experiment")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration Summary")
        st.write(f"**Provider:** {provider}")
        st.write(f"**Model:** {model_id}")
        st.write(f"**Shot counts:** {selected_shots}")
        st.write(f"**Categories:** {selected_categories}")

        questions = get_test_questions(selected_categories)
        total_runs = len(selected_shots) * len(questions)
        st.write(f"**Total API calls:** {total_runs}")

    with col2:
        st.subheader("Test Questions")
        for q in questions:
            st.write(f"- [{q['category']}] {q['question'][:50]}...")

    st.divider()

    # Run button
    if st.button("🚀 Run Experiment", disabled=not has_api_key, type="primary"):
        if not selected_shots:
            st.error("Please select at least one shot count")
        elif not selected_categories:
            st.error("Please select at least one category")
        else:
            # Create experiment in database
            experiment_id = db.create_experiment(
                provider=provider,
                model_id=model_id,
                shot_counts=selected_shots,
                categories=selected_categories
            )
            st.session_state.current_experiment_id = experiment_id

            # Initialize results in session state
            st.session_state.results = []

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                model = get_model(provider, model_id)

                current = 0
                for num_shots in selected_shots:
                    for q in questions:
                        current += 1
                        progress = current / total_runs
                        progress_bar.progress(progress)
                        status_text.text(f"Running: {num_shots} shots | {q['category']} | {q['question'][:30]}...")

                        result = run_single_experiment(model, q["question"], num_shots)
                        result["category"] = q["category"]
                        st.session_state.results.append(result)

                        # Save to database
                        db.save_result(
                            experiment_id=experiment_id,
                            question=q["question"],
                            category=q["category"],
                            num_shots=num_shots,
                            response=result["response"],
                            is_jailbreak=result["judgment"]["is_jailbreak"],
                            is_refusal=result["judgment"]["is_refusal"],
                            response_length=result["judgment"].get("response_length", 0),
                            error=result["error"]
                        )

                progress_bar.progress(1.0)
                status_text.text("✅ Complete!")

                # Update experiment stats
                db.update_experiment_stats(experiment_id)

                # Compute and display stats
                stats = compute_stats(st.session_state.results)
                st.session_state.stats = stats

                st.success(f"Completed {total_runs} experiments! (Experiment #{experiment_id})")

            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab2:
    st.header("Results")

    if "results" not in st.session_state or not st.session_state.results:
        st.info("No results yet. Run an experiment first!")
    else:
        results = st.session_state.results
        stats = st.session_state.stats

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        total_jailbreaks = sum(1 for r in results if r["judgment"]["is_jailbreak"])
        total_refusals = sum(1 for r in results if r["judgment"]["is_refusal"])

        col1.metric("Total Experiments", len(results))
        col2.metric("Jailbreaks", total_jailbreaks)
        col3.metric("Refusals", total_refusals)

        st.divider()

        # Chart: Jailbreak rate by shot count
        st.subheader("Jailbreak Rate by Shot Count")

        chart_data = []
        for shots, data in sorted(stats["by_shots"].items()):
            chart_data.append({
                "Shot Count": shots,
                "Jailbreak Rate (%)": data["rate"] * 100,
                "Jailbreaks": data["jailbreaks"],
                "Total": data["total"]
            })

        df_shots = pd.DataFrame(chart_data)

        fig = px.bar(
            df_shots,
            x="Shot Count",
            y="Jailbreak Rate (%)",
            text="Jailbreak Rate (%)",
            color="Jailbreak Rate (%)",
            color_continuous_scale="Reds"
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Chart: Jailbreak rate by category
        st.subheader("Jailbreak Rate by Category")

        cat_data = []
        for cat, data in stats["by_category"].items():
            cat_data.append({
                "Category": cat,
                "Jailbreak Rate (%)": data["rate"] * 100,
                "Jailbreaks": data["jailbreaks"],
                "Total": data["total"]
            })

        df_cats = pd.DataFrame(cat_data)

        fig2 = px.bar(
            df_cats,
            x="Category",
            y="Jailbreak Rate (%)",
            text="Jailbreak Rate (%)",
            color="Jailbreak Rate (%)",
            color_continuous_scale="Reds"
        )
        fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # Detailed results table
        st.subheader("Detailed Results")

        table_data = []
        for r in results:
            table_data.append({
                "Shots": r["num_shots"],
                "Category": r["category"],
                "Question": r["question"][:40] + "...",
                "Result": "🔓 Jailbreak" if r["judgment"]["is_jailbreak"] else "🔒 Refused",
                "Response Preview": r["judgment"].get("response_preview", "")[:100] + "..."
            })

        df_results = pd.DataFrame(table_data)
        st.dataframe(df_results, use_container_width=True)

        # Export button
        if st.button("📥 Export Results as JSON"):
            results_json = json.dumps(results, indent=2)
            st.download_button(
                label="Download JSON",
                data=results_json,
                file_name="many_shot_results.json",
                mime="application/json"
            )

with tab3:
    st.header("Experiment History")

    experiments = db.get_experiments()

    if not experiments:
        st.info("No experiments yet. Run your first experiment!")
    else:
        # Experiments table
        exp_data = []
        for exp in experiments:
            exp_data.append({
                "ID": exp["id"],
                "Date": exp["created_at"][:16] if exp["created_at"] else "",
                "Provider": exp["provider"],
                "Model": exp["model_id"],
                "Shots": str(exp["shot_counts"]),
                "Runs": exp["total_runs"] or 0,
                "Jailbreaks": exp["total_jailbreaks"] or 0,
                "Rate": f"{(exp['total_jailbreaks'] or 0) / (exp['total_runs'] or 1) * 100:.1f}%"
            })

        df_exp = pd.DataFrame(exp_data)
        st.dataframe(df_exp, use_container_width=True)

        st.divider()

        # Load specific experiment
        st.subheader("Load Experiment")
        exp_ids = [exp["id"] for exp in experiments]
        selected_exp_id = st.selectbox("Select experiment to load", exp_ids)

        if st.button("📂 Load Experiment"):
            exp_results = db.get_experiment_results(selected_exp_id)
            stats_by_shots = db.get_stats_by_shots(selected_exp_id)
            stats_by_category = db.get_stats_by_category(selected_exp_id)

            # Convert to format expected by Results tab
            st.session_state.results = [
                {
                    "num_shots": r["num_shots"],
                    "category": r["category"],
                    "question": r["question"],
                    "response": r["response"],
                    "judgment": {
                        "is_jailbreak": bool(r["is_jailbreak"]),
                        "is_refusal": bool(r["is_refusal"]),
                        "response_length": r["response_length"],
                        "response_preview": (r["response"] or "")[:200]
                    },
                    "error": r["error"]
                }
                for r in exp_results
            ]
            st.session_state.stats = {
                "by_shots": stats_by_shots,
                "by_category": stats_by_category
            }
            st.session_state.current_experiment_id = selected_exp_id
            st.success(f"Loaded experiment #{selected_exp_id}. Go to Results tab to view.")

        st.divider()

        # Compare experiments
        st.subheader("Compare Experiments")
        compare_ids = st.multiselect("Select experiments to compare", exp_ids)

        if len(compare_ids) >= 2 and st.button("📊 Compare"):
            comparison_data = db.get_comparison_data(compare_ids)

            # Build dataframe for comparison chart
            comp_df = pd.DataFrame(comparison_data)
            comp_df["Model"] = comp_df["provider"] + ":" + comp_df["model_id"]
            comp_df["Jailbreak Rate (%)"] = comp_df["rate"] * 100

            fig = px.line(
                comp_df,
                x="num_shots",
                y="Jailbreak Rate (%)",
                color="Model",
                markers=True,
                title="Jailbreak Rate by Shot Count (Model Comparison)"
            )
            fig.update_layout(xaxis_title="Shot Count", yaxis_title="Jailbreak Rate (%)")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Delete experiment
        st.subheader("Delete Experiment")
        delete_id = st.selectbox("Select experiment to delete", exp_ids, key="delete_select")
        if st.button("🗑️ Delete", type="secondary"):
            db.delete_experiment(delete_id)
            st.success(f"Deleted experiment #{delete_id}")
            st.rerun()

with tab4:
    st.header("About Many-Shot Jailbreaking")

    st.markdown("""
    ### What is Many-Shot Jailbreaking?

    Many-shot jailbreaking (MSJ) is a technique discovered by Anthropic researchers that can
    bypass AI safety training by including many examples of the AI "complying" with harmful
    requests in the prompt.

    ### How it works

    1. Create a fake dialogue with many Q&A pairs showing the AI answering harmful questions
    2. Append the actual harmful question at the end
    3. The model follows the pattern from the examples

    ### Key findings from the paper

    - Effectiveness follows a **power law** - more shots = higher success rate
    - Doesn't work at ~5 shots, works consistently at ~256 shots
    - Works across multiple models (Claude, GPT-4, Llama 2, Mistral)
    - Robust to format and style changes

    ### This tool

    This evaluation harness lets you:
    - Test different models against MSJ attacks
    - Vary the number of shots
    - Test different harm categories
    - Visualize results
    - Compare across models

    ### References

    - [Anthropic Research Blog](https://www.anthropic.com/research/many-shot-jailbreaking)
    - [NeurIPS 2024 Paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/ea456e232efb72d261715e33ce25f208-Paper-Conference.pdf)
    """)

    st.divider()

    st.subheader("Example Fake Q&A Pairs")
    st.markdown("These are examples of the fake dialogue pairs used in the attack:")

    for i, pair in enumerate(FAKE_QA_PAIRS[:3]):
        with st.expander(f"Example {i+1}: {pair['question'][:40]}..."):
            st.write(f"**Human:** {pair['question']}")
            st.write(f"**Assistant:** {pair['answer']}")
