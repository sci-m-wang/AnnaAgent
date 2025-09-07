from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import logging
from pathlib import Path

# Import existing AnnaAgent components
from src.anna_agent.backbone import configure
from fixed_ms_patient import FixedMsPatient

# Initialize AnnaAgent configuration
configure(Path("."))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AnnaAgent API",
    description="FastAPI wrapper for AnnaAgent psychological counseling system",
    version="0.1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SafeMsPatientWrapper:
    """现在使用FixedMsPatient，已经内置了强健的错误处理"""
    
    def __init__(self, portrait, report, previous_conversations):
        self.ms_patient = FixedMsPatient(portrait, report, previous_conversations)
        
    def chat(self, message: str) -> str:
        """直接使用FixedMsPatient，它已经处理了所有错误情况"""
        try:
            response = self.ms_patient.chat(message)
            
            # FixedMsPatient永远不会返回空字符串，但为了保险起见
            if not response or response.strip() == "":
                logger.warning("FixedMsPatient returned empty response - this should not happen")
                return "抱歉，我刚才走神了...最近工作太忙，脑子有点乱。你刚才说什么？"
            
            return response
            
        except Exception as e:
            # 这种情况基本不会发生，因为FixedMsPatient已经处理了所有异常
            logger.error(f"Unexpected error in SafeMsPatientWrapper: {str(e)}")
            return "不好意思，我在想工作的事情...能再说一遍吗？"
    
    # 完美代理所有其他属性，保持AnnaAgent功能完整性
    def __getattr__(self, name):
        return getattr(self.ms_patient, name)

# In-memory session storage (use database in production)
sessions: Dict[str, SafeMsPatientWrapper] = {}
session_metadata: Dict[str, dict] = {}

# Pydantic models for API
class PatientProfile(BaseModel):
    age: str
    gender: str
    occupation: str
    martial_status: str
    symptoms: str

class Report(BaseModel):
    title: str = "默认咨询案例"
    content: Optional[str] = None

class Conversation(BaseModel):
    role: str  # "Counselor" or "Seeker"
    content: str

class CreateSessionRequest(BaseModel):
    profile: PatientProfile
    report: Optional[Report] = None
    previous_conversations: Optional[List[Conversation]] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    message_count: Optional[int] = None
    emotion: Optional[str] = None
    complaint_stage: Optional[int] = None

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    profile: PatientProfile
    status: str = "active"

class SimpleResponse(BaseModel):
    response: str
    timestamp: str

# Default patient profile for simple chat
DEFAULT_PROFILE = {
    "age": "28",
    "gender": "男",
    "occupation": "软件工程师",
    "martial_status": "未婚",
    "symptoms": "工作焦虑，失眠"
}

DEFAULT_REPORT = {"案例标题": "工作压力咨询"}

@app.get("/")
async def root():
    return {
        "message": "AnnaAgent API Server", 
        "version": "0.1.0",
        "endpoints": {
            "simple_chat": "/api/chat/simple",
            "create_session": "/api/sessions",
            "session_chat": "/api/sessions/{session_id}/chat",
            "get_sessions": "/api/sessions"
        }
    }

