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
    page_title="AI Powered QBR",
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
    .progress-section {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .tip-section {
        background-color: #e3f2fd;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def setup_session_logging(session_folder):
    """Setup session-specific logging"""
    log_file = Path(session_folder) / "session.log"
    
    # Create session-specific logger
    session_logger = logging.getLogger(f"session_{st.session_state.session_id}")
    session_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    session_logger.handlers.clear()
    
    # Add file handler for session logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    session_logger.addHandler(file_handler)
    
    # Store logger in session state
    st.session_state.session_logger = session_logger
    
    # Log session start
    session_logger.info(f"Session started - ID: {st.session_state.session_id}")
    
    return session_logger


def save_conversation_json():
    """Save conversation history to JSON file"""
    try:
        session_folder = Path(st.session_state.session_folder)
        conversation_file = session_folder / "conversation.json"
        
        conversation_data = {
            "session_id": st.session_state.session_id,
            "created_at": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "engagement_complete": st.session_state.engagement_complete,
            "info_gatherer_complete": st.session_state.info_gatherer_complete,
            "synthesis_complete": st.session_state.synthesis_complete,
            "final_spec": st.session_state.final_spec,
            "workflow_progress": st.session_state.workflow_progress,
            "current_agent": st.session_state.current_agent
        }
        
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        if hasattr(st.session_state, 'session_logger'):
            st.session_state.session_logger.info(f"Conversation saved to {conversation_file}")
        
    except Exception as e:
        if hasattr(st.session_state, 'session_logger'):
            st.session_state.session_logger.error(f"Error saving conversation: {e}")


def initialize_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'agent' not in st.session_state:
        st.session_state.agent = QBREngagementAgentSync()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 Hello! I'm your QBR assistant. I can help you create a new QBR or refresh an existing report. What would you like to do today?"
        })
    
    # Agent status tracking
    if 'engagement_status' not in st.session_state:
        st.session_state.engagement_status = "pending"
    
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
    
    # Workflow progress tracking
    if 'workflow_progress' not in st.session_state:
        st.session_state.workflow_progress = 0  # 0, 33, 66, 100
    
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = "Ready to Start"
    
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
    
    # Setup session logging
    setup_session_logging(session_folder)
    
    st.session_state.session_logger.info(f"Session folder created: {session_folder}")


def update_workflow_progress():
    """Update workflow progress based on current agent status"""
    if st.session_state.synthesis_complete:
        st.session_state.workflow_progress = 100
        st.session_state.current_agent = "Complete ✅"
    elif st.session_state.synthesis_status == "running":
        st.session_state.workflow_progress = 66
        st.session_state.current_agent = "Synthesis Agent 🎨"
    elif st.session_state.info_gatherer_complete:
        st.session_state.workflow_progress = 66
        st.session_state.current_agent = "Information Gatherer Complete ✅"
    elif st.session_state.info_gatherer_status == "running":
        st.session_state.workflow_progress = 33
        st.session_state.current_agent = "Information Gatherer 📊"
    elif st.session_state.engagement_complete:
        st.session_state.workflow_progress = 33
        st.session_state.current_agent = "Engagement Complete ✅"
    elif st.session_state.engagement_status == "running":
        st.session_state.workflow_progress = 10
        st.session_state.current_agent = "Engagement Agent 💬"
    else:
        st.session_state.workflow_progress = 0
        st.session_state.current_agent = "Ready to Start"


