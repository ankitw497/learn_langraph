"""
Production Streamlit UI for QBR Orchestrator with Real Agents.
Integrates QBREngagementAgentSync, Information Gatherer, and Synthesis Agent.
"""
import asyncio
import json
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
from orchestrator.production_orchestrator import ProductionQBROrchestrator

# Import your real agents for direct access
from engagement.agent import QBREngagementAgentSync


class ProductionQBRStreamlitApp:
    """Production Streamlit application for real QBR agents."""
    
    def __init__(self):
        self.orchestrator = ProductionQBROrchestrator()
    
    def run(self):
        """Run the Streamlit application."""
        st.set_page_config(
            page_title="QBR Orchestrator - Production",
            page_icon="📊", 
            layout="wide"
        )
        
        # Initialize session state
        self._initialize_session_state()
        
        # Render UI
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
    
    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'workflow_status' not in st.session_state:
            st.session_state.workflow_status = "not_started"
        
        if 'current_phase' not in st.session_state:
            st.session_state.current_phase = "engagement"
        
        if 'qbr_spec' not in st.session_state:
            st.session_state.qbr_spec = None
        
        if 'presentation_result' not in st.session_state:
            st.session_state.presentation_result = None
    
    def _render_header(self):
        """Render the main header."""
        st.title("📊 QBR Orchestrator - Production")
        st.caption("Powered by Real AI Agents: Engagement → Information Gatherer → Synthesis")
        
        # Status indicator
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Session ID", st.session_state.session_id[-8:])
        
        with col2:
            phase_emoji = {
                "engagement": "💬",
                "information_gathering": "📊", 
                "synthesis": "📝",
                "complete": "✅",
                "error": "❌"
            }
            st.metric("Current Phase", f"{phase_emoji.get(st.session_state.current_phase, '⏳')} {st.session_state.current_phase.title()}")
        
        with col3:
            if st.session_state.workflow_status == "engagement_complete":
                completion = 33
            elif st.session_state.workflow_status == "info_gathering_complete": 
                completion = 66
            elif st.session_state.workflow_status == "complete":
                completion = 100
            else:
                completion = 0
            st.metric("Progress", f"{completion}%")
        
        with col4:
            if st.button("🔄 New Session"):
                self._reset_session()
                st.rerun()
    
    def _render_sidebar(self):
        """Render sidebar with controls and examples."""
        with st.sidebar:
            st.header("🎛️ Control Panel")
            
            # Session status
            session_status = self.orchestrator.get_session_status(st.session_state.session_id)
            
            st.subheader("Session Status")
            st.json(session_status)
            
            # Example queries
            st.subheader("📋 Example Queries")
            
            examples = [
                {
                    "name": "TechCorp Q3 2025",
                    "query": "Generate a QBR for TechCorp Industries for Q3 2025. Focus on revenue growth, customer satisfaction, and operational efficiency. Include revenue, customer NPS, cost reduction, and market share metrics."
                },
                {
                    "name": "Financial Services",
                    "query": "Create a quarterly business review for Wells Fargo Bank for Q4 2024. Focus on credit risk analysis for Bankcard products. Include delinquency rates, account balances, and year-over-year trends."
                },
                {
                    "name": "Retail Chain Analysis", 
                    "query": "I need a QBR for Walmart for Q2 2025. Focus on sales performance, inventory management, and customer satisfaction across different regions."
                }
            ]
            
            for example in examples:
                if st.button(f"📄 {example['name']}", key=f"example_{example['name']}", use_container_width=True):
                    st.session_state.example_query = example['query']
                    st.rerun()
            
            # Workflow actions
            st.subheader("🚀 Workflow Actions")
            
            if session_status.get("can_proceed"):
                if st.button("▶️ Complete QBR Workflow", type="primary"):
                    st.session_state.trigger_workflow = True
                    st.rerun()
            
            if st.button("🗑️ Clear Messages"):
                st.session_state.messages = []
                st.rerun()
            
            # Debug info
            with st.expander("🔍 Debug Info"):
                st.text(f"Session ID: {st.session_state.session_id}")
                st.text(f"Status: {st.session_state.workflow_status}")
                st.text(f"Phase: {st.session_state.current_phase}")
                st.text(f"Messages: {len(st.session_state.messages)}")
    
    def _render_main_content(self):
        """Render main content area."""
        # Handle example query injection
        if hasattr(st.session_state, 'example_query'):
            st.session_state.user_input = st.session_state.example_query
            del st.session_state.example_query
            
        # Handle workflow trigger
        if hasattr(st.session_state, 'trigger_workflow'):
            self._complete_workflow()
            del st.session_state.trigger_workflow
        
        # Chat interface
        self._render_chat_interface()
        
        # Results section
        if st.session_state.presentation_result:
            self._render_results()
    
    def _render_chat_interface(self):
        """Render the chat interface."""
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show timestamp for debugging
                if "timestamp" in message:
                    st.caption(f"🕒 {message['timestamp']}")
        
        # Handle user input
        if hasattr(st.session_state, 'user_input'):
            user_input = st.session_state.user_input
            del st.session_state.user_input
            self._process_user_message(user_input)
        
        # Chat input
        if prompt := st.chat_input("Ask about your QBR requirements..."):
            self._process_user_message(prompt)
    
    def _process_user_message(self, user_input: str):
        """Process user message through the engagement agent."""
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Show user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process through orchestrator
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing your request..."):
                try:
                    # Run the conversation through orchestrator
                    result = asyncio.run(
                        self.orchestrator.process_conversation_message(
                            st.session_state.session_id,
                            user_input
                        )
                    )
                    
                    # Update session state
                    st.session_state.current_phase = result.current_phase
                    
                    if result.is_engagement_complete:
                        st.session_state.workflow_status = "engagement_complete"
                        st.session_state.qbr_spec = result.final_qbr_spec
                        
                        # Show completion message
                        completion_msg = f"✅ **Engagement Complete!** \n\n{result.engagement_response}\n\n🚀 Ready to proceed with Information Gathering and Synthesis."
                        st.markdown(completion_msg)
                        
                        # Add to messages
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": completion_msg,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                        # Show final spec
                        with st.expander("📋 Final QBR Specification"):
                            st.json(result.final_qbr_spec)
                    
                    else:
                        # Regular conversation response
                        st.markdown(result.engagement_response)
                        
                        # Add to messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result.engagement_response, 
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                
                except Exception as e:
                    error_msg = f"❌ Error processing message: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
        
        st.rerun()
    
    def _complete_workflow(self):
        """Complete the full QBR workflow."""
        with st.spinner("🚀 Running complete QBR workflow..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Information Gathering
                status_text.text("📊 Step 2/3: Gathering and analyzing data...")
                progress_bar.progress(33)
                
                # Step 2: Synthesis
                status_text.text("📝 Step 3/3: Generating presentation...")
                progress_bar.progress(66)
                
                # Complete workflow
                result = asyncio.run(
                    self.orchestrator.complete_qbr_workflow(st.session_state.session_id)
                )
                
                progress_bar.progress(100)
                status_text.text("✅ QBR workflow complete!")
                
                # Update session state
                st.session_state.workflow_status = "complete"
                st.session_state.current_phase = "complete"
                st.session_state.presentation_result = result.presentation_result
                
                # Success message
                st.success("🎉 QBR Generation Complete!")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Workflow failed: {str(e)}")
                status_text.text("❌ Workflow failed")
                progress_bar.progress(0)
    
    def _render_results(self):
        """Render the results section with download options."""
        st.divider()
        st.header("📥 Download Your QBR")
        
        result = st.session_state.presentation_result
        
        if result and result.get('status') == 'success':
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 Presentation Ready")
                st.write(f"**Slides Created:** {result.get('slides_count', 0)}")
                st.write(f"**Insights Found:** {result.get('insights_count', 0)}")
                
                if result.get('qa_results'):
                    qa = result['qa_results']
                    st.write(f"**Quality Status:** {qa.get('overall_status', 'Unknown')}")
            
            with col2:
                # Download button
                presentation_path = result.get('presentation_path')
                if presentation_path and os.path.exists(presentation_path):
                    with open(presentation_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Extract filename
                    filename = os.path.basename(presentation_path)
                    if not filename.endswith('.pptx'):
                        filename = f"QBR_{st.session_state.session_id[:8]}.pptx"
                    
                    st.download_button(
                        label="📊 Download PowerPoint",
                        data=file_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        type="primary",
                        use_container_width=True
                    )
            
            # Show QA results if available
            if result.get('qa_results'):
                with st.expander("🔍 Quality Assurance Results"):
                    qa = result['qa_results']
                    st.json(qa)
        
        else:
            st.error("❌ Presentation generation failed")
            if result and result.get('error'):
                st.text(f"Error: {result['error']}")
    
    def _reset_session(self):
        """Reset the session and start fresh."""
        # Clear session state
        keys_to_keep = ['session_id']  # Keep session_id to maintain orchestrator state
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        
        # Generate new session
        st.session_state.session_id = str(uuid.uuid4())
        
        # Reinitialize
        self._initialize_session_state()


def main():
    """Main entry point for the Streamlit app."""
    app = ProductionQBRStreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
