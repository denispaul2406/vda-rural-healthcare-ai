'use client';

import React, { useState, useEffect, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

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
  const [mode, setMode] = useState<'patient' | 'inspector'>('patient');

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
      setIsRecording(true);
      rec.lang = activeLang;
      rec.start();
    }
  };

  const fetchAlertsAndFhir = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/alerts`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data.alerts || []);
      }
      const fhirRes = await fetch(`${API_BASE}/api/emr-payload/${sessionId}`);
      if (fhirRes.ok) {
        const fhirData = await fhirRes.json();
        setFhirPayload(fhirData);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendTurn = async (queryText?: string) => {
    const input = queryText !== undefined ? queryText : textInput;
    if (!input.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/voice-turn-json`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          text: input,
          language: activeLang
        })
      });

      if (res.ok) {
        const data: PipelineTurnResult = await res.json();
        setTurnResult(data);
        setTextInput('');

        // Speak output if browser audio is supported
        if (typeof window !== 'undefined' && 'speechSynthesis' in window && data.response_text) {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(data.response_text);
          utterance.lang = data.language.startsWith('hi') || anyDevanagari(data.response_text) ? 'hi-IN' : 'en-IN';
          window.speechSynthesis.speak(utterance);
        }

        if (data.safety_escalated) {
          fetchAlertsAndFhir();
        }
      }
    } catch (e) {
      console.error('API Call Failed:', e);
      alert('Backend API connection failed. Ensure python main.py is running on http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  const handlePurgeSession = async () => {
    try {
      await fetch(`${API_BASE}/api/session/${sessionId}`, { method: 'DELETE' });
      setTurnResult(null);
      setAlerts([]);
      setFhirPayload(null);
      alert(`Session ${sessionId} state purged from memory.`);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <main style={{ maxWidth: '880px', margin: '0 auto', padding: '36px 20px 80px 20px' }}>

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
            NCD Care & Lifestyle Guidance • Medtronic Labs Challenge
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
          </div>

        </div>
      </header>

      {/* ========================================================================= */}
      {/* 1. PATIENT VIEW (DEFAULT — Grounded Rural High-Legibility Light Surface)  */}
      {/* ========================================================================= */}
      {mode === 'patient' && (
        <div>

          {/* Emergency Escalation Overlay Card */}
          {turnResult && turnResult.safety_escalated ? (
            <div className="vda-emergency-card" style={{ marginBottom: '36px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#B23A24" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#B23A24', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Emergency Warning / आपातकालीन चेतावनी
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 700, color: '#3A2E28', marginTop: '4px', marginBottom: '12px' }}>
                    Immediate Hospital Care Required
                  </div>
                  <p style={{ fontSize: '15px', color: '#3A2E28', lineHeight: '1.6', marginBottom: '20px' }}>
                    {turnResult.response_text}
                  </p>

                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <a href="tel:108" className="vda-call-btn">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                      </svg>
                      Call Ambulance (108 / 102)
                    </a>
                    <span style={{ fontSize: '13px', color: '#6B5D53', fontWeight: 500 }}>
                      Clinician Alert Dispatched ✓
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Normal Spoken Response Display */
            turnResult && (
              <div className="vda-card" style={{ padding: '24px', marginBottom: '36px', borderColor: '#E1EDE4', background: '#F3EBDC' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 700, color: '#4C7A5E', textTransform: 'uppercase' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    </svg>
                    VDA Care & Lifestyle Guidance / स्वास्थ्य सलाह
                  </div>
                  {turnResult.sources.length > 0 && (
                    <span style={{ fontSize: '11px', color: '#6B5D53', background: '#EDE4D3', padding: '2px 8px', borderRadius: '6px' }}>
                      {turnResult.intent.includes('UC2') ? 'UC2 Lifestyle (WHO HEARTS / ICMR)' : 'UC1 Adherence (ICMR / MoHFW)'}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: '#3A2E28', lineHeight: '1.6' }}>
                  "{turnResult.response_text}"
                </div>
              </div>
            )
          )}

          {/* Core Interactive Mic Focal Area */}
          <div className="vda-card" style={{ padding: '48px 24px', textAlign: 'center', marginBottom: '32px' }}>

            {/* Language Selector */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '32px' }}>
              <button
                onClick={() => setActiveLang('hi-IN')}
                style={{
                  padding: '8px 18px', borderRadius: '10px', fontSize: '14px', fontWeight: 600, border: 'none',
                  cursor: 'pointer', background: activeLang === 'hi-IN' ? '#B8456B' : '#EDE4D3',
                  color: activeLang === 'hi-IN' ? '#FFFFFF' : '#6B5D53'
                }}
              >
                हिंदी (Hindi)
              </button>
              <button
                onClick={() => setActiveLang('en-IN')}
                style={{
                  padding: '8px 18px', borderRadius: '10px', fontSize: '14px', fontWeight: 600, border: 'none',
                  cursor: 'pointer', background: activeLang === 'en-IN' ? '#B8456B' : '#EDE4D3',
                  color: activeLang === 'en-IN' ? '#FFFFFF' : '#6B5D53'
                }}
              >
                English
              </button>
            </div>

            {/* Dominant Mic Button */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
              <button
                onClick={toggleRecording}
                className={`vda-mic-btn ${isRecording ? 'vda-mic-btn-recording' : ''}`}
                aria-label="Tap to speak"
              >
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </button>

              <div style={{ fontSize: '16px', fontWeight: 600, color: '#3A2E28' }}>
                {isRecording ? 'Listening... बोलिए' : 'Tap to speak / बोलकर सवाल पूछें'}
              </div>
            </div>

            {/* Direct Input Field */}
            <div style={{ display: 'flex', gap: '10px', maxWidth: '520px', margin: '0 auto' }}>
              <input
                type="text"
                placeholder={activeLang === 'hi-IN' ? 'अपनी बीमारी, नमक, या दवाई का सवाल लिखें...' : 'Ask about medication, salt intake, or exercise...'}
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendTurn()}
                style={{
                  flex: 1, padding: '14px 18px', borderRadius: '12px', background: '#FFFFFF',
                  border: '1px solid #DED5C2', color: '#3A2E28', fontSize: '15px', outline: 'none'
                }}
              />
              <button
                onClick={() => handleSendTurn()}
                disabled={loading}
                style={{
                  padding: '14px 22px', borderRadius: '12px', background: '#B8456B',
                  color: '#FFFFFF', border: 'none', fontWeight: 600, fontSize: '15px', cursor: 'pointer'
                }}
              >
                {loading ? 'Asking...' : 'Ask'}
              </button>
            </div>

          </div>

          {/* Scenario Chips for UC1 & UC2 Live Navigation */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#8C7D72', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Demo Test Scenarios (UC1 Adherence & UC2 Lifestyle)
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
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.5 20.5l10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7z" /><line x1="8.5" y1="8.5" x2="15.5" y2="15.5" /></svg>
                UC1: BP Medicine Schedule
              </button>
              <button
                onClick={() => handleSendTurn('Am I eligible for Ayushman Bharat PM-JAY 5 Lakh free hospital card?')}
                className="vda-chip"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
                UC2: Ayushman Bharat Scheme Check
              </button>
              <button
                onClick={() => handleSendTurn('Where is the nearest PHC hospital or Sub-Centre in Doddaballapura or Nelamangala?')}
                className="vda-chip"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                UC3: Nearest HWC / PHC Facility (Bengaluru Rural)
              </button>
              <button
                onClick={() => handleSendTurn('Who won the IPL cricket match yesterday?')}
                className="vda-chip"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="4.93" y1="4.93" x2="19.07" y2="19.07" /></svg>
                Out-of-Scope Query
              </button>
            </div>
          </div>

        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. INSPECTOR MODE (Secondary Developer & Evaluator Panel)                  */}
      {/* ========================================================================= */}
      {mode === 'inspector' && (
        <div className="inspector-panel">

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #2a2e38' }}>
            <div>
              <h3 style={{ fontSize: '16px', color: '#38bdf8', fontWeight: 700 }}>
                INSPECTOR MODE — EVALUATOR TELEMETRY
              </h3>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                Active Provider: <span style={{ color: '#f43f5e', fontWeight: 600 }}>{provider.toUpperCase()}</span> • Active Use Cases: <span style={{ color: '#34d399', fontWeight: 600 }}>UC1 (Adherence) & UC2 (Lifestyle)</span>
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