def render_workflow_progress():
    """Render workflow progress bar at bottom after conversation"""
    update_workflow_progress()
    
    st.markdown("---")  # Divider line
    
    st.markdown("""
    <div class="progress-section">
        <h4>🔄 Workflow Progress</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress_value = st.session_state.workflow_progress / 100
    st.progress(progress_value)
    
    # Current status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"**Current Status:** {st.session_state.current_agent}")
    
    with col2:
        st.write(f"**Progress:** {st.session_state.workflow_progress}%")
    
    # Phase indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.engagement_complete:
            st.write("✅ **Engagement**")
        elif st.session_state.engagement_status == "running":
            st.write("🔄 **Engagement**")
        else:
            st.write("⏳ **Engagement**")
    
    with col2:
        if st.session_state.info_gatherer_complete:
            st.write("✅ **Info Gatherer**")
        elif st.session_state.info_gatherer_status == "running":
            st.write("🔄 **Info Gatherer**")
        else:
            st.write("⏳ **Info Gatherer**")
    
    with col3:
        if st.session_state.synthesis_complete:
            st.write("✅ **Synthesis**")
        elif st.session_state.synthesis_status == "running":
            st.write("🔄 **Synthesis**")
        else:
            st.write("⏳ **Synthesis**")


def find_manifest_json(infoagent_output_path):
    """
    Find manifest.json in infoagent_output folder.
    First check root level, then check subfolders.
    """
    infoagent_path = Path(infoagent_output_path)
    
    # Check root level first
    manifest_root = infoagent_path / "manifest.json"
    if manifest_root.exists():
        st.session_state.session_logger.info(f"Found manifest.json at root level: {manifest_root}")
        return str(manifest_root)
    
    # Check subfolders
    for item in infoagent_path.iterdir():
        if item.is_dir():
            manifest_subfolder = item / "manifest.json"
            if manifest_subfolder.exists():
                st.session_state.session_logger.info(f"Found manifest.json in subfolder: {manifest_subfolder}")
                return str(manifest_subfolder)
    
    # Not found
    st.session_state.session_logger.warning(f"manifest.json not found in {infoagent_path} or its subfolders")
    return None


def render_sidebar():
    """Render sidebar with session info and agent status"""
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Session Information (No folder info as requested)
        st.markdown(f"""
        <div class="session-info">
            <h4>📋 Session Info</h4>
            <p><strong>Session ID:</strong><br><code>{st.session_state.session_id[:8]}...</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        # JSON Completion Percentage
        st.subheader("📊 Progress Metrics")
        try:
            completion_pct = st.session_state.agent.get_completion_percentage(st.session_state.session_id)
            st.metric("JSON Completion", f"{completion_pct:.0f}%")
        except:
            st.metric("JSON Completion", "N/A")
        
        # Reset Conversation Button
        st.divider()
        if st.button("🔄 Reset Conversation", type="secondary", use_container_width=True):
            reset_conversation()
        
        if st.button("🆕 New Session", type="primary", use_container_width=True):
            reset_session()
        
        # Agent Status Pipeline
        st.divider()
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
        
        # Error display
        if st.session_state.last_error:
            st.divider()
            st.subheader("❌ Last Error")
            st.error(st.session_state.last_error)


def reset_conversation():
    """Reset only the conversation, keep session"""
    st.session_state.session_logger.info("Resetting conversation")
    
    # Reset conversation and engagement state
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Hello! I'm your QBR assistant. I can help you create a new QBR or refresh an existing report. What would you like to do today?"
    })
    
    # Reset engagement state
    st.session_state.engagement_complete = False
    st.session_state.engagement_status = "pending"
    st.session_state.final_spec = None
    st.session_state.last_error = None
    
    # Reset progress
    st.session_state.workflow_progress = 0
    st.session_state.current_agent = "Ready to Start"
    
    # Keep session folder and other agent states
    save_conversation_json()
    st.rerun()


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
        update_workflow_progress()
        st.session_state.session_logger.info("Starting Information Gatherer")
        
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
        
        st.session_state.session_logger.info(f"Information Gatherer config: {config}")
        
        # Run the information gatherer
        result = run_information_gatherer(data_config=config)
        
        if result:
            st.session_state.info_gatherer_status = "complete"
            st.session_state.info_gatherer_complete = True
            update_workflow_progress()
            st.session_state.session_logger.info("Information Gatherer completed successfully")
            return True
        else:
            st.session_state.info_gatherer_status = "error"
            st.session_state.last_error = "Information Gatherer failed to complete"
            st.session_state.session_logger.error("Information Gatherer failed")
            return False
            
    except Exception as e:
        st.session_state.info_gatherer_status = "error"
        st.session_state.last_error = f"Information Gatherer error: {str(e)}"
        st.session_state.session_logger.error(f"Information Gatherer error: {e}", exc_info=True)
        return False


def run_synthesis():
    """Run the Synthesis agent"""
    try:
        st.session_state.synthesis_status = "running"
        update_workflow_progress()
        st.session_state.session_logger.info("Starting Synthesis Agent")
        
        # Setup config for this session
        session_folder = Path(st.session_state.session_folder)
        infoagent_output_path = session_folder / "infoagent_output"
        
        # Find manifest.json using the new logic
        manifest_path = find_manifest_json(infoagent_output_path)
        
        if not manifest_path:
            st.session_state.synthesis_status = "error"
            st.session_state.last_error = "manifest.json not found in infoagent_output or its subfolders"
            st.session_state.session_logger.error("manifest.json not found for synthesis")
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
        
        st.session_state.session_logger.info(f"Synthesis Agent config: {config}")
        st.session_state.session_logger.info(f"Using manifest path: {manifest_path}")
        
        # Run the synthesis agent
        result = run_synthesis_agent(config)
        
        if result:
            st.session_state.synthesis_status = "complete"
            st.session_state.synthesis_complete = True
            update_workflow_progress()
            
            # Look for the generated PowerPoint file
            output_dir = session_folder / "synthesis_output"
            pptx_files = list(output_dir.glob("*.pptx"))
            
            if pptx_files:
                st.session_state.presentation_path = str(pptx_files[0])
                st.session_state.session_logger.info(f"Presentation created: {st.session_state.presentation_path}")
            
            st.session_state.session_logger.info("Synthesis Agent completed successfully")
            return True
        else:
            st.session_state.synthesis_status = "error"
            st.session_state.last_error = "Synthesis Agent failed to complete"
            st.session_state.session_logger.error("Synthesis Agent failed")
            return False
            
    except Exception as e:
        st.session_state.synthesis_status = "error"
        st.session_state.last_error = f"Synthesis Agent error: {str(e)}"
        st.session_state.session_logger.error(f"Synthesis Agent error: {e}", exc_info=True)
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
        
        st.session_state.session_logger.info(f"Engagement spec saved to: {spec_path}")
        return True
        
    except Exception as e:
        st.session_state.session_logger.error(f"Error saving engagement spec: {e}")
        return False


