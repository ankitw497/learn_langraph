"""
QBR Orchestration - Streamlit Interface
Sequential execution of Engagement → Information Gatherer → Synthesis agents
"""

import streamlit as st
import uuid
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import logging
import traceback

# Import your agents
from engagement.agent import QBREngagementAgentSync
from setup_info_gatherer import run_information_gatherer
from synthesis_agent.main import run_synthesis_agent

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="QBR Orchestrator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .session-info {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .agent-status {
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
        border-left: 4px solid;
    }
    .agent-pending { border-left-color: #ffc107; background-color: #fff3cd; }
    .agent-running { border-left-color: #007bff; background-color: #cce5ff; }
    .agent-complete { border-left-color: #28a745; background-color: #d4edda; }
    .agent-error { border-left-color: #dc3545; background-color: #f8d7da; }
    .download-section {
        background-color: #e8f5e8;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #c3e6c3;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logger.info(f"New session created: {st.session_state.session_id}")
    
    if 'agent' not in st.session_state:
        st.session_state.agent = QBREngagementAgentSync()
        logger.info("Engagement agent initialized")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 Hello! I'm your QBR assistant. I can help you create a new QBR or refresh an existing report. What would you like to do today?"
        })
    
    # Agent status tracking
    if 'engagement_status' not in st.session_state:
        st.session_state.engagement_status = "pending"  # pending, running, complete, error
    
    if 'info_gatherer_status' not in st.session_state:
        st.session_state.info_gatherer_status = "pending"
    
    if 'synthesis_status' not in st.session_state:
        st.session_state.synthesis_status = "pending"
    
    # Completion flags
    if 'engagement_complete' not in st.session_state:
        st.session_state.engagement_complete = False
    
    if 'info_gatherer_complete' not in st.session_state:
        st.session_state.info_gatherer_complete = False
    
    if 'synthesis_complete' not in st.session_state:
        st.session_state.synthesis_complete = False
    
    # Error tracking
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None
    
    # Final outputs
    if 'final_spec' not in st.session_state:
        st.session_state.final_spec = None
    
    if 'presentation_path' not in st.session_state:
        st.session_state.presentation_path = None
    
    # Session folder setup
    if 'session_folder' not in st.session_state:
        setup_session_folder()


def setup_session_folder():
    """Setup session-specific folder structure"""
    session_id = st.session_state.session_id
    session_folder = Path(f"./sessions/{session_id}")
    
    # Create session folder and subfolders
    folders_to_create = [
        session_folder,
        session_folder / "engagement_output",
        session_folder / "infoagent_output", 
        session_folder / "synthesis_output"
    ]
    
    for folder in folders_to_create:
        folder.mkdir(parents=True, exist_ok=True)
    
    st.session_state.session_folder = str(session_folder)
    logger.info(f"Session folder created: {session_folder}")


def find_manifest_json(infoagent_output_path):
    """
    Find manifest.json in infoagent_output folder.
    First check root level, then check subfolders.
    """
    infoagent_path = Path(infoagent_output_path)
    
    # Check root level first
    manifest_root = infoagent_path / "manifest.json"
    if manifest_root.exists():
        logger.info(f"Found manifest.json at root level: {manifest_root}")
        return str(manifest_root)
    
    # Check subfolders
    for item in infoagent_path.iterdir():
        if item.is_dir():
            manifest_subfolder = item / "manifest.json"
            if manifest_subfolder.exists():
                logger.info(f"Found manifest.json in subfolder: {manifest_subfolder}")
                return str(manifest_subfolder)
    
    # Not found
    logger.warning(f"manifest.json not found in {infoagent_path} or its subfolders")
    return None


def render_sidebar():
    """Render sidebar with session info and agent status"""
    with st.sidebar:
        st.header("🚀 QBR Orchestrator")
        
        # Session Information
        st.markdown(f"""
        <div class="session-info">
            <h4>📋 Session Info</h4>
            <p><strong>Session ID:</strong><br><code>{st.session_state.session_id}</code></p>
            <p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Folder:</strong><br><code>{st.session_state.session_folder}</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Agent Status Pipeline
        st.subheader("🔄 Agent Pipeline")
        
        # Engagement Agent Status
        engagement_class = f"agent-{st.session_state.engagement_status}"
        engagement_icon = {
            "pending": "⏳",
            "running": "🔄", 
            "complete": "✅",
            "error": "❌"
        }.get(st.session_state.engagement_status, "⏳")
        
        st.markdown(f"""
        <div class="agent-status {engagement_class}">
            {engagement_icon} <strong>1. Engagement Agent</strong><br>
            <small>Status: {st.session_state.engagement_status.title()}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Information Gatherer Status
        info_class = f"agent-{st.session_state.info_gatherer_status}"
        info_icon = {
            "pending": "⏳",
            "running": "🔄",
            "complete": "✅", 
            "error": "❌"
        }.get(st.session_state.info_gatherer_status, "⏳")
        
        st.markdown(f"""
        <div class="agent-status {info_class}">
            {info_icon} <strong>2. Information Gatherer</strong><br>
            <small>Status: {st.session_state.info_gatherer_status.title()}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Synthesis Agent Status
        synthesis_class = f"agent-{st.session_state.synthesis_status}"
        synthesis_icon = {
            "pending": "⏳",
            "running": "🔄",
            "complete": "✅",
            "error": "❌"
        }.get(st.session_state.synthesis_status, "⏳")
        
        st.markdown(f"""
        <div class="agent-status {synthesis_class}">
            {synthesis_icon} <strong>3. Synthesis Agent</strong><br>
            <small>Status: {st.session_state.synthesis_status.title()}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress metrics (removed frustration index)
        st.divider()
        st.subheader("📊 Progress")
        
        try:
            completion_pct = st.session_state.agent.get_completion_percentage(st.session_state.session_id)
            st.metric("Completion", f"{completion_pct:.0f}%")
        except:
            st.write("Metrics unavailable")
        
        # Error display
        if st.session_state.last_error:
            st.divider()
            st.subheader("❌ Last Error")
            st.error(st.session_state.last_error)
        
        # Reset button
        st.divider()
        if st.button("🔄 New Session", type="secondary", use_container_width=True):
            reset_session()


def reset_session():
    """Reset session and start fresh"""
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize
    initialize_session_state()
    st.rerun()


def run_info_gatherer():
    """Run the Information Gatherer agent"""
    try:
        st.session_state.info_gatherer_status = "running"
        
        # Setup config for this session
        session_folder = Path(st.session_state.session_folder)
        
        config = {
            "INPUT_JSONS_PATH": str(session_folder / "engagement_output"),
            "SPECIFIC_JSON": None,
            "OUTPUT_DIR": str(session_folder / "infoagent_output"),
            "SAVE_RESULTS": True,
            "VERBOSE": True,
            "MAX_FILES_TO_PROCESS": None,
            "DB_HOST": os.getenv("DB_HOST", "localhost"),
            "DB_PORT": os.getenv("DB_PORT", "5432"),
            "DB_NAME": os.getenv("DB_NAME", "postgres"),
            "DB_USER": os.getenv("DB_USER", "postgres"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
            "GEMINI_PROJECT": os.getenv("VERTEX_PROJECT"),
            "GEMINI_LOCATION": os.getenv("VERTEX_LOCATION", "us-central1"),
            "GEMINI_MODEL": os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
        }
        
        logger.info(f"Running Information Gatherer with config: {config}")
        
        # Run the information gatherer
        result = run_information_gatherer(data_config=config)
        
        if result:
            st.session_state.info_gatherer_status = "complete"
            st.session_state.info_gatherer_complete = True
            logger.info("Information Gatherer completed successfully")
            return True
        else:
            st.session_state.info_gatherer_status = "error"
            st.session_state.last_error = "Information Gatherer failed to complete"
            logger.error("Information Gatherer failed")
            return False
            
    except Exception as e:
        st.session_state.info_gatherer_status = "error"
        st.session_state.last_error = f"Information Gatherer error: {str(e)}"
        logger.error(f"Information Gatherer error: {e}", exc_info=True)
        return False


def run_synthesis():
    """Run the Synthesis agent"""
    try:
        st.session_state.synthesis_status = "running"
        
        # Setup config for this session
        session_folder = Path(st.session_state.session_folder)
        infoagent_output_path = session_folder / "infoagent_output"
        
        # 🎯 Find manifest.json using the new logic
        manifest_path = find_manifest_json(infoagent_output_path)
        
        if not manifest_path:
            st.session_state.synthesis_status = "error"
            st.session_state.last_error = "manifest.json not found in infoagent_output or its subfolders"
            logger.error("manifest.json not found for synthesis")
            return False
        
        config = {
            'manifest': manifest_path,  # Use the found manifest path
            'engagement': str(session_folder / "engagement_output" / "qbr_spec.json"),
            'output_dir': str(session_folder / "synthesis_output"),
            'template_dir': './templates',
            'config': './synthesis_agent/config.yaml',
            'client': 'Client',
            'verbose': False,
            'strict': False,
            'dry_run': False,
            'log_level': 'info',
            'runtime': {'random_seed': 42},
            'logic': {'normalize_engagement': True},
            'brand': {'preferred_template': 'default', 'objectives': []},
            'features': {'enable_pdf_export': False}
        }
        
        logger.info(f"Running Synthesis Agent with config: {config}")
        logger.info(f"Using manifest path: {manifest_path}")
        
        # Run the synthesis agent
        result = run_synthesis_agent(config)
        
        if result:
            st.session_state.synthesis_status = "complete"
            st.session_state.synthesis_complete = True
            
            # Look for the generated PowerPoint file
            output_dir = session_folder / "synthesis_output"
            pptx_files = list(output_dir.glob("*.pptx"))
            
            if pptx_files:
                st.session_state.presentation_path = str(pptx_files[0])
                logger.info(f"Presentation created: {st.session_state.presentation_path}")
            
            logger.info("Synthesis Agent completed successfully")
            return True
        else:
            st.session_state.synthesis_status = "error"
            st.session_state.last_error = "Synthesis Agent failed to complete"
            logger.error("Synthesis Agent failed")
            return False
            
    except Exception as e:
        st.session_state.synthesis_status = "error"
        st.session_state.last_error = f"Synthesis Agent error: {str(e)}"
        logger.error(f"Synthesis Agent error: {e}", exc_info=True)
        return False


def auto_progress_workflow():
    """Automatically progress through the workflow when agents complete"""
    # Check if engagement is complete and trigger info gatherer
    if (st.session_state.engagement_complete and 
        st.session_state.info_gatherer_status == "pending"):
        
        with st.spinner("🔄 Running Information Gatherer..."):
            success = run_info_gatherer()
            if not success:
                st.error("❌ Information Gatherer failed. Workflow stopped.")
                return
        st.rerun()
    
    # Check if info gatherer is complete and trigger synthesis
    if (st.session_state.info_gatherer_complete and 
        st.session_state.synthesis_status == "pending"):
        
        with st.spinner("🔄 Running Synthesis Agent..."):
            success = run_synthesis()
            if not success:
                st.error("❌ Synthesis Agent failed. Workflow stopped.")
                return
        st.rerun()


def save_engagement_spec(spec):
    """Save engagement specification to session folder"""
    try:
        session_folder = Path(st.session_state.session_folder)
        spec_path = session_folder / "engagement_output" / "qbr_spec.json"
        
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2)
        
        logger.info(f"Engagement spec saved to: {spec_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving engagement spec: {e}")
        return False


def render_download_section():
    """Render download section when presentation is ready"""
    if st.session_state.presentation_path and os.path.exists(st.session_state.presentation_path):
        st.markdown("""
        <div class="download-section">
            <h3>🎉 QBR Presentation Ready!</h3>
            <p>Your PowerPoint presentation has been generated successfully.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Read the file for download
            with open(st.session_state.presentation_path, 'rb') as f:
                file_data = f.read()
            
            filename = f"QBR_{st.session_state.session_id[:8]}.pptx"
            
            st.download_button(
                label="📊 Download PowerPoint Presentation",
                data=file_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
                use_container_width=True
            )
        
        # Show session summary
        with st.expander("📋 Session Summary", expanded=False):
            st.write(f"**Session ID:** {st.session_state.session_id}")
            st.write(f"**Session Folder:** {st.session_state.session_folder}")
            
            if st.session_state.final_spec:
                st.write("**QBR Specification:**")
                st.json(st.session_state.final_spec)


def main():
    """Main application flow"""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title("🚀 QBR Orchestrator")
    st.caption("Sequential AI Agent Pipeline: Engagement → Information Gatherer → Synthesis")
    
    # Auto-progress workflow
    auto_progress_workflow()
    
    # Show download section if complete
    if st.session_state.synthesis_complete:
        render_download_section()
        st.divider()
    
    # Display chat history
    st.subheader("💬 Conversation")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input (only if engagement not complete)
    if not st.session_state.engagement_complete:
        if prompt := st.chat_input("Type your message...", key="chat_input"):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Update engagement status
            st.session_state.engagement_status = "running"
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Processing..."):
                    try:
                        # Process message
                        response = st.session_state.agent.process_message(
                            st.session_state.session_id,
                            prompt
                        )
                        
                        # Handle both string and dict responses
                        if isinstance(response, dict):
                            reply_text = response["reply"]
                            st.markdown(reply_text)
                            
                            # Add to message history
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": reply_text
                            })
                            
                            # Check for completion
                            if response.get("spec_complete"):
                                st.session_state.engagement_status = "complete"
                                st.session_state.engagement_complete = True
                                
                                # Save the final spec
                                final_spec = response.get("final_spec") or st.session_state.agent.get_final_spec(st.session_state.session_id)
                                st.session_state.final_spec = final_spec
                                
                                if final_spec:
                                    save_engagement_spec(final_spec)
                                    st.success("✅ Engagement complete! Starting Information Gatherer...")
                                
                                st.rerun()
                        else:
                            # String response
                            st.markdown(response)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": response
                            })
                        
                        # Update status
                        st.session_state.engagement_status = "pending"
                        
                    except Exception as e:
                        st.session_state.engagement_status = "error"
                        st.session_state.last_error = f"Engagement error: {str(e)}"
                        
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        error_msg = "I apologize, but I encountered an issue. Could you please try again? 🔄"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
            
            # Check if complete after processing (backup check)
            if not st.session_state.engagement_complete and st.session_state.agent.is_complete(st.session_state.session_id):
                st.session_state.engagement_status = "complete"
                st.session_state.engagement_complete = True
                
                # Save final spec
                final_spec = st.session_state.agent.get_final_spec(st.session_state.session_id)
                st.session_state.final_spec = final_spec
                
                if final_spec:
                    save_engagement_spec(final_spec)
                
                st.rerun()
    
    else:
        # Engagement complete - show status
        if st.session_state.synthesis_complete:
            st.success("🎉 All agents completed successfully! Your QBR presentation is ready.")
        elif st.session_state.info_gatherer_complete:
            st.info("📝 Information gathering complete. Synthesis agent running...")
        elif st.session_state.engagement_complete:
            st.info("💬 Engagement complete. Information gatherer running...")


if __name__ == "__main__":
    main()
