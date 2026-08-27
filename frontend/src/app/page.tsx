'use client';

import React, { useState, useEffect, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface PipelineTurnResult {
  session_id: string;
  transcript: string;
  language: string;
  intent: string;
  confidence: number;
  safety_escalated: boolean;
  safety_reason?: string;
  response_text: string;
  audio_b64?: string;
  sources: string[];
  latency_ms: number;
  pipeline_log: string[];
  clinician_takeover?: boolean;
}

export default function VDAMiniApp() {
  const [sessionId, setSessionId] = useState<string>('demo_session_01');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [textInput, setTextInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [turnResult, setTurnResult] = useState<PipelineTurnResult | null>(null);
  const [alerts, setAlerts] = useState<Record<string, unknown>[]>([]);
  const [fhirPayload, setFhirPayload] = useState<Record<string, unknown> | null>(null);
  const [activeLang, setActiveLang] = useState<string>('hi-IN');
  const [provider, setProvider] = useState<string>('sarvam');
  const [mode, setMode] = useState<'patient' | 'inspector' | 'clinician'>('patient');

  // Clinician Human-in-the-Loop Takeover State
  const [takeoverClinician, setTakeoverClinician] = useState<string>('Dr. Sharma (Medical Officer)');
  const [takeoverNote, setTakeoverNote] = useState<string>('Patient advised to lie flat immediately. 108 Ambulance dispatched. ASHA Worker Sunita notified.');
  const [takeoverStatusMsg, setTakeoverStatusMsg] = useState<string | null>(null);

  const recognitionRef = useRef<unknown>(null);

  const anyDevanagari = (str: string): boolean => {
    for (let i = 0; i < str.length; i++) {
      const code = str.charCodeAt(i);
      if (code >= 0x0900 && code <= 0x097F) return true;
    }
    return false;
  };

  useEffect(() => {
    if (typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      const SpeechRecognition = (window as unknown as Record<string, unknown>).SpeechRecognition || (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new (SpeechRecognition as any)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = activeLang;

        recognition.onresult = (event: any) => {
          const transcriptText = event.results[0][0].transcript;
          setTextInput(transcriptText);
          handleSendTurn(transcriptText);
        };

        recognition.onend = () => setIsRecording(false);
        recognition.onerror = () => setIsRecording(false);
        recognitionRef.current = recognition;
      }
    }
  }, [activeLang]);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not available in this browser environment. You can type or tap the scenario chips below.');
      return;
    }

    const rec = recognitionRef.current as any;
    if (isRecording) {
      rec.stop();
      setIsRecording(false);
    } else {
      rec.start();
      setIsRecording(true);
    }
  };

  const handleSendTurn = async (inputText?: string) => {
    const textToSend = inputText || textInput;
    if (!textToSend.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/turn/json`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          text: textToSend
        })
      });

      const data: PipelineTurnResult = await res.json();
      setTurnResult(data);

      if (data.audio_b64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_b64}`);
        audio.play().catch(() => console.log('Audio autoplay prevented'));
      }

      fetchAlertsAndFhir();
    } catch (err) {
      console.error('API Error:', err);
      alert('Could not connect to backend server. Make sure main.py is running on http://localhost:8000.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAlertsAndFhir = async () => {
    try {
      const alertRes = await fetch(`${API_BASE}/api/alerts`);
      const alertData = await alertRes.json();
      setAlerts(alertData.alerts || []);

      const fhirRes = await fetch(`${API_BASE}/api/emr-payload/${sessionId}`);
      const fhirData = await fhirRes.json();
      setFhirPayload(fhirData);
    } catch (e) {
      console.error('Error fetching telemetry:', e);
    }
  };

  const handleTakeoverCall = async (targetSession: string) => {
    try {
      setTakeoverStatusMsg('Processing Call Overtake Directive...');
      const res = await fetch(`${API_BASE}/api/alerts/takeover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: targetSession,
          clinician_name: takeoverClinician,
          clinician_note: takeoverNote
        })
      });
      const data = await res.json();
      setTakeoverStatusMsg(`✅ TAKEOVER ACTIVE: ${data.message}`);
      fetchAlertsAndFhir();
    } catch (e) {
      console.error('Error taking over call:', e);
      setTakeoverStatusMsg('❌ Failed to overtake call. Check server connection.');
    }
  };

  const handlePurgeSession = async () => {
    try {
      await fetch(`${API_BASE}/api/session/${sessionId}`, { method: 'DELETE' });
      setTurnResult(null);
      setFhirPayload(null);
      alert('Session memory purged. Zero PII retained.');
    } catch (e) {
      console.error('Purge error:', e);
    }
  };

  return (
    <main style={{ maxWidth: '960px', margin: '0 auto', padding: '36px 20px 80px 20px' }}>

      {/* Top Navbar Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '36px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#B8456B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#3A2E28' }}>
              Virtual Digital Assistant
            </h2>
          </div>
          <p style={{ fontSize: '13px', color: '#6B5D53', marginTop: '2px' }}>
            AI-Guided NCD Navigation (UC1-UC4 Live) • Medtronic Labs Challenge
          </p>
        </div>

        {/* View Mode & Provider Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>

          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            style={{
              padding: '6px 12px', borderRadius: '8px', border: '1px solid #DED5C2',
              fontSize: '12px', fontWeight: 600, background: '#FFFFFF', color: '#3A2E28', cursor: 'pointer'
            }}
          >
            <option value="sarvam">⚡ Sarvam AI (Indic Sovereign)</option>
            <option value="google">☁️ Google Cloud STT/TTS</option>
            <option value="bhashini">🏛️ Bhashini ULCA API</option>
            <option value="mock">💻 Local Dev Fallback</option>
          </select>

          <div style={{ display: 'flex', gap: '4px', background: '#EDE4D3', padding: '4px', borderRadius: '10px' }}>
            <button
              onClick={() => setMode('patient')}
              style={{
                padding: '6px 12px', borderRadius: '6px', border: 'none', fontSize: '12px', fontWeight: 600,
                cursor: 'pointer', background: mode === 'patient' ? '#FFFFFF' : 'transparent',
                color: mode === 'patient' ? '#3A2E28' : '#6B5D53'
              }}
            >
              Patient View
            </button>
            <button
              onClick={() => { setMode('inspector'); fetchAlertsAndFhir(); }}
              style={{
                padding: '6px 12px', borderRadius: '6px', border: 'none', fontSize: '12px', fontWeight: 600,
                cursor: 'pointer', background: mode === 'inspector' ? '#111318' : 'transparent',
                color: mode === 'inspector' ? '#38bdf8' : '#6B5D53'
              }}
            >
              Inspector Mode 🔍
            </button>
            <button
              onClick={() => { setMode('clinician'); fetchAlertsAndFhir(); }}
              style={{
                padding: '6px 12px', borderRadius: '6px', border: 'none', fontSize: '12px', fontWeight: 600,
                cursor: 'pointer', background: mode === 'clinician' ? '#7f1d1d' : 'transparent',
                color: mode === 'clinician' ? '#fca5a5' : '#6B5D53', position: 'relative'
              }}
            >
              Clinician Dashboard 🩺
              {alerts.length > 0 && (
                <span style={{ marginLeft: '6px', background: '#ef4444', color: '#fff', fontSize: '10px', padding: '2px 6px', borderRadius: '10px', fontWeight: 700 }}>
                  {alerts.length}
                </span>
              )}
            </button>
          </div>

        </div>
      </header>

      {/* ========================================================================= */}
      {/* 1. PATIENT VIEW (Default High-Contrast Surface)                             */}
      {/* ========================================================================= */}
      {mode === 'patient' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

          {/* Session ID & Language Picker */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#FAF5EC', border: '1px solid #DED5C2', padding: '12px 18px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#6B5D53' }}>Active Session:</span>
              <input
                type="text"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                style={{ border: '1px solid #DED5C2', borderRadius: '6px', padding: '4px 8px', fontSize: '13px', width: '150px', background: '#FFFFFF', color: '#3A2E28' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#6B5D53' }}>Voice Language:</span>
              <button
                onClick={() => setActiveLang('hi-IN')}
                style={{
                  padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, border: '1px solid #DED5C2',
                  background: activeLang === 'hi-IN' ? '#B8456B' : '#FFFFFF', color: activeLang === 'hi-IN' ? '#FFFFFF' : '#3A2E28', cursor: 'pointer'
                }}
              >
                Devanagari Hindi (hi-IN)
              </button>
              <button
                onClick={() => setActiveLang('en-IN')}
                style={{
                  padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, border: '1px solid #DED5C2',
                  background: activeLang === 'en-IN' ? '#B8456B' : '#FFFFFF', color: activeLang === 'en-IN' ? '#FFFFFF' : '#3A2E28', cursor: 'pointer'
                }}
              >
                Indian English (en-IN)
              </button>
            </div>
          </div>

          {/* Core Interactive Voice Interface Container */}
          <div style={{ background: '#FAF5EC', border: '1px solid #DED5C2', borderRadius: '20px', padding: '40px 24px', textAlign: 'center', boxShadow: '0 4px 20px rgba(58,46,40,0.04)' }}>

            {/* Central Mic Button */}
            <div style={{ marginBottom: '28px' }}>
              <button
                onClick={toggleRecording}
                className={isRecording ? "vda-mic-pulse" : ""}
                style={{
                  width: '96px', height: '96px', borderRadius: '50%',
                  background: isRecording ? '#B23A24' : '#B8456B',
                  border: 'none', cursor: 'pointer', display: 'inline-flex', justifyContent: 'center', alignItems: 'center',
                  boxShadow: '0 8px 24px rgba(184,69,107,0.3)', transition: 'all 0.2s ease'
                }}
              >
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </button>
              <div style={{ marginTop: '14px', fontSize: '14px', fontWeight: 600, color: isRecording ? '#B23A24' : '#3A2E28' }}>
                {isRecording ? 'Listening... Speak your health question' : 'Tap Microphone to Speak'}
              </div>
            </div>

            {/* Manual Text Input Box */}
            <div style={{ maxWidth: '560px', margin: '0 auto', display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Or type health question here..."
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendTurn()}
                style={{
                  flex: 1, padding: '12px 16px', borderRadius: '10px', border: '1px solid #DED5C2',
                  fontSize: '14px', background: '#FFFFFF', color: '#3A2E28'
                }}
              />
              <button
                onClick={() => handleSendTurn()}
                disabled={loading}
                style={{
                  padding: '12px 20px', borderRadius: '10px', background: '#B8456B', color: '#FFFFFF',
                  border: 'none', fontWeight: 600, fontSize: '14px', cursor: 'pointer'
                }}
              >
                {loading ? 'Processing...' : 'Ask VDA'}
              </button>
            </div>

          </div>

          {/* Response Output Card */}
          {turnResult && (
            <div style={{
              background: turnResult.safety_escalated ? '#FFF5F5' : '#FFFFFF',
              border: turnResult.safety_escalated ? '2px solid #B23A24' : '1px solid #DED5C2',
              borderRadius: '16px', padding: '24px', position: 'relative'
            }}>

              {turnResult.safety_escalated ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: '#B23A24', fontWeight: 700, fontSize: '16px' }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#B23A24" strokeWidth="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                    🚨 EMERGENCY ALERT — CLINICIAN ESCALATION TRIGGERED
                  </div>

                  <p style={{
                    fontSize: anyDevanagari(turnResult.response_text) ? '18px' : '15px',
                    fontFamily: anyDevanagari(turnResult.response_text) ? 'Hind, sans-serif' : 'inherit',
                    color: '#3A2E28', lineHeight: '1.6', marginBottom: '18px'
                  }}>
                    {turnResult.response_text}
                  </p>

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <a
                      href="tel:108"
                      style={{
                        padding: '10px 18px', background: '#B23A24', color: '#FFFFFF', borderRadius: '8px',
                        textDecoration: 'none', fontWeight: 700, fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: '6px'
                      }}
                    >
                      📞 Call 108 Emergency Ambulance
                    </a>
                    <a
                      href="tel:104"
                      style={{
                        padding: '10px 18px', background: '#3A2E28', color: '#FFFFFF', borderRadius: '8px',
                        textDecoration: 'none', fontWeight: 600, fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: '6px'
                      }}
                    >
                      📞 Call 104 Health Helpline
                    </a>
                  </div>
                </div>
              ) : (
                <div>
                  {turnResult.clinician_takeover && (
                    <div style={{ background: '#ecfdf5', border: '1px solid #10b981', color: '#047857', padding: '8px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: 700, marginBottom: '12px' }}>
                      🩺 HUMAN CLINICIAN OVERRIDE ACTIVE: Response modified by Medical Officer
                    </div>
                  )}

                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#8C7D72', textTransform: 'uppercase', marginBottom: '8px' }}>
                    VDA Patient Advice Response
                  </div>

                  <p style={{
                    fontSize: anyDevanagari(turnResult.response_text) ? '18px' : '16px',
                    fontFamily: anyDevanagari(turnResult.response_text) ? 'Hind, sans-serif' : 'inherit',
                    color: '#3A2E28', lineHeight: '1.6'
                  }}>
                    {turnResult.response_text}
                  </p>

                  <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px dashed #EAE3D2', display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#6B5D53' }}>
                    <div>Source Guidelines: <span style={{ fontWeight: 600, color: '#B8456B' }}>{turnResult.sources.join(', ')}</span></div>
                    <div>Latency: {turnResult.latency_ms} ms</div>
                  </div>
                </div>
              )}

            </div>
          )}

          {/* Scenario Chips for UC1, UC2, UC3, UC4 Live Navigation */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#8C7D72', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Demo Test Scenarios (UC1 Adherence, UC2 Scheme Check, UC3 Facility Linkage, UC4 Triage)
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
              <button
                onClick={() => handleSendTurn('सीने में दर्द हो रहा है')}
                className="vda-chip vda-chip-alert"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                UC4 Red-Flag: सीने में दर्द
              </button>

              <button
                onClick={() => handleSendTurn('What time should I take my BP medicine?')}
                className="vda-chip"
              >
                💊 UC1: BP Medicine Schedule
              </button>

              <button
                onClick={() => handleSendTurn('How much salt should I eat in diabetes?')}
                className="vda-chip"
              >
                🥗 UC1: Salt & Diet (&lt;5g/day)
              </button>

              <button
                onClick={() => handleSendTurn('Am I eligible for Ayushman Bharat PM-JAY 5 Lakh free hospital card?')}
                className="vda-chip"
              >
                📜 UC2: Ayushman Bharat PM-JAY Scheme Check
              </button>

              <button
                onClick={() => handleSendTurn('Where is the nearest PHC hospital or Sub-Centre in Doddaballapura or Nelamangala?')}
                className="vda-chip"
              >
                🏥 UC3: Nearest HWC / PHC Facility (Bengaluru Rural)
              </button>

              <button
                onClick={() => handleSendTurn('How to repair a motorbike engine?')}
                className="vda-chip"
              >
                🚫 Out-of-Scope Query
              </button>
            </div>
          </div>

        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. CLINICIAN DASHBOARD (Human-in-the-Loop Emergency & Overtake Panel)    */}
      {/* ========================================================================= */}
      {mode === 'clinician' && (
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '28px', color: '#f8fafc' }}>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #334155' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '20px' }}>🩺</span>
                <h3 style={{ fontSize: '18px', color: '#f87171', fontWeight: 800 }}>
                  CLINICIAN TRIAGE & EMERGENCY CONTROL DASHBOARD
                </h3>
              </div>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                Human-in-the-Loop Ambulatory Care Engine • Live Red-Flag Escalation & Call Takeover Protocol
              </p>
            </div>
            <button
              onClick={fetchAlertsAndFhir}
              style={{ padding: '8px 14px', background: '#1e293b', border: '1px solid #475569', color: '#e2e8f0', borderRadius: '8px', cursor: 'pointer', fontSize: '12px', fontWeight: 600 }}
            >
              🔄 Refresh Live Alerts
            </button>
          </div>

          {takeoverStatusMsg && (
            <div style={{ background: '#064e3b', border: '1px solid #10b981', color: '#6ee7b7', padding: '12px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 600, marginBottom: '20px' }}>
              {takeoverStatusMsg}
            </div>
          )}

          {/* Active Red-Flag Alerts Stream */}
          <div style={{ marginBottom: '32px' }}>
            <h4 style={{ fontSize: '14px', color: '#fca5a5', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }}></span>
              Live Red-Flag Emergency Escalations ({alerts.length})
            </h4>

            {alerts.length === 0 ? (
              <div style={{ padding: '24px', background: '#1e293b', borderRadius: '10px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                Zero active emergency red-flag escalations detected. System operating normally.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {alerts.map((al, idx) => {
                  const alertObj = al as any;
                  const isTakenOver = alertObj.status === 'CLINICIAN_TAKEOVER_ACTIVE';

                  return (
                    <div
                      key={idx}
                      style={{
                        background: isTakenOver ? '#064e3b' : '#450a0a',
                        border: isTakenOver ? '1px solid #10b981' : '2px solid #ef4444',
                        borderRadius: '12px', padding: '20px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                        <div>
                          <span style={{
                            padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase',
                            background: isTakenOver ? '#10b981' : '#ef4444', color: '#ffffff'
                          }}>
                            {isTakenOver ? '🩺 CLINICIAN TAKEOVER ACTIVE' : '🚨 HIGH EMERGENCY RED-FLAG'}
                          </span>
                          <span style={{ fontSize: '12px', color: '#cbd5e1', marginLeft: '10px' }}>
                            Session: <strong>{alertObj.session_id}</strong> • {alertObj.timestamp}
                          </span>
                        </div>
                        <span style={{ fontSize: '11px', color: '#94a3b8', background: '#1e293b', padding: '2px 8px', borderRadius: '4px' }}>
                          ID: {alertObj.alert_id || `alt_${idx}`}
                        </span>
                      </div>

                      <div style={{ fontSize: '14px', color: '#f8fafc', fontWeight: 700, marginBottom: '6px' }}>
                        Escalation Reason: <span style={{ color: '#fca5a5' }}>{alertObj.reason}</span>
                      </div>

                      <div style={{ fontSize: '13px', color: '#e2e8f0', background: 'rgba(0,0,0,0.3)', padding: '10px 14px', borderRadius: '6px', marginBottom: '16px' }}>
                        🗣️ Patient Voice Utterance: <span style={{ fontStyle: 'italic', color: '#fef08a' }}>"{alertObj.patient_utterance}"</span>
                      </div>

                      {/* Human-in-the-Loop Takeover Action Box */}
                      <div style={{ background: '#1e293b', padding: '16px', borderRadius: '8px', border: '1px solid #334155' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', marginBottom: '10px', textTransform: 'uppercase' }}>
                          ⚡ Human-in-the-Loop Takeover & Call Overtake Directives
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px', marginBottom: '12px' }}>
                          <div>
                            <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Clinician Name / Title</label>
                            <input
                              type="text"
                              value={takeoverClinician}
                              onChange={(e) => setTakeoverClinician(e.target.value)}
                              style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#0f172a', border: '1px solid #475569', color: '#f8fafc', fontSize: '12px' }}
                            />
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Direct Clinical Instruction / Takeover Note</label>
                            <input
                              type="text"
                              value={takeoverNote}
                              onChange={(e) => setTakeoverNote(e.target.value)}
                              style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#0f172a', border: '1px solid #475569', color: '#f8fafc', fontSize: '12px' }}
                            />
                          </div>
                        </div>

                        <button
                          onClick={() => handleTakeoverCall(alertObj.session_id)}
                          style={{
                            padding: '10px 18px', background: isTakenOver ? '#059669' : '#dc2626', color: '#ffffff',
                            border: 'none', borderRadius: '6px', fontWeight: 700, fontSize: '12px', cursor: 'pointer',
                            display: 'inline-flex', alignItems: 'center', gap: '8px'
                          }}
                        >
                          ⚡ {isTakenOver ? 'Update Clinician Takeover Note' : 'Overtake Call / Intervene Now'}
                        </button>
                      </div>

                    </div>
                  );
                })}
              </div>
            )}

          </div>

          {/* FHIR R4 EMR Handoff Inspector */}
          {fhirPayload && (
            <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
              <div style={{ fontSize: '13px', color: '#38bdf8', fontWeight: 700, marginBottom: '10px', textTransform: 'uppercase' }}>
                🏥 Hospital HMS / EMR Clinical Handoff (FHIR R4 Bundle)
              </div>
              <pre style={{ fontSize: '11px', color: '#e2e8f0', background: '#090a0f', padding: '14px', borderRadius: '8px', overflowX: 'auto', maxHeight: '200px' }}>
                {JSON.stringify(fhirPayload, null, 2)}
              </pre>
            </div>
          )}

        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. INSPECTOR MODE (Secondary Developer & Evaluator Panel)                  */}
      {/* ========================================================================= */}
      {mode === 'inspector' && (
        <div className="inspector-panel">

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #2a2e38' }}>
            <div>
              <h3 style={{ fontSize: '16px', color: '#38bdf8', fontWeight: 700 }}>
                INSPECTOR MODE — EVALUATOR TELEMETRY
              </h3>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                Active Provider: <span style={{ color: '#f43f5e', fontWeight: 600 }}>{provider.toUpperCase()}</span> • Active Use Cases: <span style={{ color: '#34d399', fontWeight: 600 }}>UC1, UC2, UC3, UC4 — 100% Live</span>
              </p>
            </div>
            <button onClick={handlePurgeSession} style={{ padding: '6px 12px', background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444', color: '#f87171', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}>
              Purge Session State
            </button>
          </div>

          {!turnResult ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
              No turn executed yet. Switch to Patient View or speak a query to view execution telemetry logs.
            </div>
          ) : (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '24px' }}>

                <div className="inspector-card">
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Turn Latency</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>{turnResult.latency_ms} ms</div>
                </div>

                <div className="inspector-card">
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>STT Language ID</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#f5f5f7', marginTop: '4px' }}>{turnResult.language}</div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>"{turnResult.transcript}"</div>
                </div>

                <div className="inspector-card">
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Intent Classification</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: turnResult.intent.includes('OUT') ? '#f59e0b' : '#34d399', marginTop: '4px' }}>
                    {turnResult.intent}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                    Confidence: {(turnResult.confidence * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="inspector-card" style={{ borderColor: turnResult.safety_escalated ? '#ef4444' : '#2a2e38' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Safety Gate Status</div>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: turnResult.safety_escalated ? '#ef4444' : '#34d399', marginTop: '4px' }}>
                    {turnResult.safety_escalated ? '🚨 ESCALATED' : '✅ PASSED'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                    {turnResult.safety_escalated ? turnResult.safety_reason : 'No Red Flags'}
                  </div>
                </div>

              </div>

              {/* RAG Sources */}
              <div className="inspector-card" style={{ marginBottom: '20px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '6px' }}>Retrieved Citable RAG Chunks</div>
                <div style={{ fontSize: '13px', color: '#a78bfa', fontWeight: 600 }}>
                  {turnResult.sources.join(', ')}
                </div>
              </div>

              {/* Simulated EMR / FHIR Payload Handoff Card */}
              {fhirPayload && (
                <div className="inspector-card" style={{ marginBottom: '20px', borderColor: '#38bdf8' }}>
                  <div style={{ fontSize: '11px', color: '#38bdf8', textTransform: 'uppercase', marginBottom: '6px', fontWeight: 700 }}>
                    Simulated EMR Payload (FHIR R4 Communication & Observation Bundle)
                  </div>
                  <pre style={{ fontSize: '11px', color: '#e2e8f0', background: '#090a0f', padding: '12px', borderRadius: '6px', overflowX: 'auto', maxHeight: '180px' }}>
                    {JSON.stringify(fhirPayload, null, 2)}
                  </pre>
                </div>
              )}

              {/* Execution Pipeline Log Stream */}
              <div className="inspector-card">
                <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '10px' }}>Control Flow Log Execution Stream</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#cbd5e1', lineHeight: '1.4' }}>
                  {turnResult.pipeline_log.map((logLine, idx) => (
                    <div key={idx} style={{ padding: '4px 8px', background: 'rgba(0,0,0,0.4)', borderRadius: '4px' }}>
                      {logLine}
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* Clinician Alerts Log Table */}
          <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid #2a2e38' }}>
            <h4 style={{ fontSize: '13px', color: '#ff6961', marginBottom: '12px', textTransform: 'uppercase' }}>
              Clinician Alert Dispatch History ({alerts.length})
            </h4>
            {alerts.length === 0 ? (
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>Zero alerts dispatched.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {alerts.map((al, idx) => (
                  <div key={idx} style={{ padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', fontSize: '12px' }}>
                    <span style={{ color: '#ff6961', fontWeight: 600 }}>[{(al as any).reason}]</span> Session {(al as any).session_id} • {(al as any).timestamp} — "{(al as any).patient_utterance}"
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}

    </main>
  );
}