def render_download_button():
    """Render download button at bottom right when presentation is ready"""
    if st.session_state.presentation_path and os.path.exists(st.session_state.presentation_path):
        st.markdown("---")  # Divider line
        
        # Create columns for bottom right alignment
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.success("🎉 Your QBR presentation is ready!")
        
        with col3:  # Bottom right column
            # Read the file for download
            with open(st.session_state.presentation_path, 'rb') as f:
                file_data = f.read()
            
            filename = f"QBR_{st.session_state.session_id[:8]}.pptx"
            
            st.download_button(
                label="📊 Download PPT",
                data=file_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
                use_container_width=True
            )


def render_tips():
    """Render helpful tips at the bottom"""
    st.markdown("""
    <div class="tip-section">
        💡 <strong>Tips:</strong> You can mention multiple things at once. I'll understand context from our conversation. Feel free to correct me if I misunderstand!
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application flow"""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title("🚀 AI Powered QBR")
    st.caption("Sequential AI Agent Pipeline: Engagement → Information Gatherer → Synthesis")
    
    # Auto-progress workflow
    auto_progress_workflow()
    
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
            
            # Save conversation
            save_conversation_json()
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Update engagement status
            st.session_state.engagement_status = "running"
            update_workflow_progress()
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Processing..."):
                    try:
                        # Process message
                        response = st.session_state.agent.process_message(
                            st.session_state.session_id,
                            prompt
                        )
                        
                        # Log user message
                        st.session_state.session_logger.info(f"User: {prompt}")
                        
                        # Handle both string and dict responses
                        if isinstance(response, dict):
                            reply_text = response["reply"]
                            st.markdown(reply_text)
                            
                            # Log assistant response
                            st.session_state.session_logger.info(f"Assistant: {reply_text}")
                            
                            # Add to message history
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": reply_text
                            })
                            
                            # Check for completion
                            if response.get("spec_complete"):
                                st.session_state.engagement_status = "complete"
                                st.session_state.engagement_complete = True
                                update_workflow_progress()
                                
                                # Save the final spec
                                final_spec = response.get("final_spec") or st.session_state.agent.get_final_spec(st.session_state.session_id)
                                st.session_state.final_spec = final_spec
                                
                                if final_spec:
                                    save_engagement_spec(final_spec)
                                    st.success("✅ Engagement complete! Starting Information Gatherer...")
                                    st.session_state.session_logger.info("Engagement completed successfully")
                                
                                # Save conversation
                                save_conversation_json()
                                st.rerun()
                        else:
                            # String response
                            st.markdown(response)
                            st.session_state.session_logger.info(f"Assistant: {response}")
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": response
                            })
                        
                        # Save conversation after each exchange
                        save_conversation_json()
                        
                        # Update status
                        st.session_state.engagement_status = "pending"
                        update_workflow_progress()
                        
                    except Exception as e:
                        st.session_state.engagement_status = "error"
                        st.session_state.last_error = f"Engagement error: {str(e)}"
                        
                        st.session_state.session_logger.error(f"Error processing message: {e}", exc_info=True)
                        error_msg = "I apologize, but I encountered an issue. Could you please try again? 🔄"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        save_conversation_json()
            
            # Check if complete after processing (backup check)
            if not st.session_state.engagement_complete and st.session_state.agent.is_complete(st.session_state.session_id):
                st.session_state.engagement_status = "complete"
                st.session_state.engagement_complete = True
                update_workflow_progress()
                
                # Save final spec
                final_spec = st.session_state.agent.get_final_spec(st.session_state.session_id)
                st.session_state.final_spec = final_spec
                
                if final_spec:
                    save_engagement_spec(final_spec)
                
                save_conversation_json()
                st.rerun()
    
    else:
        # Engagement complete - show status
        if st.session_state.synthesis_complete:
            st.success("🎉 All agents completed successfully! Your QBR presentation is ready.")
        elif st.session_state.info_gatherer_complete:
            st.info("📝 Information gathering complete. Synthesis agent running...")
        elif st.session_state.engagement_complete:
            st.info("💬 Engagement complete. Information gatherer running...")
    
    # ✅ Progress bar at bottom after conversation
    render_workflow_progress()
    
    # ✅ Download button at bottom right (only if synthesis complete)
    if st.session_state.synthesis_complete:
        render_download_button()
    
    # Render tips at the very bottom
    render_tips()


if __name__ == "__main__":
    main()
