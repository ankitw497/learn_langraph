"""
Simplified File-Based Orchestrator for QBR Agents.
Works with file system: engagement_output -> infoagent_output -> synthesis_output
"""
import asyncio
import json
import logging
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from pydantic import BaseModel, Field

# Import your real agents
try:
    from engagement.agent import QBREngagementAgentSync
    from setput_info_gatherer import run_information_gatherer, CONFIG as INFO_GATHERER_CONFIG
    from synthesis.synthesis_agent import SynthesisAgentFactory
except ImportError as e:
    logging.warning(f"Could not import real agents: {e}. Using mock mode.")
    
    # Mock agents for testing
    class QBREngagementAgentSync:
        def __init__(self):
            self.sessions = {}
            
        def process_message(self, session_id, message):
            if session_id not in self.sessions:
                self.sessions[session_id] = {"messages": [], "complete": False}
            self.sessions[session_id]["messages"].append(message)
            if len(self.sessions[session_id]["messages"]) >= 3:
                self.sessions[session_id]["complete"] = True
                return {"reply": "Mock engagement complete!", "spec_complete": True}
            return {"reply": f"Mock response {len(self.sessions[session_id]['messages'])}"}
            
        def is_complete(self, session_id):
            return self.sessions.get(session_id, {}).get("complete", False)
            
        def get_final_spec(self, session_id):
            return {"mock": "spec", "session_id": session_id}
            
        def get_completion_percentage(self, session_id):
            msg_count = len(self.sessions.get(session_id, {}).get("messages", []))
            return min(msg_count * 33.33, 100.0)
            
        def get_frustration_index(self, session_id):
            return 0.0
    
    def run_information_gatherer(config):
        return [{"status": "mock_success", "filename": "mock_file.json"}]
    
    INFO_GATHERER_CONFIG = {"OUTPUT_DIR": "infoagent_output"}
    
    class SynthesisAgentFactory:
        @staticmethod
        def create_test_agent(data_mode="local"):
            class MockSynthesis:
                def generate_presentation(self, spec, tables_manifest=None, mappings=None):
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


