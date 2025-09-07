import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageCircle, User, Brain, Settings, RotateCcw, Play, Pause, FileText, Clock, Heart, Calendar, UserCheck, History, ArrowLeft, ArrowRight } from 'lucide-react';

type Message = {
  id: number;
  type: 'system' | 'counselor' | 'client';
  content: string;
  timestamp: string;
  emotion?: string;
};

type PreviousSession = { session: number; date: string; summary: string };

type ClientProfile = {
  name: string;
  age: number;
  gender: string;
  occupation: string;
  background: string;
  personality: string;
  symptoms: string[];
  previousSessions: PreviousSession[];
  avatar: string;
};

const PsychologyTrainingInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentScenario, setCurrentScenario] = useState('');
  const [sessionTime, setSessionTime] = useState(0);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [currentSession, setCurrentSession] = useState(1);
  const [reviewPreviousSessions, setReviewPreviousSessions] = useState(false);
  const [clientProfile, setClientProfile] = useState<ClientProfile | null>(null);
  const [sessionHistory, setSessionHistory] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showProfile, setShowProfile] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  // 按场景缓存会话与消息，避免切换时重复初始化
  const [sessionsByScenario, setSessionsByScenario] = useState<Record<string, string>>({});
  const [messagesByScenario, setMessagesByScenario] = useState<Record<string, Message[]>>({});

  // 后端 API 基址
  const apiBase = 'http://127.0.0.1:8080';

  // 预设的来访者角色画像
  const clientProfiles = {
    '焦虑症状咨询': {
      name: '李明',
      age: 28,
      gender: '男',
      occupation: '软件工程师',
      background: '工作压力大，经常加班，最近出现焦虑症状',
      personality: '内向、完美主义、责任心强',
      symptoms: ['失眠', '心跳加速', '担心工作表现', '社交回避'],
      previousSessions: [
        { session: 1, date: '2024-08-15', summary: '初诊，主要症状为工作焦虑和失眠' },
        { session: 2, date: '2024-08-22', summary: '探讨了工作压力来源，学习了呼吸放松技巧' }
      ],
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face'
    },
    '抑郁情绪疏导': {
      name: '王小雨',
      age: 24,
      gender: '女',
      occupation: '大学生',
      background: '即将毕业，对未来感到迷茫，情绪低落',
      personality: '敏感、善良、缺乏自信',
      symptoms: ['情绪低落', '兴趣减退', '自我价值感低', '未来焦虑'],
      previousSessions: [
        { session: 1, date: '2024-08-10', summary: '表达了对未来的担忧和无助感' },
        { session: 2, date: '2024-08-17', summary: '探索了个人兴趣和价值观' }
      ],
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b2b5a6d4?w=100&h=100&fit=crop&crop=face'
    },
    '人际关系困扰': {
      name: '张浩',
      age: 32,
      gender: '男',
      occupation: '销售经理',
      background: '在职场和家庭关系中都遇到困难',
      personality: '外向但缺乏深度沟通技巧',
      symptoms: ['人际冲突', '沟通困难', '情绪控制问题', '关系焦虑'],
      previousSessions: [
        { session: 1, date: '2024-08-12', summary: '讨论了与同事的冲突问题' },
        { session: 2, date: '2024-08-19', summary: '练习了积极沟通技巧' }
      ],
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face'
    },
    '职场压力应对': {
      name: '刘芳',
      age: 35,
      gender: '女',
      occupation: '财务主管',
      background: '工作责任重大，面临晋升压力',
      personality: '认真负责、追求完美、容易焦虑',
      symptoms: ['工作焦虑', '完美主义', '身体疲劳', '情绪波动'],
      previousSessions: [
        { session: 1, date: '2024-08-14', summary: '探讨了完美主义对工作和生活的影响' },
        { session: 2, date: '2024-08-21', summary: '学习了压力管理和时间规划技巧' }
      ],
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face'
    },
    '家庭关系冲突': {
      name: '陈建国',
      age: 45,
      gender: '男',
      occupation: '中学教师',
      background: '与青春期孩子关系紧张，夫妻沟通存在问题',
      personality: '传统、固执、关心家庭但表达方式有问题',
      symptoms: ['家庭冲突', '沟通障碍', '情绪爆发', '关系疏远'],
      previousSessions: [
        { session: 1, date: '2024-08-13', summary: '讨论了与儿子的冲突和沟通问题' },
        { session: 2, date: '2024-08-20', summary: '探索了家庭动力学和沟通模式' }
      ],
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face'
    }
  };

  // 模拟场景选项
  const scenarios = [
    { name: '焦虑症状咨询', difficulty: '初级', description: '来访者表现出焦虑情绪和睡眠问题' },
    { name: '抑郁情绪疏导', difficulty: '中级', description: '来访者情绪低落，对生活失去兴趣' },
    { name: '人际关系困扰', difficulty: '初级', description: '来访者在人际交往中遇到困难' },
    { name: '职场压力应对', difficulty: '中级', description: '来访者面临工作压力和职业倦怠' },
    { name: '家庭关系冲突', difficulty: '高级', description: '来访者家庭关系紧张，需要深度疏导' }
  ];

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 计时器
  useEffect(() => {
    let interval;
    if (isSessionActive) {
      interval = setInterval(() => {
        setSessionTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isSessionActive]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const counselorMessage: Message = {
      id: Date.now(),
      type: 'counselor',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, counselorMessage]);
    setInputValue('');
    setIsTyping(true);

    // 启动会话计时
    if (!isSessionActive) {
      setIsSessionActive(true);
    }

    // 调用后端持续会话接口
    try {
      if (!sessionId) {
        setIsTyping(false);
        alert('请先在左侧选择场景以创建会话');
        return;
      }
      const res = await fetch(`${apiBase}/api/sessions/${sessionId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: counselorMessage.content })
      });
      const data = await res.json();
      const clientResponse: Message = {
        id: Date.now() + 1,
        type: 'client',
        content: data.response,
        emotion: undefined,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, clientResponse]);
    } catch (e) {
      const fallback: Message = {
        id: Date.now() + 1,
        type: 'client',
        content: '抱歉，我刚才走神了...可以再说一遍吗？',
        emotion: undefined,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, fallback]);
    } finally {
      setIsTyping(false);
    }
  };

  const getContextualResponses = (profile, includeHistory) => {
    if (!profile) return [{ content: '谢谢您的关心...', emotion: '平静' }];

    const baseResponses = [
      { content: `是的，就像我们之前说的，${profile.symptoms[0]}的情况还是存在...`, emotion: '焦虑' },
      { content: `我一直在想您上次提到的建议，但实施起来还是有些困难。`, emotion: '困惑' },
      { content: `这周的情况和之前差不多，${profile.symptoms[1]}还是会出现。`, emotion: '疲惫' }
    ];

    const historyResponses = [
      { content: `您还记得我们第一次见面时我提到的那个问题吗？现在情况有些变化...`, emotion: '回忆' },
      { content: `我按照您之前教我的方法试了，但是...`, emotion: '尝试' },
      { content: `自从上次咨询后，我一直在思考您说的话。`, emotion: '思考' }
    ];

    return includeHistory ? [...baseResponses, ...historyResponses] : baseResponses;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewSession = async (scenario) => {
    const scenarioName = scenario.name;
    const profile = clientProfiles[scenarioName];

    // 若重复点击同一场景且已有会话，直接返回
    if (currentScenario === scenarioName && sessionId) {
      return;
    }

    // 切换前保存当前场景消息
    if (currentScenario) {
      setMessagesByScenario((prev) => ({
        ...prev,
        [currentScenario]: messages,
      }));
    }

    setCurrentScenario(scenarioName);
    setClientProfile(profile);
    setSessionTime(0);
    setIsSessionActive(false);
    setCurrentSession(profile.previousSessions.length + 1);

    // 若该场景已有缓存，直接恢复
    const cachedSessionId = sessionsByScenario[scenarioName];
    const cachedMessages = messagesByScenario[scenarioName];
    if (cachedSessionId) {
      setSessionId(cachedSessionId);
      if (Array.isArray(cachedMessages) && cachedMessages.length > 0) {
        setMessages(cachedMessages);
      } else {
        const greetingCached = reviewPreviousSessions
          ? `您好，医生。距离我们上次见面已经一周了，我想继续聊聊之前的话题...`
          : getInitialGreeting(profile, scenarioName);
        setMessages([
          {
            id: 1,
            type: 'system',
            content: `已开始第 ${profile.previousSessions.length + 1} 次「${scenarioName}」模拟训练 (${scenario.difficulty})`,
            timestamp: new Date().toLocaleTimeString()
          },
          {
            id: 2,
            type: 'client',
            content: greetingCached,
            emotion: getInitialEmotion(profile),
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      }
      return;
    }

    // 首次进入该场景：创建新会话并缓存
    try {
      const payload = {
        profile: {
          age: String(profile.age),
          gender: String(profile.gender),
          occupation: String(profile.occupation),
          martial_status: '未婚',
          symptoms: Array.isArray(profile.symptoms) ? profile.symptoms.join('，') : String(profile.symptoms || '')
        },
        report: { title: scenarioName },
        previous_conversations: []
      };
      const res = await fetch(`${apiBase}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setSessionId(data.session_id);
      setSessionsByScenario((prev) => ({ ...prev, [scenarioName]: data.session_id }));

      const greeting = reviewPreviousSessions ?
        `您好，医生。距离我们上次见面已经一周了，我想继续聊聊之前的话题...` :
        getInitialGreeting(profile, scenarioName);

      setMessages([
        {
          id: 1,
          type: 'system',
          content: `已开始第 ${profile.previousSessions.length + 1} 次「${scenarioName}」模拟训练 (${scenario.difficulty})`,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: 2,
          type: 'client',
          content: greeting,
          emotion: getInitialEmotion(profile),
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } catch (e) {
      setSessionId(null);
    }
  };

  const getInitialGreeting = (profile, scenarioName) => {
    const greetings = {
      '焦虑症状咨询': '你好，医生... 我最近总是感到很焦虑，晚上睡不着觉。',
      '抑郁情绪疏导': '医生，我最近总是感到很沮丧，对什么事都提不起兴趣...',
      '人际关系困扰': '医生，我想和您聊一下我最近在人际关系上遇到的问题...',
      '职场压力应对': '医生，我工作压力很大，感觉快要承受不住了...',
      '家庭关系冲突': '医生，我和家人的关系最近很紧张，不知道该怎么办...'
    };
    return greetings[scenarioName] || '医生，我想和您聊一下我最近遇到的一些问题...';
  };

  const getInitialEmotion = (profile) => {
    if (profile.symptoms.includes('失眠')) return '焦虑';
    if (profile.symptoms.includes('情绪低落')) return '低落';
    if (profile.symptoms.includes('人际冲突')) return '困惑';
    return '紧张';
  };

  const getEmotionColor = (emotion) => {
    const colors = {
      '焦虑': 'text-orange-400',
      '紧张': 'text-red-400',
      '担忧': 'text-yellow-400',
      '疲惫': 'text-gray-400',
      '低落': 'text-blue-400',
      '困惑': 'text-purple-400',
      '回忆': 'text-indigo-400',
      '尝试': 'text-green-400',
      '思考': 'text-teal-400',
      '平静': 'text-emerald-400'
    };
    return colors[emotion] || 'text-gray-400';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      {/* 温和的背景装饰 */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-20 w-64 h-64 bg-emerald-200 rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
        <div className="absolute top-40 right-20 w-72 h-72 bg-cyan-200 rounded-full mix-blend-multiply filter blur-xl animate-pulse" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-teal-200 rounded-full mix-blend-multiply filter blur-xl animate-pulse" style={{ animationDelay: '4s' }}></div>
      </div>

      <div className="relative z-10 flex h-screen">
        {/* 左侧功能面板 */}
        <div className="w-96 bg-white/70 backdrop-blur-xl border-r border-emerald-200/50 shadow-xl">
          <div className="p-6">
            {/* 标题区域 */}
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 shadow-lg">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-emerald-800">心理咨询训练系统</h1>
                <p className="text-sm text-emerald-600">多疗程记忆版</p>
              </div>
            </div>

            {/* 当前会话信息 */}
            <div className="bg-gradient-to-r from-emerald-100 to-teal-100 rounded-2xl p-4 mb-6 border border-emerald-200/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-emerald-700">当前场景</span>
                <div className="flex items-center gap-2 text-emerald-600">
                  <Clock className="w-4 h-4" />
                  <span className="text-sm font-mono">{formatTime(sessionTime)}</span>
                </div>
              </div>
              <h3 className="font-semibold text-emerald-800">{currentScenario}</h3>
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-2">
                  {isSessionActive ? (
                    <>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-600">第 {currentSession} 次会话</span>
                    </>
                  ) : (
                    <>
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                      <span className="text-xs text-gray-500">等待开始</span>
                    </>
                  )}
                </div>
                {clientProfile && (
                  <button
                    onClick={() => setShowProfile(!showProfile)}
                    className="text-xs text-emerald-600 hover:text-emerald-700 underline"
                  >
                    {showProfile ? '隐藏' : '查看'}档案
                  </button>
                )}
              </div>
            </div>

            {/* 来访者档案 */}
            {showProfile && clientProfile && (
              <div className="bg-white/80 rounded-2xl p-4 mb-6 border border-emerald-200/50 shadow-lg">
                <div className="flex items-center gap-3 mb-3">
                  <img
                    src={clientProfile.avatar}
                    alt={clientProfile.name}
                    className="w-12 h-12 rounded-full object-cover border-2 border-emerald-200"
                  />
                  <div>
                    <h4 className="font-semibold text-emerald-800">{clientProfile.name}</h4>
                    <p className="text-sm text-emerald-600">{clientProfile.age}岁 · {clientProfile.gender} · {clientProfile.occupation}</p>
                  </div>
                </div>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="font-medium text-emerald-700">背景：</span>
                    <p className="text-emerald-600 mt-1">{clientProfile.background}</p>
                  </div>
                  <div>
                    <span className="font-medium text-emerald-700">性格特点：</span>
                    <p className="text-emerald-600 mt-1">{clientProfile.personality}</p>
                  </div>
                  <div>
                    <span className="font-medium text-emerald-700">主要症状：</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {clientProfile.symptoms.map((symptom, index) => (
                        <span key={index} className="bg-red-100 text-red-600 px-2 py-1 rounded-full text-xs">
                          {symptom}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 疗程记忆设置 */}
            <div className="bg-blue-50 rounded-2xl p-4 mb-6 border border-blue-200/50">
              <div className="flex items-center gap-2 mb-3">
                <History className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">疗程记忆</span>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reviewPreviousSessions}
                  onChange={(e) => setReviewPreviousSessions(e.target.checked)}
                  className="rounded border-blue-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-blue-600">回顾之前疗程内容</span>
              </label>
              <p className="text-xs text-blue-500 mt-2">
                开启后，AI来访者会记住之前的咨询内容并继续讨论
              </p>
            </div>

            {/* 历史疗程记录 */}
            {clientProfile && (
              <div className="bg-gray-50 rounded-2xl p-4 mb-6 border border-gray-200/50">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-4 h-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">历史疗程</span>
                </div>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {clientProfile.previousSessions.map((session, index) => (
                    <div key={index} className="bg-white/80 rounded-lg p-2 border border-gray-200/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-700">第 {session.session} 次</span>
                        <span className="text-xs text-gray-500">{session.date}</span>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed">{session.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 场景选择 */}
            <div className="mb-6">
              <h3 className="font-semibold text-emerald-800 mb-3">选择练习场景</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {scenarios.map((scenario, index) => (
                  <div
                    key={index}
                    onClick={() => startNewSession(scenario)}
                    className="p-3 rounded-xl bg-white/60 hover:bg-white/80 border border-emerald-200/30 hover:border-emerald-300/50 cursor-pointer transition-all duration-200 hover:shadow-md"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-emerald-800 text-sm">{scenario.name}</h4>
                      <span className={`text-xs px-2 py-1 rounded-full ${scenario.difficulty === '初级' ? 'bg-green-100 text-green-600' :
                        scenario.difficulty === '中级' ? 'bg-yellow-100 text-yellow-600' :
                          'bg-red-100 text-red-600'
                        }`}>
                        {scenario.difficulty}
                      </span>
                    </div>
                    <p className="text-xs text-emerald-600 leading-relaxed">{scenario.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 底部工具栏 */}
          <div className="absolute bottom-6 left-6 right-6">
            <div className="flex gap-2">
              <button className="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl bg-emerald-100 hover:bg-emerald-200 transition-colors text-emerald-700 border border-emerald-200">
                <FileText className="w-4 h-4" />
                <span className="text-sm">会话记录</span>
              </button>
              <button className="flex items-center justify-center p-3 rounded-xl bg-emerald-100 hover:bg-emerald-200 transition-colors text-emerald-700 border border-emerald-200">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* 主对话区域 */}
        <div className="flex-1 flex flex-col bg-white/30 backdrop-blur-sm">
          {/* 对话头部 */}
          <div className="p-6 bg-white/70 backdrop-blur-xl border-b border-emerald-200/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {clientProfile ? (
                  <img
                    src={clientProfile.avatar}
                    alt={clientProfile.name}
                    className="w-12 h-12 rounded-full object-cover border-2 border-teal-300 shadow-lg"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-teal-400 to-cyan-400 flex items-center justify-center shadow-lg">
                    <MessageCircle className="w-6 h-6 text-white" />
                  </div>
                )}
                <div>
                  <h2 className="font-semibold text-emerald-800">
                    {clientProfile ? clientProfile.name : '模拟来访者'}
                  </h2>
                  <p className="text-sm text-emerald-600">
                    {clientProfile ? `${clientProfile.age}岁 · ${clientProfile.occupation}` : 'AI 驱动的心理咨询训练伙伴'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-sm text-emerald-600">
                  <UserCheck className="w-4 h-4" />
                  <span>第 {currentSession} 次咨询</span>
                </div>
                <button
                  onClick={() => {
                    setIsSessionActive(false);
                    setSessionTime(0);
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-100 hover:bg-emerald-200 transition-colors text-emerald-700 border border-emerald-200"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span className="text-sm">重置会话</span>
                </button>
              </div>
            </div>
          </div>

          {/* 消息区域 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'counselor' ? 'justify-end' : 'justify-start'}`}>
                {message.type === 'system' ? (
                  <div className="w-full flex justify-center">
                    <div className="bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm border border-emerald-200">
                      {message.content}
                    </div>
                  </div>
                ) : (
                  <div className={`flex gap-4 max-w-2xl ${message.type === 'counselor' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center shadow-lg ${message.type === 'counselor'
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-500'
                      : ''
                      }`}>
                      {message.type === 'counselor' ? (
                        <User className="w-6 h-6 text-white" />
                      ) : clientProfile ? (
                        <img
                          src={clientProfile.avatar}
                          alt={clientProfile.name}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                      ) : (
                        <Heart className="w-6 h-6 text-white" />
                      )}
                    </div>
                    <div className={`rounded-3xl px-6 py-4 shadow-lg ${message.type === 'counselor'
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50'
                      : 'bg-white/80 backdrop-blur-sm border border-emerald-200/50'
                      }`}>
                      <p className={`leading-relaxed ${message.type === 'counselor' ? 'text-blue-800' : 'text-emerald-800'
                        }`}>
                        {message.content}
                      </p>
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-xs text-gray-500">{message.timestamp}</span>
                        {message.emotion && (
                          <span className={`text-xs px-2 py-1 rounded-full bg-gray-100 ${getEmotionColor(message.emotion)}`}>
                            情绪: {message.emotion}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="flex gap-4 max-w-2xl">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full shadow-lg overflow-hidden">
                    {clientProfile ? (
                      <img
                        src={clientProfile.avatar}
                        alt={clientProfile.name}
                        className="w-12 h-12 object-cover"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-gradient-to-r from-rose-400 to-pink-400 flex items-center justify-center">
                        <Heart className="w-6 h-6 text-white" />
                      </div>
                    )}
                  </div>
                  <div className="rounded-3xl px-6 py-4 bg-white/80 backdrop-blur-sm border border-emerald-200/50 shadow-lg">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 输入区域 */}
          <div className="p-6 bg-white/70 backdrop-blur-xl border-t border-emerald-200/50">
            <div className="max-w-4xl mx-auto">
              <div className="flex gap-4 items-end">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="请输入您的咨询回应..."
                    className="w-full p-4 pr-12 rounded-2xl bg-white/80 backdrop-blur-sm border-2 border-emerald-200/50 text-emerald-800 placeholder-emerald-500/70 resize-none focus:outline-none focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100 transition-all shadow-lg"
                    rows={1}
                    style={{ minHeight: '60px' }}
                  />
                </div>
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isTyping}
                  className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 shadow-lg"
                >
                  <Send className="w-5 h-5 text-white" />
                </button>
              </div>
              <div className="flex items-center justify-between mt-4">
                <p className="text-xs text-emerald-600">
                  按 Enter 发送，Shift + Enter 换行
                </p>
                <div className="flex items-center gap-4 text-xs text-emerald-600">
                  <span>💡 提示：{reviewPreviousSessions ? '关注来访者的历史情况和进展' : '专注于当前症状和感受'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PsychologyTrainingInterface;
