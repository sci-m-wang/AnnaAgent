# -*- coding: utf-8 -*-
"""
心理咨询来访者模拟系统 - 基于预生成Prompts的REST API服务器
使用CPsyCounS-3134_prompts.json中的预生成prompts避免初始化延迟
"""

import json
import os
import sys
import uuid
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ms_patient_with_prompt import MsPatient

class PromptBasedBackendService:
    """基于预生成prompts的后端服务"""

    def __init__(self):
        self.patients_data = {}
        self.load_patients_data()

    def load_patients_data(self):
        """加载预生成的患者数据"""
        try:
            prompts_file = "CPsyCounS-3134_prompts.json"
            if os.path.exists(prompts_file):
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    patients = json.load(f)
                    for patient in patients:
                        self.patients_data[patient['id']] = patient
                print(f"已加载 {len(self.patients_data)} 个患者配置")
            else:
                print("警告: 未找到CPsyCounS-3134_prompts.json文件")
        except Exception as e:
            print(f"加载患者数据失败: {e}")

    def extract_patient_info(self, prompt):
        """从prompt中提取患者信息"""
        info = {
            'age': 25,
            'gender': '未知',
            'occupation': '未知',
            'marital_status': '未知',
            'symptoms': '未指定'
        }

        # 提取年龄
        age_match = re.search(r'年龄[:：]\s*(\d+)', prompt)
        if age_match:
            info['age'] = int(age_match.group(1))

        # 提取性别
        if '性别: 女' in prompt or '性别：女' in prompt:
            info['gender'] = '女'
        elif '性别: 男' in prompt or '性别：男' in prompt:
            info['gender'] = '男'

        # 提取职业
        occupation_match = re.search(r'职业[:：]\s*([^\n]+)', prompt)
        if occupation_match:
            info['occupation'] = occupation_match.group(1).strip()

        # 提取婚姻状况
        marital_match = re.search(r'婚姻状况[:：]\s*([^\n]+)', prompt)
        if marital_match:
            info['marital_status'] = marital_match.group(1).strip()

        # 提取症状（从chain的第一个内容）
        symptom_match = re.search(r'症状[:：]\s*([^\n]+)', prompt)
        if symptom_match:
            info['symptoms'] = symptom_match.group(1).strip()

        return info

    def get_system_status(self):
        """获取系统状态"""
        return {
            "status": "running",
            "patients_loaded": len(self.patients_data),
            "active_sessions": len(self.active_sessions),
            "service": "prompt-based-counseling-system"
        }

    def get_available_patients(self):
        """获取可用患者列表"""
        patients = []
        for pid, data in self.patients_data.items():
            info = self.extract_patient_info(data.get('seeker_prompt', ''))
            patients.append({
                "patient_id": pid,
                "name": f"患者_{pid[:8]}",
                "profile": info,
                "symptom_count": len(data.get('chain', [])),
                "description": data.get('chain', [{}])[0].get('content', '未指定') if data.get('chain') else '未指定'
            })
        return patients

# 创建服务实例
backend_service = PromptBasedBackendService()

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "接口不存在"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    return jsonify({"error": str(error)}), 500

# 系统状态接口
@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    try:
        status = backend_service.get_system_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 患者管理接口
@app.route('/api/patients', methods=['GET'])
def get_patients():
    """获取所有可用患者"""
    try:
        patients = backend_service.get_available_patients()
        return jsonify({
            "patients": patients,
            "count": len(patients)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient_detail(patient_id):
    """获取患者详细信息"""
    try:
        patients = backend_service.get_available_patients()
        patient = next((p for p in patients if p['patient_id'] == patient_id), None)

        if not patient:
            return jsonify({"error": "患者不存在"}), 404

        # 获取完整患者数据
        full_data = backend_service.patients_data.get(patient_id, {})
        patient['full_prompt'] = full_data.get('seeker_prompt', '')
        patient['chain'] = full_data.get('chain', [])

        return jsonify(patient)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 会话管理接口
@app.route('/api/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    try:
        data = request.get_json()
        if not data or 'patient_id' not in data:
            return jsonify({"error": "缺少patient_id参数"}), 400

        patient_id = data['patient_id']
        session_info = backend_service.create_patient_session(patient_id)

        return jsonify(session_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取活跃会话列表"""
    try:
        sessions = backend_service.get_active_sessions()
        return jsonify({
            "sessions": sessions,
            "count": len(sessions)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话详情"""
    try:
        session_data = backend_service.get_session_history(session_id)
        return jsonify(session_data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def close_session(session_id):
    """关闭会话"""
    try:
        result = backend_service.close_session(session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 对话接口
@app.route('/api/sessions/<session_id>/chat', methods=['POST'])
def chat_with_patient(session_id):
    """与患者对话"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "缺少message参数"}), 400

        message = data['message']
        response = backend_service.chat_with_patient(session_id, message)

        return jsonify(response)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 数据导出接口
@app.route('/api/sessions/<session_id>/export', methods=['POST'])
def export_session(session_id):
    """导出会话数据"""
    try:
        data = request.get_json() or {}
        filename = data.get('filename')

        saved_file = backend_service.save_session_data(session_id, filename)

        return jsonify({
            "session_id": session_id,
            "filename": saved_file,
            "download_url": f"/api/download/{saved_file}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "prompt-based-counseling-system"
    })

# 根路径
@app.route('/', methods=['GET'])
def index():
    """API文档"""
    return jsonify({
        "service": "心理咨询来访者模拟系统 - 基于预生成Prompts的REST API",
        "version": "2.1.0",
        "features": [
            "使用预生成prompts避免初始化延迟",
            "支持1428个患者角色",
            "集成BigModel API (glm-4.5-flash)",
            "实时对话功能",
            "会话管理和数据导出"
        ],
        "configuration": {
            "api_base": "https://open.bigmodel.cn/api/paas/v4/",
            "model": "glm-4.5-flash"
        },
        "endpoints": {
            "系统状态": "/api/status",
            "患者列表": "/api/patients",
            "患者详情": "/api/patients/<patient_id>",
            "创建会话": "/api/sessions",
            "会话列表": "/api/sessions",
            "会话详情": "/api/sessions/<session_id>",
            "关闭会话": "/api/sessions/<session_id>",
            "对话接口": "/api/sessions/<session_id>/chat",
            "导出数据": "/api/sessions/<session_id>/export",
            "健康检查": "/health"
        }
    })

if __name__ == '__main__':
    print("心理咨询来访者模拟系统 - 基于预生成Prompts的REST API服务器")
    print("=" * 60)
    print("配置信息:")
    print(f"  API密钥: {os.environ.get('OPENAI_API_KEY', '未设置')[:8]}...")
    print(f"  API地址: {os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')}")
    print(f"  模型: {os.environ.get('OPENAI_MODEL_NAME', 'gpt-3.5-turbo')}")
    print("=" * 60)

    try:
        # 测试服务状态
        status = backend_service.get_system_status()
        print(f"系统状态: {status}")

        patients = backend_service.get_available_patients()
        print(f"可用患者: {len(patients)} 个")

        if patients:
            print("前3个患者示例:")
            for i, p in enumerate(patients[:3]):
                print(f"  {i+1}. {p['name']} - {p['description']} ({p['profile']['age']}岁, {p['profile']['gender']})")

        # 启动服务器
        app.run(
            host='0.0.0.0',
            port=5001,  # 使用不同端口避免冲突
            debug=True,
            threaded=True
        )

    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