class FileBasedOrchestratorState(BaseModel):
    """State object for file-based orchestrator."""
    session_id: str
    user_input: str = ""
    conversation_messages: list = Field(default_factory=list)
    
    # Engagement phase
    engagement_response: str = ""
    is_engagement_complete: bool = False
    final_qbr_spec: Optional[Dict[str, Any]] = None
    engagement_output_files: list = Field(default_factory=list)
    
    # Information gathering phase
    info_gathering_complete: bool = False
    info_gatherer_output_files: list = Field(default_factory=list)
    
    # Synthesis phase
    synthesis_complete: bool = False
    synthesis_output_files: list = Field(default_factory=list)
    presentation_result: Optional[Dict[str, Any]] = None
    
    # Status tracking
    current_phase: str = "engagement"
    error_message: Optional[str] = None
    completion_percentage: float = 0.0
    
    # File tracking
    session_folder: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class FileBasedQBROrchestrator:
    """File-based orchestrator that works with existing folder structure."""
    
    def __init__(self):
        """Initialize the orchestrator with real agents and folder structure."""
        try:
            self.engagement_agent = QBREngagementAgentSync()
            logger.info("Real engagement agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize engagement agent: {e}")
            raise
        
        # Define folder paths (at root level)
        self.root_dir = Path(".")
        self.engagement_output_dir = self.root_dir / "engagement_output"
        self.infoagent_output_dir = self.root_dir / "infoagent_output"
        self.synthesis_output_dir = self.root_dir / "synthesis_output"
        self.session_data_dir = self.root_dir / "session_data"
        
        # Create directories if they don't exist
        for dir_path in [self.engagement_output_dir, self.infoagent_output_dir, 
                        self.synthesis_output_dir, self.session_data_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Track session states in memory
        self._session_states = {}
        
        logger.info("File-based QBR Orchestrator initialized successfully")
        logger.info(f"Engagement output: {self.engagement_output_dir}")
        logger.info(f"Info gatherer output: {self.infoagent_output_dir}")
        logger.info(f"Synthesis output: {self.synthesis_output_dir}")
        logger.info(f"Session data: {self.session_data_dir}")
    
    async def process_conversation_message(self, session_id: str, user_message: str) -> FileBasedOrchestratorState:
        """Process a single conversation message through the engagement agent."""
        try:
            logger.info(f"Processing message for session {session_id}")
            
            # Load or create session state
            if session_id in self._session_states:
                state = self._session_states[session_id]
                logger.info(f"Loaded existing session state with {len(state.conversation_messages)} messages")
            else:
                state = FileBasedOrchestratorState(
                    session_id=session_id,
                    conversation_messages=[],
                    session_folder=str(self.session_data_dir / session_id)
                )
                # Create session folder
                session_folder = Path(state.session_folder)
                session_folder.mkdir(exist_ok=True)
                logger.info(f"Created new session state for {session_id}")
                self._session_states[session_id] = state
            
            # Update with current user input
            state.user_input = user_message
            
            # Add user message to conversation history
            user_msg = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            }
            state.conversation_messages.append(user_msg)
            
            # Process through engagement agent
            logger.info("Calling engagement agent...")
            response = self.engagement_agent.process_message(session_id, user_message)
            
            # Handle response format
            if isinstance(response, dict):
                reply_text = response.get("reply", str(response))
                spec_complete = response.get("spec_complete", False)
            else:
                reply_text = str(response)
                spec_complete = self.engagement_agent.is_complete(session_id)
            
            # Update state
            state.engagement_response = reply_text
            state.current_phase = "engagement"
            
            # Add assistant response to conversation
            assistant_msg = {
                "role": "assistant",
                "content": reply_text,
                "timestamp": datetime.now().isoformat()
            }
            state.conversation_messages.append(assistant_msg)
            
            # Check completion status
            if spec_complete or self.engagement_agent.is_complete(session_id):
                state.is_engagement_complete = True
                state.final_qbr_spec = self.engagement_agent.get_final_spec(session_id)
                state.completion_percentage = 33.0
                
                # Copy engagement output files to session folder
                await self._copy_engagement_files_to_session(state)
                
                logger.info(f"Engagement completed for session {session_id}")
            else:
                # Get completion percentage
                try:
                    pct = self.engagement_agent.get_completion_percentage(session_id)
                    state.completion_percentage = min(pct * 0.33, 32.0)
                except:
                    state.completion_percentage = 10.0
            
            # Save session state
            self._save_session_state(session_id, state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error processing conversation message: {e}")
            error_state = FileBasedOrchestratorState(
                session_id=session_id,
                user_input=user_message,
                error_message=str(e),
                current_phase="error"
            )
            self._session_states[session_id] = error_state
            return error_state
    
    async def complete_qbr_workflow(self, session_id: str) -> FileBasedOrchestratorState:
        """Complete the full QBR workflow: Information Gathering + Synthesis."""
        try:
            logger.info(f"Starting complete QBR workflow for session {session_id}")
            
            # Load session state
            if session_id not in self._session_states:
                raise Exception("No session state found. Complete engagement first.")
            
            state = self._session_states[session_id]
            
            if not state.is_engagement_complete:
                raise Exception("Engagement not complete. Cannot proceed to workflow.")
            
            # Step 1: Information Gathering
            logger.info("🔄 Step 1: Running Information Gatherer...")
            state.current_phase = "information_gathering"
            state.completion_percentage = 50.0
            
            # Run information gatherer with existing config
            try:
                info_config = INFO_GATHERER_CONFIG.copy()
                info_config["INPUT_JSONS_PATH"] = str(self.engagement_output_dir)
                info_config["OUTPUT_DIR"] = str(self.infoagent_output_dir)
                
                results = run_information_gatherer(info_config)
                logger.info(f"Information gatherer completed with {len(results)} results")
                
                state.info_gathering_complete = True
                state.completion_percentage = 66.0
                
                # Copy info gatherer output files to session folder
                await self._copy_info_gatherer_files_to_session(state)
                
            except Exception as e:
                logger.error(f"Information gathering failed: {e}")
                state.error_message = f"Information gathering failed: {str(e)}"
                return state
            
            # Step 2: Synthesis
            logger.info("🔄 Step 2: Running Synthesis Agent...")
            state.current_phase = "synthesis"
            state.completion_percentage = 80.0
            
            try:
                # Create synthesis agent
                synthesis_agent = SynthesisAgentFactory.create_test_agent(data_mode="local")
                
                # Prepare synthesis inputs
                spec = state.final_qbr_spec
                tables_manifest = self._load_json_file(self.infoagent_output_dir / "tables_manifest.json") or []
                mappings = self._load_json_file(self.infoagent_output_dir / "mappings.json") or {}
                
                # Generate presentation
                result = synthesis_agent.generate_presentation(
                    spec=spec,
                    tables_manifest=tables_manifest,
                    mappings=mappings
                )
                
                state.presentation_result = result
                state.synthesis_complete = True
                state.completion_percentage = 100.0
                
                # Copy synthesis output files to session folder
                await self._copy_synthesis_files_to_session(state)
                
                logger.info(f"Synthesis completed successfully for session {session_id}")
                
            except Exception as e:
                logger.error(f"Synthesis failed: {e}")
                state.error_message = f"Synthesis failed: {str(e)}"
                return state
            
            # Complete
            state.current_phase = "complete"
            self._save_session_state(session_id, state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error completing QBR workflow: {e}")
            state = self._session_states.get(session_id, FileBasedOrchestratorState(session_id=session_id))
            state.error_message = str(e)
            state.current_phase = "error"
            return state
    
    async def _copy_engagement_files_to_session(self, state: FileBasedOrchestratorState):
        """Copy engagement output files to session folder."""
        try:
            session_folder = Path(state.session_folder)
            engagement_session_folder = session_folder / "engagement_output"
            engagement_session_folder.mkdir(exist_ok=True)
            
            # Copy all files from engagement_output
            copied_files = []
            for file_path in self.engagement_output_dir.glob("*"):
                if file_path.is_file():
                    dest_path = engagement_session_folder / file_path.name
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(str(dest_path))
                    logger.info(f"Copied engagement file: {file_path.name}")
            
            state.engagement_output_files = copied_files
            logger.info(f"Copied {len(copied_files)} engagement files to session {state.session_id}")
            
        except Exception as e:
            logger.error(f"Error copying engagement files: {e}")
    
    async def _copy_info_gatherer_files_to_session(self, state: FileBasedOrchestratorState):
        """Copy info gatherer output files to session folder."""
        try:
            session_folder = Path(state.session_folder)
            info_session_folder = session_folder / "infoagent_output"
            info_session_folder.mkdir(exist_ok=True)
            
            # Copy all files from infoagent_output
            copied_files = []
            for file_path in self.infoagent_output_dir.glob("*"):
                if file_path.is_file():
                    dest_path = info_session_folder / file_path.name
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(str(dest_path))
                    logger.info(f"Copied info gatherer file: {file_path.name}")
            
            state.info_gatherer_output_files = copied_files
            logger.info(f"Copied {len(copied_files)} info gatherer files to session {state.session_id}")
            
        except Exception as e:
            logger.error(f"Error copying info gatherer files: {e}")
    
    async def _copy_synthesis_files_to_session(self, state: FileBasedOrchestratorState):
        """Copy synthesis output files to session folder."""
        try:
            session_folder = Path(state.session_folder)
            synthesis_session_folder = session_folder / "synthesis_output"
            synthesis_session_folder.mkdir(exist_ok=True)
            
            # Copy all files from synthesis_output
            copied_files = []
            for file_path in self.synthesis_output_dir.glob("*"):
                if file_path.is_file():
                    dest_path = synthesis_session_folder / file_path.name
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(str(dest_path))
                    logger.info(f"Copied synthesis file: {file_path.name}")
            
            state.synthesis_output_files = copied_files
            logger.info(f"Copied {len(copied_files)} synthesis files to session {state.session_id}")
            
        except Exception as e:
            logger.error(f"Error copying synthesis files: {e}")
    
    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file safely."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load JSON file {file_path}: {e}")
        return None
    
    def _save_session_state(self, session_id: str, state: FileBasedOrchestratorState):
        """Save session state to file."""
        try:
            session_folder = Path(state.session_folder)
            state_file = session_folder / "session_state.json"
            with open(state_file, 'w') as f:
                json.dump(state.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save session state: {e}")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session status."""
        try:
            status = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            if session_id in self._session_states:
                state = self._session_states[session_id]
                status.update({
                    "current_phase": state.current_phase,
                    "completion_percentage": state.completion_percentage,
                    "message_count": len(state.conversation_messages),
                    "has_conversation": len(state.conversation_messages) > 0,
                    "session_folder": state.session_folder
                })
                
                # Engagement status
                status["engagement"] = {
                    "is_complete": state.is_engagement_complete,
                    "completion_percentage": self.engagement_agent.get_completion_percentage(session_id) if hasattr(self.engagement_agent, 'get_completion_percentage') else 0,
                    "output_files": len(state.engagement_output_files)
                }
                
                # Workflow status
                status["workflow"] = {
                    "current_phase": state.current_phase,
                    "info_gathering_complete": state.info_gathering_complete,
                    "synthesis_complete": state.synthesis_complete,
                    "has_presentation": state.presentation_result is not None,
                    "info_files": len(state.info_gatherer_output_files),
                    "synthesis_files": len(state.synthesis_output_files)
                }
            else:
                status.update({
                    "message_count": 0,
                    "has_conversation": False,
                    "current_phase": "not_started"
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return {"session_id": session_id, "error": str(e)}
    
    def cleanup_session(self, session_id: str):
        """Clean up session data."""
        try:
            # Remove from memory
            if session_id in self._session_states:
                del self._session_states[session_id]
            
            # Remove session folder
            session_folder = self.session_data_dir / session_id
            if session_folder.exists():
                shutil.rmtree(session_folder)
            
            logger.info(f"Cleaned up session {session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
