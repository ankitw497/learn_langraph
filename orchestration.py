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
try:
    from engagement.agent import QBREngagementAgentSync
    from setup_info_gatherer import run_information_gatherer
    from synthesis.synthesis_agent import SynthesisAgentFactory
except ImportError as e:
    logging.warning(f"Could not import real agents: {e}. Using mock agents for testing.")
    # Fallback to mock agents if real ones aren't available
    class QBREngagementAgentSync:
        def __init__(self):
            self.sessions = {}
            
        def process_message(self, session_id, message):
            if session_id not in self.sessions:
                self.sessions[session_id] = {"messages": [], "complete": False}
            self.sessions[session_id]["messages"].append(message)
            if len(self.sessions[session_id]["messages"]) >= 3:
                self.sessions[session_id]["complete"] = True
                return "Mock engagement complete! I have all the information I need."
            return f"Mock engagement response {len(self.sessions[session_id]['messages'])}"
            
        def is_complete(self, session_id):
            return self.sessions.get(session_id, {}).get("complete", False)
            
        def get_final_spec(self, session_id):
            return {"mock": "spec", "session_id": session_id}
            
        def get_completion_percentage(self, session_id):
            msg_count = len(self.sessions.get(session_id, {}).get("messages", []))
            return min(msg_count * 33.33, 100.0)
    
    def run_information_gatherer(spec):
        return {"status": "mock_success"}
    
    class SynthesisAgentFactory:
        @staticmethod
        def create_test_agent(data_mode="local"):
            class MockSynthesis:
                def generate_presentation(self, spec, tables_manifest, mappings):
                    return {
                        "status": "success",
                        "presentation_path": "./mock_presentation.pptx",
                        "slides_count": 5,
                        "insights_count": 3
                    }
            return MockSynthesis()

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
    completion_percentage: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True


