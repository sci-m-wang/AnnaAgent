from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import logging
from pathlib import Path
import os

# Import existing AnnaAgent components
from src.anna_agent.backbone import configure
from src.anna_agent.fixed_ms_patient import FixedMsPatient
from src.anna_agent.dataset_loader import DatasetLoader
from src.anna_agent.complaint_chain import gen_complaint_chain

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

    def __init__(self, portrait, report, previous_conversations,chain,prompt):
        # 为缺省/空的 chain 提供安全默认
        safe_chain = chain if chain else gen_complaint_chain(portrait)
        # prompt 允许为空字符串，不阻断
        safe_prompt = prompt if (prompt is not None) else ""
        self.ms_patient = FixedMsPatient(
            portrait, report, previous_conversations, safe_chain, safe_prompt
        )

    def chat(self, message: str):
        """调用底层并始终返回 (response, emotion, complaint) 三元组。"""
        try:
            result = self.ms_patient.chat(message)
            if isinstance(result, tuple) and len(result) == 3:
                response, emotion, complaint = result
            elif isinstance(result, str):
                response, emotion, complaint = result, "neutral", "unknown"
            else:
                response, emotion, complaint = (
                    "抱歉，我刚才走神了...最近工作太忙，脑子有点乱。你刚才说什么？",
                    "neutral",
                    "unknown",
                )

            if not response or (isinstance(response, str) and response.strip() == ""):
                logger.warning(
                    "FixedMsPatient returned empty response - this should not happen"
                )
                return (
                    "抱歉，我刚才走神了...最近工作太忙，脑子有点乱。你刚才说什么？",
                    emotion or "neutral",
                    complaint or "unknown",
                )

            return response, emotion, complaint

        except Exception as e:
            logger.error(f"Unexpected error in SafeMsPatientWrapper: {str(e)}")
            return (
                "不好意思，我在想工作的事情...能再说一遍吗？",
                "neutral",
                "unknown",
            )

    # 完美代理所有其他属性，保持AnnaAgent功能完整性
    def __getattr__(self, name):
        return getattr(self.ms_patient, name)

# In-memory session storage (use database in production)
sessions: Dict[str, SafeMsPatientWrapper] = {}
session_metadata: Dict[str, dict] = {}

# Dataset loader (with mtime-based hot reload)
DATASET_PATH = Path(os.getenv("MERGED_DATA_PATH", "ref/merged_data.json"))
dataset_loader = DatasetLoader(DATASET_PATH)

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
    id: str
    conversation: Optional[List[Conversation]] = None
    report: Optional[Report] = None
    portrait: PatientProfile
    seeker_prompt: Optional[str] = None
    chain: Optional[List[str]] = None

class CreateSessionByIdRequest(BaseModel):
    patient_id: str

class CreateSessionRequest(BaseModel):
    profile: PatientProfile
    report: Optional[Dict[str, Any]] = None
    previous_conversations: Optional[List[Dict[str, str]]] = None
    seeker_prompt: Optional[str] = None
    chain: Optional[List[str]] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    emotion: str
    complaint: str
    session_id: str
    timestamp: str
    message_count: Optional[int] = None
    complaint_stage: Optional[int] = None

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    profile: PatientProfile
    status: str = "active"

class SimpleResponse(BaseModel):
    response: str
    emotion: str
    complaint: str
    timestamp: str

class PatientSummary(BaseModel):
    id: str
    name: str
    age: str
    gender: str
    occupation: str
    symptoms: List[str]
    case_title: str
    difficulty: str = "中级"
    description: str

class PatientDetail(BaseModel):
    id: str
    profile: PatientProfile
    report: Dict[str, Any]
    conversation_preview: List[Dict[str, str]]
    seeker_prompt: Optional[str] = None
    chain: List[Dict[str, Any]]
    total_messages: int

class PatientListResponse(BaseModel):
    patients: List[PatientSummary]
    total: int
    page: int
    page_size: int

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
            "patients_list": "/api/patients",
            "patient_detail": "/api/patients/{patient_id}", 
            "create_session": "/api/sessions",
            "create_session_by_id": "/api/sessions/by_id",
            "session_chat": "/api/sessions/{session_id}/chat",
            "get_sessions": "/api/sessions",
            "get_session_detail": "/api/sessions/{session_id}",
            "end_session": "/api/sessions/{session_id}",
            "list_patient_ids": "/api/patients/ids"
        }
    }

