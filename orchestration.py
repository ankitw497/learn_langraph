"""
Production LangGraph Orchestrator for Real QBR Agents.
Orchestrates QBREngagementAgentSync -> Information Gatherer -> Synthesis Agent
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

# Import your real agents
from engagement.agent import QBREngagementAgentSync
from setup_info_gatherer import run_information_gatherer
from synthesis.synthesis_agent import SynthesisAgentFactory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionOrchestratorState(BaseModel):
    """State object for production orchestrator."""
    session_id: str
    user_input: str = ""
    conversation_messages: list = Field(default_factory=list)
    
    # Engagement phase
    engagement_response: str = ""
    is_engagement_complete: bool = False
    final_qbr_spec: Optional[Dict[str, Any]] = None
    
    # Information gathering phase
    info_gathering_complete: bool = False
    enriched_data_path: Optional[str] = None
    tables_manifest: Optional[list] = None
    mappings: Optional[Dict[str, Any]] = None
    
    # Synthesis phase
    synthesis_complete: bool = False
    presentation_path: Optional[str] = None
    presentation_result: Optional[Dict[str, Any]] = None
    
    # Status tracking
    current_phase: str = "engagement"
    error_message: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        arbitrary_types_allowed = True


class ProductionQBROrchestrator:
    """Production LangGraph orchestrator for real QBR agents."""
    
    def __init__(self):
        self.engagement_agent = QBREngagementAgentSync()
        self.graph = self._build_graph()
        
        # Ensure data directories exist
        self.data_dir = Path("./session_data")
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info("Production QBR Orchestrator initialized")
    
    def _build_graph(self) -> CompiledStateGraph:
        """Build the LangGraph workflow for production agents."""
        workflow = StateGraph(ProductionOrchestratorState)
        
        # Add nodes
        workflow.add_node("engagement", self._engagement_node)
        workflow.add_node("information_gathering", self._information_gathering_node) 
        workflow.add_node("synthesis", self._synthesis_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Add edges
        workflow.add_edge(START, "engagement")
        
        # Conditional edges from engagement
        workflow.add_conditional_edges(
            "engagement",
            self._should_continue_from_engagement,
            {
                "continue": "information_gathering",
                "stay": "engagement", 
                "error": "error_handler"
            }
        )
        
        # Conditional edges from information gathering
        workflow.add_conditional_edges(
            "information_gathering",
            self._should_continue_from_info_gathering,
            {
                "continue": "synthesis",
                "error": "error_handler"
            }
        )
        
        # Conditional edges from synthesis
        workflow.add_conditional_edges(
            "synthesis",
            self._should_continue_from_synthesis,
            {
                "complete": END,
                "error": "error_handler"
            }
        )
        
        # Error handler edges
        workflow.add_conditional_edges(
            "error_handler",
            self._should_retry,
            {
                "retry_engagement": "engagement",
                "retry_info_gathering": "information_gathering", 
                "retry_synthesis": "synthesis",
                "end": END
            }
        )
        
        return workflow.compile()
    
    async def process_conversation_message(self, session_id: str, user_message: str) -> ProductionOrchestratorState:
        """Process a single conversation message through the engagement agent."""
        try:
            # Create or load state
            state = ProductionOrchestratorState(
                session_id=session_id,
                user_input=user_message,
                conversation_messages=self._load_conversation_history(session_id)
            )
            
            # Add user message to history
            state.conversation_messages.append({
                "role": "user", 
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Run just the engagement phase
            result = await self.graph.ainvoke(state)
            
            if isinstance(result, dict):
                # Convert dict back to state object
                final_state = ProductionOrchestratorState(**result)
            else:
                final_state = result
            
            # Save conversation history
            self._save_conversation_history(session_id, final_state.conversation_messages)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error processing conversation message: {e}")
            error_state = ProductionOrchestratorState(
                session_id=session_id,
                user_input=user_message,
                error_message=str(e),
                current_phase="error"
            )
            return error_state
    
    async def complete_qbr_workflow(self, session_id: str) -> ProductionOrchestratorState:
        """Complete the full QBR workflow after engagement is done."""
        try:
            # Load the completed engagement state
            state_file = self.data_dir / f"{session_id}_final_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                state = ProductionOrchestratorState(**state_data)
            else:
                raise Exception("No completed engagement state found")
            
            # Continue from information gathering
            state.current_phase = "information_gathering"
            result = await self.graph.ainvoke(state)
            
            if isinstance(result, dict):
                final_state = ProductionOrchestratorState(**result)
            else:
                final_state = result
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error completing QBR workflow: {e}")
            error_state = ProductionOrchestratorState(
                session_id=session_id,
                error_message=str(e),
                current_phase="error"
            )
            return error_state
    
    def _engagement_node(self, state: ProductionOrchestratorState) -> ProductionOrchestratorState:
        """Handle engagement phase with the real engagement agent."""
        try:
            logger.info(f"Processing engagement for session {state.session_id}")
            
            # Process the message with the real engagement agent
            response = self.engagement_agent.process_message(
                state.session_id, 
                state.user_input
            )
            
            # Add response to conversation history
            state.conversation_messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            state.engagement_response = response
            state.current_phase = "engagement"
            
            # Check if engagement is complete
            state.is_engagement_complete = self.engagement_agent.is_complete(state.session_id)
            
            if state.is_engagement_complete:
                # Get the final spec
                state.final_qbr_spec = self.engagement_agent.get_final_spec(state.session_id)
                logger.info(f"Engagement complete for session {state.session_id}")
                
                # Save the complete state
                self._save_final_state(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Engagement node error: {e}")
            state.error_message = str(e)
            state.current_phase = "error"
            return state
    
    def _information_gathering_node(self, state: ProductionOrchestratorState) -> ProductionOrchestratorState:
        """Handle information gathering with the real info gatherer."""
        try:
            logger.info(f"Starting information gathering for session {state.session_id}")
            
            if not state.final_qbr_spec:
                raise Exception("No QBR specification available for information gathering")
            
            # Set up output directory for this session
            session_output_dir = self.data_dir / state.session_id / "info_gathering"
            session_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set environment variable for output location
            os.environ["QBR_OUT"] = str(session_output_dir)
            
            # Run the information gatherer
            result = run_information_gatherer(state.final_qbr_spec)
            
            # Store the results
            state.info_gathering_complete = True
            state.current_phase = "information_gathering_complete"
            
            # Look for generated files
            spec_file = session_output_dir / "spec.json"
            manifest_file = session_output_dir / "tables_manifest.json" 
            mappings_file = session_output_dir / "mappings.json"
            
            if spec_file.exists():
                with open(spec_file, 'r') as f:
                    # Re-load the spec (might be enriched)
                    state.final_qbr_spec = json.load(f)
            
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    state.tables_manifest = json.load(f)
            
            if mappings_file.exists():
                with open(mappings_file, 'r') as f:
                    state.mappings = json.load(f)
            
            logger.info(f"Information gathering complete for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Information gathering error: {e}")
            state.error_message = str(e)
            state.current_phase = "error"
            return state
    
    def _synthesis_node(self, state: ProductionOrchestratorState) -> ProductionOrchestratorState:
        """Handle synthesis with the real synthesis agent."""
        try:
            logger.info(f"Starting synthesis for session {state.session_id}")
            
            if not state.final_qbr_spec:
                raise Exception("No QBR specification available for synthesis")
            
            # Create synthesis agent
            synthesis_agent = SynthesisAgentFactory.create_test_agent(data_mode="local")
            
            # Generate presentation
            result = synthesis_agent.generate_presentation(
                spec=state.final_qbr_spec,
                tables_manifest=state.tables_manifest or [],
                mappings=state.mappings or {}
            )
            
            state.presentation_result = result
            state.synthesis_complete = True
            state.current_phase = "complete"
            
            if result.get('status') == 'success':
                state.presentation_path = result.get('presentation_path')
                logger.info(f"Synthesis complete for session {state.session_id}")
            else:
                raise Exception(f"Synthesis failed: {result.get('error', 'Unknown error')}")
            
            return state
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            state.error_message = str(e)
            state.current_phase = "error"
            return state
    
    def _error_handler_node(self, state: ProductionOrchestratorState) -> ProductionOrchestratorState:
        """Handle errors and determine retry strategy."""
        state.retry_count += 1
        logger.warning(f"Error handler: {state.error_message} (retry {state.retry_count})")
        
        if state.retry_count >= 3:
            state.current_phase = "failed"
            logger.error(f"Max retries reached for session {state.session_id}")
        
        return state
    
    # Conditional edge functions
    def _should_continue_from_engagement(self, state: ProductionOrchestratorState) -> str:
        if state.error_message:
            return "error"
        elif state.is_engagement_complete:
            return "continue"
        else:
            return "stay"
    
    def _should_continue_from_info_gathering(self, state: ProductionOrchestratorState) -> str:
        if state.error_message:
            return "error"
        else:
            return "continue"
    
    def _should_continue_from_synthesis(self, state: ProductionOrchestratorState) -> str:
        if state.error_message:
            return "error"
        else:
            return "complete"
    
    def _should_retry(self, state: ProductionOrchestratorState) -> str:
        if state.retry_count >= 3:
            return "end"
        elif state.current_phase == "engagement":
            return "retry_engagement"
        elif state.current_phase == "information_gathering":
            return "retry_info_gathering"
        elif state.current_phase == "synthesis":
            return "retry_synthesis"
        else:
            return "end"
    
    # Helper methods
    def _load_conversation_history(self, session_id: str) -> list:
        """Load conversation history from disk."""
        history_file = self.data_dir / f"{session_id}_conversation.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_conversation_history(self, session_id: str, messages: list):
        """Save conversation history to disk."""
        history_file = self.data_dir / f"{session_id}_conversation.json"
        with open(history_file, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def _save_final_state(self, state: ProductionOrchestratorState):
        """Save the final state for later workflow completion."""
        state_file = self.data_dir / f"{state.session_id}_final_state.json"
        with open(state_file, 'w') as f:
            json.dump(state.dict(), f, indent=2)
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a session."""
        try:
            # Check if there's a conversation history
            history_file = self.data_dir / f"{session_id}_conversation.json"
            if not history_file.exists():
                return {"status": "new", "phase": "not_started"}
            
            # Check engagement completion
            if self.engagement_agent.is_complete(session_id):
                # Check if full workflow was completed
                state_file = self.data_dir / f"{session_id}_final_state.json"
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)
                    return {
                        "status": "engagement_complete",
                        "phase": state_data.get("current_phase", "engagement"),
                        "can_proceed": True
                    }
                else:
                    return {
                        "status": "engagement_complete", 
                        "phase": "engagement",
                        "can_proceed": True
                    }
            else:
                return {
                    "status": "in_progress",
                    "phase": "engagement", 
                    "completion_pct": self.engagement_agent.get_completion_percentage(session_id)
                }
                
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return {"status": "error", "error": str(e)}