class ProductionQBROrchestrator:
    """Production orchestrator for real QBR agents with proper session management."""
    
    def __init__(self):
        """Initialize the orchestrator with real agents."""
        try:
            self.engagement_agent = QBREngagementAgentSync()
            logger.info("Real engagement agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize engagement agent: {e}")
            raise
        
        # Create data directories
        self.data_dir = Path("./session_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Simple conversation graph for engagement only
        self.conversation_graph = self._build_conversation_graph()
        
        # Track session states in memory for faster access
        self._session_states = {}
        
        logger.info("Production QBR Orchestrator initialized successfully")
    
    def _build_conversation_graph(self) -> CompiledStateGraph:
        """Build a simple graph for engagement conversations only."""
        workflow = StateGraph(ProductionOrchestratorState)
        
        # Single node for engagement
        workflow.add_node("engagement", self._engagement_node)
        
        # Simple linear flow
        workflow.add_edge(START, "engagement")
        workflow.add_edge("engagement", END)
        
        return workflow.compile()
    
    async def process_conversation_message(self, session_id: str, user_message: str) -> ProductionOrchestratorState:
        """Process a single conversation message through the engagement agent."""
        try:
            logger.info(f"Processing message for session {session_id}")
            
            # 🔧 FIX: Load existing session state instead of creating new one
            if session_id in self._session_states:
                state = self._session_states[session_id]
                logger.info(f"Loaded existing session state with {len(state.conversation_messages)} messages")
            else:
                # Load from disk if available
                state = self._load_session_state(session_id)
                if state is None:
                    # Create new state only if none exists
                    state = ProductionOrchestratorState(
                        session_id=session_id,
                        conversation_messages=[]
                    )
                    logger.info(f"Created new session state for {session_id}")
                else:
                    logger.info(f"Loaded session state from disk with {len(state.conversation_messages)} messages")
                
                # Cache in memory
                self._session_states[session_id] = state
            
            # Update with current user input
            state.user_input = user_message
            
            # Add user message to conversation history
            state.conversation_messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Process through engagement graph
            result = await self.conversation_graph.ainvoke(state)
            
            # Handle result format (LangGraph can return dict or state object)
            if isinstance(result, dict):
                final_state = ProductionOrchestratorState(**result)
            else:
                final_state = result
            
            # 🔧 FIX: Update cached state and save to disk
            self._session_states[session_id] = final_state
            self._save_session_state(session_id, final_state)
            
            # Save conversation history separately for backup
            self._save_conversation_history(session_id, final_state.conversation_messages)
            
            # Save engagement state if complete
            if final_state.is_engagement_complete:
                self._save_engagement_state(session_id, final_state)
                logger.info(f"Engagement complete for session {session_id}")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error processing conversation message: {e}")
            error_state = ProductionOrchestratorState(
                session_id=session_id,
                user_input=user_message,
                error_message=str(e),
                current_phase="error"
            )
            # Save error state too
            self._session_states[session_id] = error_state
            return error_state
    
    async def complete_qbr_workflow(self, session_id: str) -> ProductionOrchestratorState:
        """Complete the full QBR workflow: Information Gathering + Synthesis."""
        try:
            logger.info(f"Starting complete QBR workflow for session {session_id}")
            
            # 🔧 FIX: Load state from memory first, then disk
            if session_id in self._session_states:
                state = self._session_states[session_id]
            else:
                state = self._load_engagement_state(session_id)
                if state:
                    self._session_states[session_id] = state
            
            if not state:
                raise Exception("No completed engagement state found. Complete engagement first.")
            
            if not state.final_qbr_spec:
                raise Exception("No QBR specification available. Engagement may not be complete.")
            
            # Step 1: Information Gathering
            logger.info("Executing information gathering phase...")
            state.current_phase = "information_gathering"
            state.completion_percentage = 50.0
            
            state = self._information_gathering_node(state)
            
            if state.error_message:
                logger.error(f"Information gathering failed: {state.error_message}")
                self._session_states[session_id] = state
                return state
            
            # Step 2: Synthesis
            logger.info("Executing synthesis phase...")
            state.current_phase = "synthesis"
            state.completion_percentage = 80.0
            
            state = self._synthesis_node(state)
            
            if state.error_message:
                logger.error(f"Synthesis failed: {state.error_message}")
                self._session_states[session_id] = state
                return state
            
            # Complete
            state.current_phase = "complete"
            state.completion_percentage = 100.0
            
            # Save final state
            self._session_states[session_id] = state
            self._save_final_state(session_id, state)
            
            logger.info(f"QBR workflow completed successfully for session {session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error completing QBR workflow: {e}")
            error_state = ProductionOrchestratorState(
                session_id=session_id,
                error_message=str(e),
                current_phase="error",
                completion_percentage=0.0
            )
            self._session_states[session_id] = error_state
            return error_state
    
    def _engagement_node(self, state: ProductionOrchestratorState) -> ProductionOrchestratorState:
        """Handle engagement phase with the real engagement agent."""
        try:
            logger.info(f"Processing engagement for session {state.session_id}")
            
            # 🔧 FIX: The engagement agent maintains its own session memory
            # We just need to call it with the same session_id consistently
            response = self.engagement_agent.process_message(
                state.session_id,
                state.user_input
            )
            
            # Update state
            state.engagement_response = response
            state.current_phase = "engagement"
            
            # Add response to conversation
            state.conversation_messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check completion status from the agent
            state.is_engagement_complete = self.engagement_agent.is_complete(state.session_id)
            
            if state.is_engagement_complete:
                # Get final specification
                state.final_qbr_spec = self.engagement_agent.get_final_spec(state.session_id)
                state.completion_percentage = 33.0
                logger.info(f"Engagement completed for session {state.session_id}")
            else:
                # Get completion percentage
                try:
                    pct = self.engagement_agent.get_completion_percentage(state.session_id)
                    state.completion_percentage = min(pct * 0.33, 32.0)  # Cap at 32% until complete
                except Exception as e:
                    logger.warning(f"Could not get completion percentage: {e}")
                    state.completion_percentage = 10.0  # Default partial completion
            
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
            
            # Create session-specific output directory
            session_output_dir = self.data_dir / state.session_id / "info_gathering"
            session_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set environment variable for output location
            original_qbr_out = os.environ.get("QBR_OUT")
            os.environ["QBR_OUT"] = str(session_output_dir)
            
            try:
                # Run the real information gatherer
                result = run_information_gatherer(state.final_qbr_spec)
                logger.info(f"Information gatherer result: {result}")
                
            finally:
                # Restore original environment
                if original_qbr_out:
                    os.environ["QBR_OUT"] = original_qbr_out
                elif "QBR_OUT" in os.environ:
                    del os.environ["QBR_OUT"]
            
            # Update state
            state.info_gathering_complete = True
            state.enriched_data_path = str(session_output_dir)
            
            # Load generated files if they exist
            spec_file = session_output_dir / "spec.json"
            manifest_file = session_output_dir / "tables_manifest.json"
            mappings_file = session_output_dir / "mappings.json"
            
            if spec_file.exists():
                with open(spec_file, 'r') as f:
                    enriched_spec = json.load(f)
                    # Update with enriched spec
                    state.final_qbr_spec.update(enriched_spec)
                    logger.info("Loaded enriched specification")
            
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    state.tables_manifest = json.load(f)
                    logger.info(f"Loaded tables manifest with {len(state.tables_manifest)} tables")
            
            if mappings_file.exists():
                with open(mappings_file, 'r') as f:
                    state.mappings = json.load(f)
                    logger.info(f"Loaded mappings with {len(state.mappings)} entries")
            
            logger.info(f"Information gathering completed for session {state.session_id}")
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
            
            # Prepare parameters
            spec = state.final_qbr_spec
            tables_manifest = state.tables_manifest or []
            mappings = state.mappings or {}
            
            logger.info(f"Generating presentation with {len(tables_manifest)} tables and {len(mappings)} mappings")
            
            # Generate presentation
            result = synthesis_agent.generate_presentation(
                spec=spec,
                tables_manifest=tables_manifest,
                mappings=mappings
            )
            
            # Update state
            state.presentation_result = result
            state.synthesis_complete = True
            
            if result.get('status') == 'success':
                state.presentation_path = result.get('presentation_path')
                logger.info(f"Synthesis completed successfully. Presentation: {state.presentation_path}")
            else:
                error_msg = result.get('error', 'Unknown synthesis error')
                logger.error(f"Synthesis failed: {error_msg}")
                raise Exception(error_msg)
            
            return state
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            state.error_message = str(e)
            state.current_phase = "error"
            return state
    
    # 🔧 FIX: Enhanced state management methods
    def _load_session_state(self, session_id: str) -> Optional[ProductionOrchestratorState]:
        """Load complete session state from disk."""
        try:
            state_file = self.data_dir / f"{session_id}_session_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                return ProductionOrchestratorState(**state_data)
        except Exception as e:
            logger.warning(f"Could not load session state: {e}")
        return None
    
    def _save_session_state(self, session_id: str, state: ProductionOrchestratorState):
        """Save complete session state to disk."""
        try:
            state_file = self.data_dir / f"{session_id}_session_state.json"
            with open(state_file, 'w') as f:
                json.dump(state.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save session state: {e}")
    
    def _load_conversation_history(self, session_id: str) -> list:
        """Load conversation history from disk."""
        try:
            history_file = self.data_dir / f"{session_id}_conversation.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load conversation history: {e}")
        return []
    
    def _save_conversation_history(self, session_id: str, messages: list):
        """Save conversation history to disk."""
        try:
            history_file = self.data_dir / f"{session_id}_conversation.json"
            with open(history_file, 'w') as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save conversation history: {e}")
    
    def _load_engagement_state(self, session_id: str) -> Optional[ProductionOrchestratorState]:
        """Load completed engagement state."""
        try:
            state_file = self.data_dir / f"{session_id}_engagement_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                return ProductionOrchestratorState(**state_data)
        except Exception as e:
            logger.error(f"Could not load engagement state: {e}")
        return None
    
    def _save_engagement_state(self, session_id: str, state: ProductionOrchestratorState):
        """Save completed engagement state."""
        try:
            state_file = self.data_dir / f"{session_id}_engagement_state.json"
            with open(state_file, 'w') as f:
                json.dump(state.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save engagement state: {e}")
    
    def _save_final_state(self, session_id: str, state: ProductionOrchestratorState):
        """Save final workflow state."""
        try:
            state_file = self.data_dir / f"{session_id}_final_state.json"
            with open(state_file, 'w') as f:
                json.dump(state.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save final state: {e}")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session status."""
        try:
            status = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 🔧 FIX: Check memory cache first
            if session_id in self._session_states:
                state = self._session_states[session_id]
                status["message_count"] = len(state.conversation_messages)
                status["has_conversation"] = len(state.conversation_messages) > 0
                status["current_phase"] = state.current_phase
                status["completion_percentage"] = state.completion_percentage
            else:
                # Fallback to disk
                history = self._load_conversation_history(session_id)
                status["message_count"] = len(history)
                status["has_conversation"] = len(history) > 0
            
            # Check engagement status with the agent directly
            try:
                is_complete = self.engagement_agent.is_complete(session_id)
                completion_pct = self.engagement_agent.get_completion_percentage(session_id)
                
                status["engagement"] = {
                    "is_complete": is_complete,
                    "completion_percentage": completion_pct
                }
                
                if is_complete:
                    spec = self.engagement_agent.get_final_spec(session_id)
                    status["engagement"]["has_spec"] = spec is not None
                    status["can_proceed_to_workflow"] = True
                else:
                    status["can_proceed_to_workflow"] = False
                    
            except Exception as e:
                status["engagement"] = {"error": str(e)}
                status["can_proceed_to_workflow"] = False
            
            # Check workflow completion from cached state
            if session_id in self._session_states:
                state = self._session_states[session_id]
                status["workflow"] = {
                    "current_phase": state.current_phase,
                    "completion_percentage": state.completion_percentage,
                    "info_gathering_complete": state.info_gathering_complete,
                    "synthesis_complete": state.synthesis_complete,
                    "has_presentation": state.presentation_path is not None
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_session(self, session_id: str):
        """Clean up session data."""
        try:
            # Remove from memory cache
            if session_id in self._session_states:
                del self._session_states[session_id]
            
            # Remove session files
            files_to_remove = [
                f"{session_id}_conversation.json",
                f"{session_id}_engagement_state.json", 
                f"{session_id}_final_state.json",
                f"{session_id}_session_state.json"
            ]
            
            for filename in files_to_remove:
                file_path = self.data_dir / filename
                if file_path.exists():
                    file_path.unlink()
            
            # Remove session directory
            session_dir = self.data_dir / session_id
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
            
            logger.info(f"Cleaned up session {session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