@app.get("/api/patients", response_model=PatientListResponse)
async def get_patients(page: int = 1, page_size: int = 10, random_order: bool = False):
    """
    获取病人列表，支持分页和随机排序
    """
    try:
        ids = dataset_loader.list_ids()
        total = len(ids)
        
        # 如果需要随机排序
        if random_order:
            import random
            ids = random.sample(ids, len(ids))
        
        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_ids = ids[start_idx:end_idx]
        
        patients = []
        for patient_id in page_ids:
            try:
                record = dataset_loader.get_by_id(patient_id)
                portrait, report, conversation, _, chain = dataset_loader.try_map_to_components(record)
                
                # 解析症状列表
                symptoms_str = portrait.get("symptoms", "")
                symptoms = [s.strip() for s in symptoms_str.split(";") if s.strip()] if symptoms_str else []
                
                # 生成病人摘要
                case_title = report.get("案例标题", "心理咨询案例")
                
                # 根据症状和案例类型判断难度
                difficulty = "初级"
                if "抑郁" in symptoms_str or "焦虑" in symptoms_str:
                    difficulty = "中级"
                if "精神" in symptoms_str or "幻听" in symptoms_str or "双相" in symptoms_str:
                    difficulty = "高级"
                
                # 生成描述
                case_categories = report.get("案例类别", [])
                description = f"{portrait.get('age')}岁{portrait.get('gender')}性，{portrait.get('occupation')}，主要涉及{' '.join(case_categories[:2]) if case_categories else '心理健康'}问题"
                
                patient_summary = PatientSummary(
                    id=patient_id,
                    name=f"{portrait.get('gender')}性求助者",  # 保护隐私，不使用真实姓名
                    age=portrait.get("age", "28"),
                    gender=portrait.get("gender", "男"),
                    occupation=portrait.get("occupation", "未知"),
                    symptoms=symptoms,
                    case_title=case_title,
                    difficulty=difficulty,
                    description=description
                )
                patients.append(patient_summary)
            except Exception as e:
                logger.warning(f"Error processing patient {patient_id}: {str(e)}")
                continue
        
        return PatientListResponse(
            patients=patients,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error getting patients list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取病人列表时出错: {str(e)}")

@app.get("/api/patients/{patient_id}", response_model=PatientDetail)
async def get_patient_detail(patient_id: str):
    """
    获取指定病人的详细信息
    """
    try:
        record = dataset_loader.get_by_id(patient_id)
        portrait, report, conversation, seeker_prompt, chain = dataset_loader.try_map_to_components(record)
        
        # 处理对话预览（前几条消息）
        conversation_preview = conversation[:6] if conversation else []
        
        # 处理chain格式
        formatted_chain = []
        if isinstance(chain, list):
            for i, item in enumerate(chain):
                if isinstance(item, dict):
                    formatted_chain.append({
                        "stage": item.get("stage", i + 1),
                        "content": item.get("content", str(item))
                    })
                else:
                    formatted_chain.append({
                        "stage": i + 1,
                        "content": str(item)
                    })
        
        return PatientDetail(
            id=patient_id,
            profile=PatientProfile(**portrait),
            report=report,
            conversation_preview=conversation_preview,
            seeker_prompt=seeker_prompt,
            chain=formatted_chain,
            total_messages=len(conversation)
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"病人ID {patient_id} 不存在")
    except Exception as e:
        logger.error(f"Error getting patient detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取病人详情时出错: {str(e)}")

@app.get("/api/patients/ids")
async def list_patient_ids():
    """
    获取所有病人ID列表（向后兼容）
    """
    try:
        ids = dataset_loader.list_ids()
        return {"ids": ids, "count": len(ids)}
    except Exception as e:
        logger.error(f"Error listing patient ids: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取患者ID列表时出错: {str(e)}")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new patient session with custom profile (for frontend compatibility).
    Returns session ID for subsequent conversations.
    """
    try:
        session_id = str(uuid.uuid4())

        # Convert frontend profile to internal format
        portrait = {
            "age": request.profile.age,
            "gender": request.profile.gender,
            "occupation": request.profile.occupation,
            "martial_status": request.profile.martial_status,
            "symptoms": request.profile.symptoms
        }
        
        report = request.report or {"title": "自定义咨询案例"}
        previous_conversations = request.previous_conversations or []
        seeker_prompt = request.seeker_prompt or ""
        chain = request.chain or []

        # Create MsPatient instance
        patient = SafeMsPatientWrapper(
            portrait=portrait,
            report=report,
            previous_conversations=previous_conversations,
            chain=chain,
            prompt=seeker_prompt
        )

        # Store session
        sessions[session_id] = patient
        session_metadata[session_id] = {
            "created_at": datetime.now(),
            "profile": portrait,
            "message_count": 0,
            "status": "active"
        }

        logger.info(f"Created session {session_id} with custom profile")

        return SessionResponse(
            session_id=session_id,
            created_at=session_metadata[session_id]["created_at"].isoformat(),
            profile=PatientProfile(**portrait),
            status="active"
        )

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建会话时出错: {str(e)}")

@app.post("/api/sessions/by_id", response_model=SessionResponse)
async def create_session_by_id(request: CreateSessionByIdRequest):
    """
    Create a new patient session by loading from dataset by patient ID.
    Returns session ID for subsequent conversations.
    """
    try:
        session_id = str(uuid.uuid4())

        # Load from dataset by id
        try:
            record = dataset_loader.get_by_id(request.patient_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"未找到患者ID: {request.patient_id}")
        portrait, report, previous, seek_prompt, chain = dataset_loader.try_map_to_components(record)

        # Create MsPatient instance
        patient = SafeMsPatientWrapper(
            portrait=portrait,
            report=report,
            previous_conversations=previous,
            chain=chain,
            prompt=seek_prompt
        )

        # Store session
        sessions[session_id] = patient
        session_metadata[session_id] = {
            "created_at": datetime.now(),
            "profile": portrait,
            "message_count": 0,
            "status": "active"
        }

        logger.info(f"Created session {session_id} for patient {request.patient_id}")

        return SessionResponse(
            session_id=session_id,
            created_at=session_metadata[session_id]["created_at"].isoformat(),
            profile=PatientProfile(**portrait),
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
        response, emotion, complaint = patient.chat(request.message)

        # Update metadata
        session_metadata[session_id]["message_count"] += 1

        # Build response with additional info
        chat_response = ChatResponse(
            response=response,
            emotion=emotion,
            complaint=complaint,
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