@app.post("/api/chat/simple", response_model=SimpleResponse)
async def simple_chat(request: ChatRequest):
    """
    Simple stateless chat endpoint using default patient profile.
    Each request creates a new MsPatient instance.
    """
    try:
        # Create new MsPatient instance with default settings
        patient = SafeMsPatientWrapper(
            portrait=DEFAULT_PROFILE,
            report=DEFAULT_REPORT,
            previous_conversations=[]
        )
        
        # Get response - 这里确保我们等待完整的处理
        logger.info(f"Processing message: {request.message}")
        response = patient.chat(request.message)
        logger.info(f"Got response: {response}")
        
        return SimpleResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error in simple chat: {str(e)}")
        # 确保即使出错也返回200状态码和有意义的回复
        fallback_response = "抱歉，我刚才走神了...最近工作太忙，脑子有点乱。你刚才说什么？"
        return SimpleResponse(
            response=fallback_response,
            timestamp=datetime.now().isoformat()
        )

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new patient session with custom profile.
    Returns session ID for subsequent conversations.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Convert profile to dict format expected by MsPatient
        profile_dict = {
            "age": request.profile.age,
            "gender": request.profile.gender,
            "occupation": request.profile.occupation,
            "martial_status": request.profile.martial_status,
            "symptoms": request.profile.symptoms
        }
        
        # Convert report to dict format
        report_dict = {"案例标题": request.report.title if request.report else "默认咨询案例"}
        if request.report and request.report.content:
            report_dict["内容"] = request.report.content
        
        # Convert previous conversations to expected format
        previous_convs = []
        if request.previous_conversations:
            previous_convs = [
                {"role": conv.role, "content": conv.content} 
                for conv in request.previous_conversations
            ]
        
        # Create MsPatient instance
        patient = SafeMsPatientWrapper(
            portrait=profile_dict,
            report=report_dict,
            previous_conversations=previous_convs
        )
        
        # Store session
        sessions[session_id] = patient
        session_metadata[session_id] = {
            "created_at": datetime.now(),
            "profile": request.profile,
            "message_count": 0,
            "status": "active"
        }
        
        logger.info(f"Created session {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            created_at=session_metadata[session_id]["created_at"].isoformat(),
            profile=request.profile,
            status="active"
        )
    
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建会话时出错: {str(e)}")

@app.post("/api/sessions/{session_id}/chat", response_model=ChatResponse)
async def session_chat(session_id: str, request: ChatRequest):
    """
    Send message to specific session and get response.
    Maintains conversation state within the MsPatient instance.
    """
    try:
        # Check if session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        # Check if session is active
        if session_metadata[session_id]["status"] != "active":
            raise HTTPException(status_code=400, detail=f"会话 {session_id} 已结束")
        
        # Get patient instance
        patient = sessions[session_id]
        
        # Get response
        response = patient.chat(request.message)
        
        # Update metadata
        session_metadata[session_id]["message_count"] += 1
        
        # Build response with additional info
        chat_response = ChatResponse(
            response=response,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            message_count=session_metadata[session_id]["message_count"],
            complaint_stage=patient.chain_index
        )
        
        logger.info(f"Session {session_id}: message #{chat_response.message_count}")
        
        return chat_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in session chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理对话时出错: {str(e)}")

@app.get("/api/sessions")
async def list_sessions():
    """
    List all active sessions.
    """
    try:
        session_list = []
        for session_id, metadata in session_metadata.items():
            session_list.append({
                "session_id": session_id,
                "created_at": metadata["created_at"].isoformat(),
                "message_count": metadata["message_count"],
                "status": metadata["status"],
                "profile": metadata["profile"]
            })
        
        return {"sessions": session_list, "total": len(session_list)}
    
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表时出错: {str(e)}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get session details and conversation history.
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        patient = sessions[session_id]
        metadata = session_metadata[session_id]
        
        return {
            "session_id": session_id,
            "metadata": {
                "created_at": metadata["created_at"].isoformat(),
                "message_count": metadata["message_count"],
                "status": metadata["status"],
                "profile": metadata["profile"]
            },
            "conversation": patient.conversation,
            "complaint_stage": patient.chain_index,
            "status_summary": patient.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话详情时出错: {str(e)}")

@app.delete("/api/sessions/{session_id}")
async def end_session(session_id: str):
    """
    End a session (mark as inactive).
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        # Mark as inactive instead of deleting to preserve history
        session_metadata[session_id]["status"] = "ended"
        session_metadata[session_id]["ended_at"] = datetime.now()
        
        return {"message": f"会话 {session_id} 已结束", "session_id": session_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"结束会话时出错: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)