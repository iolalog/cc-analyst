from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from claude_processor import ClaudeQueryProcessor
from data_manager import (  # ECBDataServer for backward compatibility
    DataManager,
    ECBDataServer,
)

load_dotenv()

st.set_page_config(page_title="ECB Analytics Assistant", page_icon="📊", layout="wide")

st.title("📊 ECB Analytics Assistant")
st.markdown("Natural language analytics for European Central Bank data")

# Initialize processors
@st.cache_resource
def get_processors() -> tuple[ClaudeQueryProcessor, ECBDataServer, DataManager]:
    claude_processor = ClaudeQueryProcessor()
    ecb_server = ECBDataServer()  # For backward compatibility
    data_manager = DataManager()  # New generic data manager
    return claude_processor, ecb_server, data_manager


try:
    claude_processor, ecb_server, data_manager = get_processors()
    processors_available = True
except Exception as e:
    st.error(f"⚠️ API Configuration needed: {str(e)}")
    st.info("Please set your ANTHROPIC_API_KEY in a .env file")
    processors_available = False
    claude_processor = ecb_server = data_manager = None

# Sidebar for data source selection
st.sidebar.header("Data Configuration")

if processors_available and data_manager:
    available_sources = data_manager.get_available_sources()
    st.sidebar.markdown("**Available Data Sources:**")
    for source_id, source_name in available_sources.items():
        st.sidebar.markdown(f"- **{source_id.upper()}**: {source_name}")
else:
    st.sidebar.markdown("**Data Source:** ECB Statistical Data Warehouse")
    st.sidebar.markdown("**API:** https://data-api.ecb.europa.eu")

# Main interface
st.header("Ask Questions About ECB Data")

if processors_available:
    # Sample queries for users
    st.markdown("### Sample Questions:")
    sample_queries: list[str] = [
        "Show me ECB interest rate developments over the last 2 years",
        "What are the current deposit facility rates?",
        "Compare all three key ECB rates over time",
        "Display main refinancing rate trends since 2020",
    ]

    col1, col2 = st.columns(2)
    for i, query in enumerate(sample_queries):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(query, key=query, use_container_width=True):
                st.session_state.user_query = query

    # User input
    user_query = st.text_area(
        "Enter your question about ECB data:",
        value=st.session_state.get("user_query", ""),
        height=100,
        placeholder="Example: Show me the ECB interest rate trends for the past year",
    )
else:
    st.warning("Please configure API access to continue.")
    user_query = None

if processors_available and st.button("Analyze", type="primary"):
    if user_query:
        with st.spinner("Processing your question..."):
            # Step 1: Parse the natural language query
            parsed_result = claude_processor.parse_user_query(user_query)

            if not parsed_result["success"]:
                st.error(
                    f"Failed to parse query: {parsed_result.get('error', 'Unknown error')}"
                )
                st.stop()

            parsed_query = parsed_result["parsed_query"]

            # Step 2: Fetch data based on parsed query
            data_source = parsed_query.get("data_source", "ecb")
            dataset_type = parsed_query.get("dataset_type", "interest_rates")

            with st.spinner(f"Fetching data from {data_source.upper()}..."):
                # Prepare parameters
                parameters = {}
                if dataset_type == "interest_rates":
                    parameters["rate_types"] = parsed_query.get(
                        "specific_rates", ["MRR", "DFR", "MLF"]
                    )
                    parameters["start_date"] = parsed_query.get("start_date")
                    parameters["end_date"] = parsed_query.get("end_date")

                    # Set default date range if not specified
                    if not parameters["start_date"]:
                        if parsed_query.get("time_period") == "2Y":
                            parameters["start_date"] = (
                                datetime.now() - timedelta(days=730)
                            ).strftime("%Y-%m-%d")
                        else:
                            parameters["start_date"] = (
                                datetime.now() - timedelta(days=365)
                            ).strftime("%Y-%m-%d")

                # Query data using the generic data manager
                data_result = data_manager.query_data(
                    data_source, dataset_type, parameters
                )

                if not data_result["success"]:
                    st.error(
                        f"Failed to fetch data: {data_result.get('error', 'Unknown error')}"
                    )
                    if "validation_errors" in data_result:
                        st.error("Validation errors:")
                        for error in data_result["validation_errors"]:
                            st.error(f"- {error}")
                    if "suggestions" in data_result:
                        st.info("Suggestions:")
                        for suggestion in data_result["suggestions"]:
                            st.info(f"- {suggestion}")
                    st.stop()

            # Step 3: Analyze results with Claude
            with st.spinner("Analyzing data..."):
                analysis_result = claude_processor.analyze_data_results(
                    data_result["data"], user_query
                )

                if not analysis_result["success"]:
                    st.warning(
                        f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"
                    )
                    analysis_text = (
                        "Data retrieved successfully, but analysis is unavailable."
                    )
                else:
                    analysis_text = analysis_result["analysis"]

            # Step 4: Display results
            st.subheader("📊 Analysis Results")
            st.markdown(f"**Your question:** {user_query}")

            # Show analysis
            with st.expander("🤖 AI Analysis", expanded=True):
                st.markdown(analysis_text)

            # Show data visualization
            st.subheader("📈 Data Visualization")

            # Convert data to DataFrame for visualization
            viz_data: list[dict[str, Any]] = []
            data = data_result["data"]

            for rate_type, rate_data in data.items():
                if "observations" in rate_data:
                    for obs in rate_data["observations"]:
                        if obs["value"] is not None:
                            viz_data.append(
                                {
                                    "Date": pd.to_datetime(obs["date"]),
                                    "Rate_Type": rate_type,
                                    "Value": obs["value"],
                                }
                            )

            if viz_data:
                df = pd.DataFrame(viz_data)

                # Create interactive plot
                chart_title = f"{data_source.upper()} {dataset_type.replace('_', ' ').title()} Over Time"
                fig = px.line(
                    df,
                    x="Date",
                    y="Value",
                    color="Rate_Type",
                    title=chart_title,
                    labels={"Value": "Rate (%)", "Rate_Type": "Rate Type"},
                )

                fig.update_layout(height=500, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

                # Show current values
                st.subheader("📋 Current Rates")
                cols = st.columns(len(data))

                for i, (rate_type, rate_data) in enumerate(data.items()):
                    if "observations" in rate_data and rate_data["observations"]:
                        latest_obs = rate_data["observations"][-1]
                        if latest_obs["value"] is not None:
                            cols[i].metric(
                                f"{rate_type} Rate",
                                f"{latest_obs['value']:.2f}%",
                                delta=None,
                            )

                # Show data table
                with st.expander("📄 Raw Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.warning("No data available for visualization.")

    elif processors_available:
        st.warning("Please enter a question about ECB data.")

# Footer
st.markdown("---")
if processors_available:
    sources_text = ", ".join(
        [f"{sid.upper()}" for sid in data_manager.get_available_sources().keys()]
    )
    st.success(f"✅ Connected to {sources_text} & Claude API")
else:
    st.error("❌ API configuration required")

st.markdown("**Powered by:** Multi-source Data Analytics + Claude AI")
