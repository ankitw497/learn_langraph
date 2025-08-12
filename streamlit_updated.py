import asyncio
import json
import logging
import os
import uuid
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from orchestrator.file_based_orchestrator import FileBasedQBROrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileBasedQBRStreamlitApp:
    """File-based Streamlit application with auto-workflow progression."""
    
    def __init__(self):
        # Use session state to maintain orchestrator instance
        if 'orchestrator' not in st.session_state:
            st.session_state.orchestrator = FileBasedQBROrchestrator()
        self.orchestrator = st.session_state.orchestrator
    
    def run(self):
        """Run the Streamlit application."""
        st.set_page_config(
            page_title="QBR Orchestrator - File Based",
            page_icon="📊", 
            layout="wide"
        )
        
        # Initialize session state
        self._initialize_session_state()
        
        # Render UI components
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
    
    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            logger.info(f"Created new session: {st.session_state.session_id}")
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'engagement_complete' not in st.session_state:
            st.session_state.engagement_complete = False
        
        if 'workflow_running' not in st.session_state:
            st.session_state.workflow_running = False
        
        if 'workflow_complete' not in st.session_state:
            st.session_state.workflow_complete = False
        
        if 'qbr_spec' not in st.session_state:
            st.session_state.qbr_spec = None
        
        if 'presentation_result' not in st.session_state:
            st.session_state.presentation_result = None
        
        if 'current_phase' not in st.session_state:
            st.session_state.current_phase = "engagement"
        
        if 'completion_percentage' not in st.session_state:
            st.session_state.completion_percentage = 0.0
        
        if 'frustration_index' not in st.session_state:
            st.session_state.frustration_index = 0.0
        
        if 'json_completion_percentage' not in st.session_state:
            st.session_state.json_completion_percentage = 0.0
        
        if 'auto_trigger_workflow' not in st.session_state:
            st.session_state.auto_trigger_workflow = False
        
        # Add initial greeting if no messages exist
        if len(st.session_state.messages) == 0:
            self._add_initial_greeting()
    
    def _add_initial_greeting(self):
        """Add initial greeting from the engagement agent."""
        initial_greeting = {
            "role": "assistant",
            "content": "👋 Hello! I'm your QBR assistant. I can help you create a new QBR or refresh an existing report. What would you like to do today?"
        }
        st.session_state.messages.append(initial_greeting)
        logger.info("Added initial greeting message")
    
    def _render_header(self):
        """Render the main header with phase indicators."""
        st.title("📊 QBR Orchestrator - File Based")
        st.caption("Real AI Agents: Engagement Agent → Information Gatherer → Synthesis Agent")
        
        # Phase indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Session ID", st.session_state.session_id[-8:])
        
        with col2:
            # Phase indicator with clear status
            phase_status = self._get_phase_status()
            st.metric("Current Phase", phase_status["display"])
        
        with col3:
            # Progress percentage
            progress = st.session_state.completion_percentage
            st.metric("Progress", f"{progress:.0f}%")
        
        with col4:
            if st.button("🔄 New Session"):
                self._reset_session()
                st.rerun()
        
        # Progress bar
        if progress > 0:
            st.progress(progress / 100.0)
    
    def _get_phase_status(self):
        """Get current phase status with emoji and description."""
        if st.session_state.workflow_complete:
            return {"display": "✅ Complete", "description": "QBR presentation ready for download"}
        elif st.session_state.workflow_running:
            return {"display": "⚙️ Workflow Running", "description": "Generating QBR presentation"}
        elif st.session_state.engagement_complete:
            return {"display": "🚀 Auto-Processing", "description": "Automatically starting full workflow"}
        else:
            return {"display": "💬 Chatting", "description": "Gathering QBR requirements"}
    
    def _render_sidebar(self):
        """Render sidebar with controls, status, and file tracking."""
        with st.sidebar:
            st.header("🎛️ Control Panel")
            
            # Real-time session status from orchestrator
            self._render_session_status()
            
            # Engagement metrics
            self._render_engagement_metrics()
            
            # File tracking
            self._render_file_tracking()
            
            # Phase explanation
            self._render_phase_explanation()
            
            # Workflow controls (simplified)
            self._render_workflow_controls()
            
            # Debug information
            self._render_debug_info()
    
    def _render_session_status(self):
        """Render real-time session status."""
        st.subheader("📊 Live Session Status")
        
        try:
            status = self.orchestrator.get_session_status(st.session_state.session_id)
            
            # Engagement status
            if 'engagement' in status:
                eng_status = status['engagement']
                if 'error' in eng_status:
                    st.error(f"Engagement Error: {eng_status['error']}")
                else:
                    is_complete = eng_status.get('is_complete', False)
                    completion_pct = eng_status.get('completion_percentage', 0)
                    
                    if is_complete:
                        st.success("✅ Engagement Complete")
                        st.session_state.engagement_complete = True
                        st.session_state.completion_percentage = 33.0
                        # 🎯 Auto-trigger workflow when engagement completes
                        if not st.session_state.auto_trigger_workflow and not st.session_state.workflow_running:
                            st.session_state.auto_trigger_workflow = True
                    else:
                        st.info(f"💬 Engagement: {completion_pct:.1f}%")
                        st.session_state.completion_percentage = completion_pct * 0.33
            
            # Workflow status
            if 'workflow' in status:
                wf_status = status['workflow']
                current_phase = wf_status.get('current_phase', 'engagement')
                st.session_state.current_phase = current_phase
                
                if wf_status.get('has_presentation'):
                    st.success("🎉 Presentation Ready!")
                    st.session_state.workflow_complete = True
                    st.session_state.completion_percentage = 100.0
                elif wf_status.get('synthesis_complete'):
                    st.info("📝 Synthesis Complete")
                    st.session_state.completion_percentage = 90.0
                elif wf_status.get('info_gathering_complete'):
                    st.info("📊 Information Gathering Complete")
                    st.session_state.completion_percentage = 66.0
            
            # Show status details
            with st.expander("📋 Detailed Status"):
                st.json(status)
                
        except Exception as e:
            st.error(f"Status Error: {str(e)}")
    
    def _render_engagement_metrics(self):
        """Render JSON completion percentage and frustration index."""
        st.subheader("📈 Engagement Metrics")
        
        try:
            # Get metrics from engagement agent
            if hasattr(self.orchestrator.engagement_agent, 'get_completion_percentage'):
                completion_pct = self.orchestrator.engagement_agent.get_completion_percentage(st.session_state.session_id)
                st.session_state.json_completion_percentage = completion_pct
            
            # Get frustration index if available
            frustration = 0.0
            if hasattr(self.orchestrator.engagement_agent, 'get_frustration_index'):
                frustration = self.orchestrator.engagement_agent.get_frustration_index(st.session_state.session_id)
                st.session_state.frustration_index = frustration
            else:
                # Calculate simple frustration based on message count without completion
                message_count = len([m for m in st.session_state.messages if m["role"] == "user"])
                if message_count > 3 and not st.session_state.engagement_complete:
                    frustration = min((message_count - 3) * 10, 50)  # Max 50% frustration
                st.session_state.frustration_index = frustration
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "JSON Completion %", 
                    f"{st.session_state.json_completion_percentage:.1f}%",
                    delta=None
                )
            
            with col2:
                # Color code frustration index
                frustration_color = "🟢" if frustration < 20 else "🟡" if frustration < 40 else "🔴"
                st.metric(
                    f"{frustration_color} Frustration Index", 
                    f"{st.session_state.frustration_index:.1f}%",
                    delta=None
                )
            
            # Progress bars
            st.caption("JSON Completion Progress:")
            st.progress(st.session_state.json_completion_percentage / 100.0)
            
            if st.session_state.frustration_index > 0:
                st.caption("Frustration Level:")
                st.progress(st.session_state.frustration_index / 100.0)
            
        except Exception as e:
            logger.warning(f"Could not get engagement metrics: {e}")
            st.warning("Metrics temporarily unavailable")
    
    def _render_file_tracking(self):
        """Render file tracking information."""
        st.subheader("📁 File Tracking")
        
        try:
            status = self.orchestrator.get_session_status(st.session_state.session_id)
            
            # Session folder info
            session_folder = status.get("session_folder")
            if session_folder:
                st.text(f"📂 Session Folder:")
                st.code(session_folder, language="text")
            
            # File counts
            col1, col2, col3 = st.columns(3)
            
            with col1:
                eng_files = status.get("engagement", {}).get("output_files", 0)
                st.metric("📝 Engagement Files", eng_files)
            
            with col2:
                info_files = status.get("workflow", {}).get("info_files", 0)
                st.metric("📊 Info Files", info_files)
            
            with col3:
                synth_files = status.get("workflow", {}).get("synthesis_files", 0)
                st.metric("📋 Synthesis Files", synth_files)
            
            # Show session folder contents if it exists
            if session_folder and Path(session_folder).exists():
                with st.expander("📂 Session Files"):
                    session_path = Path(session_folder)
                    for subfolder in ["engagement_output", "infoagent_output", "synthesis_output"]:
                        subfolder_path = session_path / subfolder
                        if subfolder_path.exists():
                            st.text(f"{subfolder}/")
                            for file_path in subfolder_path.glob("*"):
                                if file_path.is_file():
                                    st.text(f"  📄 {file_path.name}")
        
        except Exception as e:
            logger.warning(f"Could not get file tracking info: {e}")
    
    def _render_phase_explanation(self):
        """Explain when each agent is called."""
        st.subheader("🔄 Agent Execution Flow")
        
        phases = [
            {
                "name": "💬 Engagement Agent",
                "when": "Every chat message",
                "what": "Saves spec to engagement_output/",
                "status": "✅" if st.session_state.engagement_complete else "🔄" if st.session_state.completion_percentage > 0 else "⏳"
            },
            {
                "name": "📊 Information Gatherer", 
                "when": "Auto-triggered after engagement",
                "what": "Reads engagement_output/, saves to infoagent_output/",
                "status": "✅" if st.session_state.completion_percentage >= 66 else "⏳"
            },
            {
                "name": "📝 Synthesis Agent",
                "when": "Auto-triggered after info gathering", 
                "what": "Reads both folders, saves to synthesis_output/",
                "status": "✅" if st.session_state.workflow_complete else "⏳"
            }
        ]
        
        for phase in phases:
            with st.container():
                st.write(f"{phase['status']} **{phase['name']}**")
                st.caption(f"*When:* {phase['when']}")
                st.caption(f"*What:* {phase['what']}")
                st.divider()
    
    def _render_workflow_controls(self):
        """Render simplified workflow control buttons."""
        st.subheader("🚀 Controls")
        
        # Show auto-flow status
        if st.session_state.engagement_complete and not st.session_state.workflow_complete:
            st.info("🤖 **Auto-Flow Enabled**\nWorkflow will start automatically after engagement completes!")
        
        # Reset buttons only
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True, disabled=st.session_state.workflow_running):
                # Clear messages but keep initial greeting
                st.session_state.messages = []
                self._add_initial_greeting()
                st.session_state.engagement_complete = False
                st.session_state.qbr_spec = None
                st.session_state.completion_percentage = 0.0
                st.session_state.json_completion_percentage = 0.0
                st.session_state.frustration_index = 0.0
                st.session_state.auto_trigger_workflow = False
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset All", use_container_width=True, disabled=st.session_state.workflow_running):
                self._reset_session()
                st.rerun()
    
    def _render_debug_info(self):
        """Render debug information."""
        with st.expander("🔍 Debug Info"):
            debug_info = {
                "Session ID": st.session_state.session_id,
                "Messages": len(st.session_state.messages),
                "Engagement Complete": st.session_state.engagement_complete,
                "Workflow Running": st.session_state.workflow_running,
                "Workflow Complete": st.session_state.workflow_complete,
                "Current Phase": st.session_state.current_phase,
                "Completion %": st.session_state.completion_percentage,
                "JSON Completion %": st.session_state.json_completion_percentage,
                "Frustration Index": st.session_state.frustration_index,
                "Auto Trigger": st.session_state.auto_trigger_workflow
            }
            st.json(debug_info)
    
    def _render_main_content(self):
        """Render main content area."""
        # Handle auto-workflow trigger first
        self._handle_auto_workflow_trigger()
        
        # Main content tabs
        tab1, tab2 = st.tabs(["💬 Chat with QBR Assistant", "📊 QBR Results"])
        
        with tab1:
            self._render_chat_interface()
        
        with tab2:
            self._render_results_tab()
    
    def _handle_auto_workflow_trigger(self):
        """Handle automatic workflow trigger when engagement completes."""
        if st.session_state.auto_trigger_workflow and not st.session_state.workflow_running:
            logger.info("Auto-triggering workflow after engagement completion")
            st.session_state.auto_trigger_workflow = False
            self._start_full_workflow()
    
    def _render_chat_interface(self):
        """Render the chat interface for engagement agent."""
        st.subheader("💬 QBR Assistant Chat")
        st.caption("The QBR assistant will understand your requirements and automatically start the workflow")
        
        # Show workflow progress if running
        if st.session_state.workflow_running:
            self._render_workflow_progress()
        
        # Display chat messages (without timestamps)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input - disable when workflow is running
        if not st.session_state.workflow_running and not st.session_state.workflow_complete:
            prompt = st.chat_input("Tell me about your QBR requirements...")
            if prompt:
                self._process_engagement_message(prompt)
        elif st.session_state.workflow_running:
            st.info("🔄 **Workflow in progress...** The system is automatically processing your QBR.")
        elif st.session_state.workflow_complete:
            st.success("✅ **QBR Generation Complete!** Check the Results tab for your presentation.")
        
        # Show engagement completion status
        if st.session_state.engagement_complete and not st.session_state.workflow_running and not st.session_state.workflow_complete:
            st.success("✅ **Requirements Gathered!** Starting automatic workflow...")
    
    def _render_workflow_progress(self):
        """Render workflow progress bar and status."""
        st.subheader("🔄 Workflow Progress")
        
        # Progress bar
        progress = st.session_state.completion_percentage
        progress_bar = st.progress(progress / 100.0)
        
        # Status text based on phase
        if st.session_state.current_phase == "information_gathering":
            st.info("📊 **Information Gatherer Running**\nReading engagement output and enriching data...")
        elif st.session_state.current_phase == "synthesis":
            st.info("📝 **Synthesis Agent Running**\nCreating PowerPoint presentation...")
        else:
            st.info(f"🔄 **Processing** - Current phase: {st.session_state.current_phase}")
        
        # Phase checklist
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅" if st.session_state.engagement_complete else "⏳"
            st.write(f"{status} Engagement Complete")
        
        with col2:
            status = "✅" if st.session_state.completion_percentage >= 66 else "🔄" if st.session_state.completion_percentage > 33 else "⏳"
            st.write(f"{status} Information Gathering")
        
        with col3:
            status = "✅" if st.session_state.workflow_complete else "🔄" if st.session_state.completion_percentage > 66 else "⏳"
            st.write(f"{status} Synthesis Complete")
    
    def _render_results_tab(self):
        """Render the results tab."""
        if not st.session_state.engagement_complete:
            st.info("💡 Complete the chat conversation first to see results here.")
            return
        
        if st.session_state.workflow_running:
            st.info("⚙️ Workflow is running automatically... Results will appear here when complete.")
            self._render_workflow_progress()
            return
        
        if not st.session_state.workflow_complete:
            st.warning("🔄 Workflow will start automatically after engagement completes.")
            return
        
        # Show results
        self._render_final_results()
    
    def _process_engagement_message(self, user_input: str):
        """Process message through engagement agent only."""
        # Add user message to chat (without timestamp)
        user_message = {
            "role": "user",
            "content": user_input
        }
        st.session_state.messages.append(user_message)
        
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process through engagement agent
        with st.chat_message("assistant"):
            with st.spinner("🤔 QBR assistant is thinking..."):
                try:
                    # Call orchestrator to handle engagement
                    result = asyncio.run(
                        self.orchestrator.process_conversation_message(
                            st.session_state.session_id,
                            user_input
                        )
                    )
                    
                    # Display response
                    if result.error_message:
                        error_msg = f"❌ Error: {result.error_message}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                    else:
                        # Show engagement response
                        st.markdown(result.engagement_response)
                        
                        # Add to messages (without timestamp)
                        assistant_message = {
                            "role": "assistant",
                            "content": result.engagement_response
                        }
                        st.session_state.messages.append(assistant_message)
                        
                        # Update session state
                        if result.is_engagement_complete:
                            st.session_state.engagement_complete = True
                            st.session_state.qbr_spec = result.final_qbr_spec
                            st.session_state.completion_percentage = 33.0
                            
                            # 🎯 Set auto-trigger flag - workflow will start automatically
                            st.session_state.auto_trigger_workflow = True
                            
                            # Show completion message
                            st.success("🎉 Requirements complete! Automatically starting workflow...")
                
                except Exception as e:
                    error_msg = f"❌ Error processing message: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
        
        st.rerun()
    
    def _start_full_workflow(self):
        """Start the full QBR workflow automatically (Information Gatherer + Synthesis)."""
        st.session_state.workflow_running = True
        
        # Use a placeholder for dynamic updates
        placeholder = st.empty()
        
        with placeholder.container():
            st.info("🚀 **Starting Automatic QBR Workflow**")
            
            # Create progress container
            progress_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0.33)  # Start at 33% (engagement done)
                status_text = st.empty()
                
                try:
                    # Step 1: Information Gatherer
                    status_text.text("📊 Information Gatherer: Reading engagement output and enriching data...")
                    progress_bar.progress(0.5)
                    
                    # Brief pause to show progress
                    import time
                    time.sleep(1)
                    
                    # Step 2: Synthesis Agent
                    status_text.text("📝 Synthesis Agent: Creating PowerPoint presentation...")
                    progress_bar.progress(0.8)
                    
                    # Run full workflow
                    result = asyncio.run(
                        self.orchestrator.complete_qbr_workflow(st.session_state.session_id)
                    )
                    
                    # Handle result
                    if result.error_message:
                        status_text.text("❌ Workflow failed")
                        st.error(f"❌ Workflow failed: {result.error_message}")
                        progress_bar.progress(0.33)
                    else:
                        # Success
                        progress_bar.progress(1.0)
                        status_text.text("✅ QBR presentation complete!")
                        
                        st.session_state.workflow_complete = True
                        st.session_state.presentation_result = result.presentation_result
                        st.session_state.completion_percentage = 100.0
                        
                        st.success("🎉 **QBR Generation Complete!** Your presentation is ready in the Results tab.")
                        st.balloons()
                    
                except Exception as e:
                    status_text.text("❌ Workflow error")
                    st.error(f"❌ Workflow error: {str(e)}")
                    progress_bar.progress(0.33)
                
                finally:
                    st.session_state.workflow_running = False
        
        # Clear the placeholder after completion
        time.sleep(2)
        placeholder.empty()
        st.rerun()
    
    def _render_final_results(self):
        """Render final results with download options."""
        st.subheader("🎉 QBR Presentation Ready!")
        
        result = st.session_state.presentation_result
        
        if result and result.get('status') == 'success':
            # Results summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Slides Created", result.get('slides_count', 0))
            
            with col2:
                st.metric("💡 Insights Found", result.get('insights_count', 0))
            
            with col3:
                st.metric("📁 Session Files", "All Copied")
            
            # Download section
            st.divider()
            presentation_path = result.get('presentation_path')
            
            if presentation_path and os.path.exists(presentation_path):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📥 Download Your QBR")
                    st.write("Your PowerPoint presentation is ready for download.")
                
                with col2:
                    # Download button
                    with open(presentation_path, 'rb') as f:
                        file_data = f.read()
                    
                    filename = f"QBR_{st.session_state.session_id[:8]}.pptx"
                    
                    st.download_button(
                        label="📊 Download PowerPoint",
                        data=file_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        type="primary",
                        use_container_width=True
                    )
            
            # Show QBR specification used
            if st.session_state.qbr_spec:
                with st.expander("📋 QBR Specification Used"):
                    st.json(st.session_state.qbr_spec)
        
        else:
            st.error("❌ Presentation generation failed")
            if result and result.get('error'):
                st.text(f"Error: {result['error']}")
    
    def _reset_session(self):
        """Reset the session and start fresh."""
        # Clean up current session
        try:
            self.orchestrator.cleanup_session(st.session_state.session_id)
        except:
            pass  # Ignore cleanup errors
        
        # Clear all session state except orchestrator
        keys_to_keep = ['orchestrator']
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        
        # Reinitialize
        self._initialize_session_state()


def main():
    """Main entry point for the Streamlit app."""
    app = FileBasedQBRStreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
