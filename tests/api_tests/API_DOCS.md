# AnnaAgent API 文档

AnnaAgent 心理咨询训练系统的 REST API 接口文档

## 基础信息

- **基础URL**: `http://127.0.0.1:8080`
- **API版本**: v0.1.0
- **响应格式**: JSON

## 认证

当前版本无需认证。

## API 端点

### 1. 系统信息

#### GET /
获取API基本信息和所有可用端点

**响应**:
```json
{
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
```

### 2. 病人管理

#### GET /api/patients
获取病人列表，支持分页和随机排序

**查询参数**:
- `page` (int, optional): 页码，默认为1
- `page_size` (int, optional): 每页数量，默认为10
- `random_order` (bool, optional): 是否随机排序，默认为false

**响应**:
```json
{
  "patients": [
    {
      "id": "42289a5f-bbdc-43f9-826a-9569bbbd5feb",
      "name": "女性求助者",
      "age": "30",
      "gender": "女",
      "occupation": "家庭主妇",
      "symptoms": ["胸闷", "睡眠差", "做噩梦", "食欲不振", "体重下降"],
      "case_title": "家庭压力导致的心理困扰",
      "difficulty": "中级",
      "description": "30岁女性，家庭主妇，主要涉及个人成长 情感关系问题"
    }
  ],
  "total": 3134,
  "page": 1,
  "page_size": 10
}
```

#### GET /api/patients/{patient_id}
获取指定病人的详细信息

**路径参数**:
- `patient_id` (string): 病人ID

**响应**:
```json
{
  "id": "42289a5f-bbdc-43f9-826a-9569bbbd5feb",
  "profile": {
    "age": "30",
    "gender": "女",
    "occupation": "家庭主妇",
    "martial_status": "已婚",
    "symptoms": "胸闷;睡眠差;做噩梦;食欲不振;体重下降"
  },
  "report": {
    "案例标题": "家庭压力导致的心理困扰",
    "案例类别": ["个人成长", "情感关系"],
    "运用的技术": ["认知行为疗法", "情绪聚焦疗法"]
  },
  "conversation_preview": [
    {
      "role": "Seeker",
      "content": "心理咨询师，我觉得我的胸闷症状越来越严重了，这让我很害怕。"
    }
  ],
  "seeker_prompt": "...",
  "chain": [
    {
      "stage": 1,
      "content": "婚姻焦虑"
    }
  ],
  "total_messages": 16
}
```

#### GET /api/patients/ids
获取所有病人ID列表（向后兼容接口）

**响应**:
```json
{
  "ids": ["42289a5f-bbdc-43f9-826a-9569bbbd5feb", "..."],
  "count": 3134
}
```

### 3. 会话管理

#### POST /api/sessions
创建新会话（支持前端自定义profile调用）

**请求体**:
```json
{
  "profile": {
    "age": "28",
    "gender": "男",
    "occupation": "软件工程师",
    "martial_status": "未婚",
    "symptoms": "工作焦虑，失眠"
  },
  "report": {
    "title": "工作压力咨询"
  },
  "previous_conversations": [],
  "seeker_prompt": "...",
  "chain": []
}
```

**响应**:
```json
{
  "session_id": "de671a5f-f752-440d-b9b9-f663a10f487e",
  "created_at": "2025-09-08T22:24:49.169218",
  "profile": {
    "age": "28",
    "gender": "男",
    "occupation": "软件工程师",
    "martial_status": "未婚",
    "symptoms": "工作焦虑，失眠"
  },
  "status": "active"
}
```

#### POST /api/sessions/by_id
根据病人ID创建新会话

**请求体**:
```json
{
  "patient_id": "42289a5f-bbdc-43f9-826a-9569bbbd5feb"
}
```

**响应**:
```json
{
  "session_id": "de671a5f-f752-440d-b9b9-f663a10f487e",
  "created_at": "2025-09-08T22:24:49.169218",
  "profile": {
    "age": "30",
    "gender": "女",
    "occupation": "职场人士",
    "martial_status": "已婚",
    "symptoms": "婚姻困扰;沟通不足;情感疏远;自我价值感低"
  },
  "status": "active"
}
```

#### POST /api/sessions/{session_id}/chat
向指定会话发送消息

**路径参数**:
- `session_id` (string): 会话ID

**请求体**:
```json
{
  "message": "你好，今天感觉怎么样？"
}
```

