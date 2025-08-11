"""
Production Streamlit UI for QBR Orchestrator with Real Agents.
Clear separation: Engagement (chat) vs Full Workflow (info gathering + synthesis)
"""
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
from orchestrator import ProductionQBROrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionQBRStreamlitApp:
    """Production Streamlit application with clear agent execution phases."""
    
    def __init__(self):
        # 🔧 FIX: Use session state to maintain orchestrator instance
        if 'orchestrator' not in st.session_state:
            st.session_state.orchestrator = ProductionQBROrchestrator()
        self.orchestrator = st.session_state.orchestrator
    
    def run(self):
        """Run the Streamlit application."""
        st.set_page_config(
            page_title="QBR Orchestrator - Production",
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
        
        # 🔧 FIX: Load existing conversation on app restart
        if len(st.session_state.messages) == 0:
            self._load_existing_conversation()
            
        # 🔧 FIX: Add initial greeting if no messages exist
        if len(st.session_state.messages) == 0:
            self._add_initial_greeting()
    
    def _add_initial_greeting(self):
        """Add initial greeting from the engagement agent."""
        initial_greeting = {
            "role": "assistant",
            "content": "Hello! I'm your QBR Engagement Agent. I'll help you create a comprehensive Quarterly Business Review. To get started, could you please tell me:\n\n1. What company or organization is this QBR for?\n2. What time period should we cover?\n3. What are the key business areas you'd like to focus on?\n\nFeel free to provide as much detail as you'd like!",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(initial_greeting)
        logger.info("Added initial greeting message")
    
    def _load_existing_conversation(self):
        """Load existing conversation from orchestrator if available."""
        try:
            status = self.orchestrator.get_session_status(st.session_state.session_id)
            
            if status.get("has_conversation", False):
                # Load conversation messages from orchestrator
                if hasattr(self.orchestrator, '_session_states') and st.session_state.session_id in self.orchestrator._session_states:
                    state = self.orchestrator._session_states[st.session_state.session_id]
                    st.session_state.messages = state.conversation_messages.copy()
                    st.session_state.engagement_complete = state.is_engagement_complete
                    st.session_state.qbr_spec = state.final_qbr_spec
                    st.session_state.current_phase = state.current_phase
                    st.session_state.completion_percentage = state.completion_percentage
                    
                    logger.info(f"Loaded {len(st.session_state.messages)} existing messages for session {st.session_state.session_id}")
                
        except Exception as e:
            logger.warning(f"Could not load existing conversation: {e}")
    
    def _render_header(self):
        """Render the main header with phase indicators."""
        st.title("📊 QBR Orchestrator - Production")
        st.caption("Real AI Agents: Engagement Agent (Chat) → Information Gatherer → Synthesis Agent")
        
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
            return {"display": "💬 Engagement Done", "description": "Ready to start full workflow"}
        else:
            return {"display": "💬 Chatting", "description": "Gathering QBR requirements"}
    
    def _render_sidebar(self):
        """Render sidebar with controls, status, and examples."""
        with st.sidebar:
            st.header("🎛️ Control Panel")
            
            # Real-time session status from orchestrator
            self._render_session_status()
            
            # 🔧 FIX: Add JSON completion and frustration metrics
            self._render_engagement_metrics()
            
            # Phase explanation
            self._render_phase_explanation()
            
            # Workflow controls
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
            
            # Try to get frustration index if available
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
    
    def _render_phase_explanation(self):
        """Explain when each agent is called."""
        st.subheader("🔄 Agent Execution Flow")
        
        phases = [
            {
                "name": "💬 Engagement Agent",
                "when": "Every chat message",
                "what": "Understands requirements, asks clarifying questions",
                "status": "✅" if st.session_state.engagement_complete else "🔄" if st.session_state.completion_percentage > 0 else "⏳"
            },
            {
                "name": "📊 Information Gatherer", 
                "when": "After engagement completion",
                "what": "Enriches data, generates tables and mappings",
                "status": "✅" if st.session_state.completion_percentage >= 66 else "⏳"
            },
            {
                "name": "📝 Synthesis Agent",
                "when": "After information gathering", 
                "what": "Creates PowerPoint presentation",
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
        """Render workflow control buttons."""
        st.subheader("🚀 Workflow Controls")
        
        # Start full workflow button
        if st.session_state.engagement_complete and not st.session_state.workflow_running and not st.session_state.workflow_complete:
            if st.button("▶️ Start Full QBR Workflow", type="primary", use_container_width=True):
                st.session_state.trigger_workflow = True
                st.rerun()
            
            st.info("💡 This will run Information Gatherer + Synthesis Agent")
        
        # Reset buttons
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
                "Frustration Index": st.session_state.frustration_index
            }
            st.json(debug_info)
    
    def _render_main_content(self):
        """Render main content area."""
        # Handle triggers
        self._handle_triggers()
        
        # Main content tabs
        tab1, tab2 = st.tabs(["💬 Chat with Engagement Agent", "📊 QBR Results"])
        
        with tab1:
            self._render_chat_interface()
        
        with tab2:
            self._render_results_tab()
    
    def _handle_triggers(self):
        """Handle various UI triggers."""
        # Workflow trigger
        if hasattr(st.session_state, 'trigger_workflow'):
            self._start_full_workflow()
            del st.session_state.trigger_workflow
    
    def _render_chat_interface(self):
        """Render the chat interface for engagement agent."""
        st.subheader("💬 Engagement Agent Chat")
        st.caption("The engagement agent will ask questions to understand your QBR requirements")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if "timestamp" in message:
                    st.caption(f"🕒 {message['timestamp']}")
        
        # Chat input - 🔧 FIX: Moved outside of any conditional or button logic
        if not st.session_state.workflow_running:
            prompt = st.chat_input("Describe your QBR requirements...")
            if prompt:
                self._process_engagement_message(prompt)
        else:
            st.info("💡 Chat is disabled while workflow is running")
        
        # Show engagement completion status
        if st.session_state.engagement_complete:
            st.success("✅ **Engagement Complete!** Ready to generate your QBR presentation.")
            
            if st.session_state.qbr_spec:
                with st.expander("📋 Final QBR Specification"):
                    st.json(st.session_state.qbr_spec)
    
    def _render_results_tab(self):
        """Render the results tab."""
        if not st.session_state.engagement_complete:
            st.info("💡 Complete the engagement chat first to see results here.")
            return
        
        if st.session_state.workflow_running:
            st.info("⚙️ Workflow is running... Results will appear here when complete.")
            return
        
        if not st.session_state.workflow_complete:
            st.warning("🚀 Click 'Start Full QBR Workflow' in the sidebar to generate your presentation.")
            return
        
        # Show results
        self._render_final_results()
    
    def _process_engagement_message(self, user_input: str):
        """Process message through engagement agent only."""
        # Add user message to chat
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process through engagement agent
        with st.chat_message("assistant"):
            with st.spinner("🤔 Engagement agent is thinking..."):
                try:
                    # 🎯 ENGAGEMENT AGENT CALLED HERE - for every chat message
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
                            "content": error_msg,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                    else:
                        # Show engagement response
                        st.markdown(result.engagement_response)
                        
                        # Add to messages - 🔧 FIX: Don't duplicate, the orchestrator already adds it
                        # Update session state directly from result
                        st.session_state.messages = result.conversation_messages.copy()
                        
                        # Update session state
                        if result.is_engagement_complete:
                            st.session_state.engagement_complete = True
                            st.session_state.qbr_spec = result.final_qbr_spec
                            st.session_state.completion_percentage = 33.0
                            
                            # Show completion message
                            st.success("🎉 Engagement complete! Ready for full workflow.")
                
                except Exception as e:
                    error_msg = f"❌ Error processing message: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
        
        # 🔧 FIX: Use st.rerun() only at the end to prevent input box issues
        st.rerun()
    
    def _start_full_workflow(self):
        """Start the full QBR workflow (Information Gatherer + Synthesis)."""
        st.session_state.workflow_running = True
        
        # Create workflow status container
        with st.container():
            st.info("🚀 Starting full QBR workflow...")
            progress_bar = st.progress(0.33)  # Start at 33% (engagement done)
            status_text = st.empty()
            
            try:
                # Update status
                status_text.text("📊 Step 2/3: Information Gatherer is analyzing data...")
                progress_bar.progress(0.5)
                
                # Update status  
                status_text.text("📝 Step 3/3: Synthesis Agent is creating presentation...")
                progress_bar.progress(0.8)
                
                # 🎯 INFORMATION GATHERER + SYNTHESIS AGENTS CALLED HERE
                result = asyncio.run(
                    self.orchestrator.complete_qbr_workflow(st.session_state.session_id)
                )
                
                # Handle result
                if result.error_message:
                    st.error(f"❌ Workflow failed: {result.error_message}")
                    status_text.text("❌ Workflow failed")
                    progress_bar.progress(0.33)
                else:
                    # Success
                    progress_bar.progress(1.0)
                    status_text.text("✅ QBR presentation complete!")
                    
                    st.session_state.workflow_complete = True
                    st.session_state.presentation_result = result.presentation_result
                    st.session_state.completion_percentage = 100.0
                    
                    st.success("🎉 QBR Generation Complete!")
                    st.balloons()
                
            except Exception as e:
                st.error(f"❌ Workflow error: {str(e)}")
                status_text.text("❌ Workflow error")
                progress_bar.progress(0.33)
            
            finally:
                st.session_state.workflow_running = False
        
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
                if result.get('qa_results'):
                    qa_status = result['qa_results'].get('overall_status', 'Unknown')
                    st.metric("✅ Quality Status", qa_status)
            
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
            
            # Quality assurance results
            if result.get('qa_results'):
                with st.expander("🔍 Quality Assurance Results"):
                    st.json(result['qa_results'])
            
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
    app = ProductionQBRStreamlitApp()
    app.run()

if __name__ == "__main__":
    main()