**响应**:
```json
{
  "response": "（低头摆弄手指）其实...最近工作上的事情让我挺难受的。明明很努力在做项目，但领导好像完全没注意到。",
  "emotion": "neutral",
  "complaint": "工作表现被忽视",
  "session_id": "de671a5f-f752-440d-b9b9-f663a10f487e",
  "timestamp": "2025-09-08T22:25:22.803416",
  "message_count": 1,
  "complaint_stage": 1
}
```

#### GET /api/sessions
获取所有活跃会话列表

**响应**:
```json
{
  "sessions": [
    {
      "session_id": "de671a5f-f752-440d-b9b9-f663a10f487e",
      "created_at": "2025-09-08T22:24:49.169218",
      "message_count": 1,
      "status": "active",
      "profile": {
        "age": "30",
        "gender": "女",
        "occupation": "职场人士",
        "martial_status": "已婚",
        "symptoms": "婚姻困扰;沟通不足;情感疏远;自我价值感低"
      }
    }
  ],
  "total": 1
}
```

#### GET /api/sessions/{session_id}
获取会话详情和对话历史

**路径参数**:
- `session_id` (string): 会话ID

**响应**:
```json
{
  "session_id": "de671a5f-f752-440d-b9b9-f663a10f487e",
  "metadata": {
    "created_at": "2025-09-08T22:24:49.169218",
    "message_count": 1,
    "status": "active",
    "profile": {
      "age": "30",
      "gender": "女",
      "occupation": "职场人士",
      "martial_status": "已婚",
      "symptoms": "婚姻困扰;沟通不足;情感疏远;自我价值感低"
    }
  },
  "conversation": [
    {
      "role": "Counselor",
      "content": "你好，今天感觉怎么样？"
    },
    {
      "role": "Seeker",
      "content": "（低头摆弄手指）其实...最近工作上的事情让我挺难受的。"
    }
  ],
  "complaint_stage": 1,
  "status_summary": "活跃状态"
}
```

#### DELETE /api/sessions/{session_id}
结束会话

**路径参数**:
- `session_id` (string): 会话ID

**响应**:
```json
{
  "message": "会话 de671a5f-f752-440d-b9b9-f663a10f487e 已结束",
  "session_id": "de671a5f-f752-440d-b9b9-f663a10f487e"
}
```

### 4. 健康检查

#### GET /health
系统健康检查

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-08T22:25:22.803416"
}
```

## 错误响应

所有错误响应都采用标准HTTP状态码，并包含错误详情：

```json
{
  "detail": "错误描述信息"
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在  
- `500`: 服务器内部错误

## 使用示例

### 完整的前端交互流程

1. **获取病人列表**:
```bash
curl -X GET "http://127.0.0.1:8080/api/patients?page=1&page_size=10&random_order=true"
```

2. **根据病人ID创建会话**:
```bash
curl -X POST "http://127.0.0.1:8080/api/sessions/by_id" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "42289a5f-bbdc-43f9-826a-9569bbbd5feb"}'
```

3. **开始对话**:
```bash
curl -X POST "http://127.0.0.1:8080/api/sessions/{session_id}/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，今天感觉怎么样？"}'
```

4. **查看会话历史**:
```bash
curl -X GET "http://127.0.0.1:8080/api/sessions/{session_id}"
```

5. **结束会话**:
```bash
curl -X DELETE "http://127.0.0.1:8080/api/sessions/{session_id}"
```

## 数据模型

### PatientProfile
```json
{
  "age": "string",
  "gender": "string", 
  "occupation": "string",
  "martial_status": "string",
  "symptoms": "string"
}
```

### PatientSummary
```json
{
  "id": "string",
  "name": "string",
  "age": "string", 
  "gender": "string",
  "occupation": "string",
  "symptoms": ["string"],
  "case_title": "string",
  "difficulty": "string",
  "description": "string"
}
```

### ChatResponse
```json
{
  "response": "string",
  "emotion": "string",
  "complaint": "string", 
  "session_id": "string",
  "timestamp": "string",
  "message_count": "number",
  "complaint_stage": "number"
}
```

## 部署说明

启动服务器：
```bash
cd /Users/zhangbeibei/code/github/AnnaAgent
python -m uvicorn api_server:app --host 0.0.0.0 --port 8080 --reload
```

访问交互式API文档：
- Swagger UI: `http://127.0.0.1:8080/docs`
- ReDoc: `http://127.0.0.1:8080/redoc`
