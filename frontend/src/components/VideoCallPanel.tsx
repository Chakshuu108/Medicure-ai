import { useCallback, useEffect, useRef, useState } from 'react'
import { Button } from './ui/Button'
import { api } from '../lib/api'

type Phase = 'idle' | 'call' | 'wrapup' | 'done'

interface VideoCallPanelProps {
  roomName: string
  displayName: string
  bookingId: string
  onSummarySaved?: () => void
}

const SPEECH_IFRAME_HTML = `<!DOCTYPE html>
<html><head><style>body{margin:0;padding:0;overflow:hidden;background:transparent;height:1px;}</style></head>
<body><script>
(function(){
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { parent.postMessage({type:'speech-status', supported:false}, '*'); return; }
  parent.postMessage({type:'speech-status', supported:true}, '*');
  var t0 = Date.now();
  var r = new SR();
  r.continuous = true;
  r.interimResults = true;
  r.lang = 'en-IN';
  r.onresult = function(e) {
    for (var i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        var tx = e.results[i][0].transcript.trim();
        if (tx.length > 1) parent.postMessage({type:'speech-line', text:tx, ts_ms:Date.now()-t0}, '*');
      }
    }
  };
  r.onerror = function(e) {
    parent.postMessage({type:'speech-error', error:e.error||'unknown'}, '*');
    if (e.error !== 'no-speech' && e.error !== 'aborted')
      setTimeout(function(){ try { r.start(); } catch(x) {} }, 1500);
  };
  r.onend = function() {
    setTimeout(function(){ try { r.start(); } catch(x) {} }, 400);
  };
  try { r.start(); } catch(x) { parent.postMessage({type:'speech-status', supported:false}, '*'); }
})();
</script></body></html>`

export function VideoCallPanel({ roomName, displayName, bookingId, onSummarySaved }: VideoCallPanelProps) {
  const [phase, setPhase] = useState<Phase>('idle')
  const [lineCount, setLineCount] = useState(0)
  const [livePreview, setLivePreview] = useState('')
  const [notes, setNotes] = useState('')
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [speechSupported, setSpeechSupported] = useState(true)
  const [speechStatus, setSpeechStatus] = useState('Waiting for microphone…')
  const [micReady, setMicReady] = useState(false)
  const callStartRef = useRef(0)
  const inCallRef = useRef(false)
  const localLinesRef = useRef<string[]>([])
  const micStreamRef = useRef<MediaStream | null>(null)
  const [jitsiReady, setJitsiReady] = useState(false)

  const safeRoom = roomName.replace(/[^a-zA-Z0-9-]/g, '')
  const jitsiUrl = `https://meet.jit.si/${safeRoom}#userInfo.displayName="${encodeURIComponent(displayName)}"&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false`

  useEffect(() => {
    api.getMeetSummary(bookingId)
      .then(res => {
        if (res.summary) {
          setSummary(res.summary)
          setPhase('done')
        }
      })
      .catch(() => {})
  }, [bookingId])

  const pushLine = useCallback(async (text: string, tsMs: number) => {
    const line = `${displayName}: ${text}`
    localLinesRef.current.push(line)
    setLineCount(localLinesRef.current.length)
    setLivePreview(prev => (prev ? `${prev}\n${line}` : line))
    setSpeechStatus('Listening…')
    try {
      await api.appendTranscriptLine(bookingId, displayName, text, tsMs)
    } catch {
      /* keep local copy even if sync fails */
    }
  }, [bookingId, displayName])

  useEffect(() => {
    if (phase !== 'call') {
      setJitsiReady(false)
      return
    }
    const timer = window.setTimeout(() => setJitsiReady(true), 1200)
    return () => window.clearTimeout(timer)
  }, [phase])

  useEffect(() => {
    return () => {
      micStreamRef.current?.getTracks().forEach(t => t.stop())
      micStreamRef.current = null
    }
  }, [])

  useEffect(() => {
    if (phase !== 'call') return
    inCallRef.current = true

    const onMessage = (event: MessageEvent) => {
      if (!inCallRef.current || !event.data || typeof event.data !== 'object') return
      const data = event.data as { type?: string; text?: string; ts_ms?: number; supported?: boolean; error?: string }
      if (data.type === 'speech-status') {
        setSpeechSupported(data.supported !== false)
        if (data.supported === false) setSpeechStatus('Speech capture unavailable — type notes after the call')
        return
      }
      if (data.type === 'speech-error') {
        if (data.error === 'not-allowed') {
          setSpeechStatus('Microphone blocked — allow mic access and rejoin, or type notes after the call')
          setSpeechSupported(false)
        } else if (data.error !== 'no-speech' && data.error !== 'aborted') {
          setSpeechStatus(`Speech paused (${data.error}) — still listening…`)
        }
        return
      }
      if (data.type === 'speech-line' && data.text) {
        void pushLine(data.text, data.ts_ms ?? Date.now() - callStartRef.current)
      }
    }

    window.addEventListener('message', onMessage)
    return () => {
      inCallRef.current = false
      window.removeEventListener('message', onMessage)
    }
  }, [phase, pushLine])

  const requestMicAndStart = async () => {
    setError('')
    try {
      micStreamRef.current?.getTracks().forEach(t => t.stop())
      micStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true })
      setMicReady(true)
      setSpeechStatus('Microphone ready — starting speech capture…')
    } catch {
      setMicReady(false)
      setSpeechSupported(false)
      setSpeechStatus('Microphone permission denied — you can still type notes after the call')
    }
    localLinesRef.current = []
    callStartRef.current = Date.now()
    setLineCount(0)
    setLivePreview('')
    setNotes('')
    setSummary(null)
    setPhase('call')
  }

  const finishCall = async () => {
    inCallRef.current = false
    micStreamRef.current?.getTracks().forEach(t => t.stop())
    micStreamRef.current = null
    setLoading(true)
    setError('')
    try {
      const remote = await api.getTranscript(bookingId)
      const merged = remote.formatted?.trim() || localLinesRef.current.join('\n')
      setNotes(merged)
      setLineCount(remote.count || localLinesRef.current.length)
      if (merged) setLivePreview(merged)
    } catch {
      setNotes(localLinesRef.current.join('\n'))
    } finally {
      setLoading(false)
      setPhase('wrapup')
    }
  }

  const generateSummary = async () => {
    const transcript = notes.trim() || livePreview.trim() || localLinesRef.current.join('\n')
    if (transcript.trim().length < 15) {
      setError('Add consultation notes below (symptoms discussed, medicines prescribed, follow-up). At least one sentence.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await api.createMeetSummary(bookingId, transcript)
      setSummary(result.summary as Record<string, unknown>)
      setPhase('done')
      onSummarySaved?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate summary')
    } finally {
      setLoading(false)
    }
  }

  if (phase === 'idle') {
    return (
      <div className="mt-3 p-4 bg-primary-50 dark:bg-primary-950/40 border border-primary-200 dark:border-primary-800 rounded-xl">
        <p className="text-sm text-primary-800 dark:text-primary-200 mb-1">
          Video room: <code className="bg-white dark:bg-slate-800 px-2 py-0.5 rounded text-xs">{safeRoom}</code>
        </p>
        <p className="text-xs text-slate-500 mb-3">
          Doctor and patient must join the same room. Allow microphone when prompted — speech is captured for the AI summary.
        </p>
        <Button onClick={requestMicAndStart}>🎥 Join Video Call</Button>
      </div>
    )
  }

  if (phase === 'call') {
    return (
      <div className="mt-3 space-y-3 relative">
        <iframe
          srcDoc={SPEECH_IFRAME_HTML}
          title="Speech capture"
          className="w-0 h-0 border-0 opacity-0 pointer-events-none absolute"
          allow="microphone"
        />
        {jitsiReady ? (
          <iframe
            src={jitsiUrl}
            allow="camera; microphone; display-capture; fullscreen; autoplay"
            className="w-full h-[420px] rounded-xl border-2 border-primary-500"
            title="Jitsi video call"
          />
        ) : (
          <div className="w-full h-[420px] rounded-xl border-2 border-primary-500 bg-slate-900 flex items-center justify-center text-white text-sm">
            Starting speech capture…
          </div>
        )}
        <div className="p-3 portal-surface rounded-xl text-xs space-y-2">
          <p className="text-slate-600 dark:text-slate-300">
            🎙 <strong>{lineCount}</strong> sentence(s) captured · {speechStatus}
            {!speechSupported && ' · Type notes after ending the call'}
          </p>
          {livePreview && (
            <div className="max-h-24 overflow-y-auto text-slate-700 dark:text-slate-200 whitespace-pre-wrap bg-white dark:bg-slate-900 rounded-lg p-2 border border-slate-100 dark:border-slate-700">
              {livePreview}
            </div>
          )}
          {!livePreview && micReady && (
            <p className="text-slate-500">Speak clearly near your microphone. Both sides&apos; speech is saved to the consultation transcript.</p>
          )}
        </div>
        <Button variant="secondary" onClick={finishCall} loading={loading}>
          📴 End Call &amp; Generate Summary
        </Button>
      </div>
    )
  }

  return (
    <div className="mt-3 space-y-3">
      {phase === 'wrapup' && (
        <>
          <div className="p-4 portal-banner-warning">
            <p className="text-sm font-medium mb-2">Consultation transcript</p>
            <p className="text-xs mb-3 opacity-90">
              {lineCount > 0
                ? `${lineCount} line(s) captured from the call (doctor + patient). Edit if needed, then generate.`
                : 'No speech was captured. Type what was discussed in the consultation below.'}
            </p>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Patient complained of headache and fever. Doctor prescribed Paracetamol 500mg twice daily for 3 days. Advised rest and follow-up in 1 week."
              className="portal-input w-full h-32 resize-none"
            />
          </div>
          {error && <p className="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">{error}</p>}
          <Button onClick={generateSummary} loading={loading} className="w-full">
            🧠 Generate &amp; Save Summary
          </Button>
        </>
      )}
      {phase === 'done' && summary && (
        <>
          <SummaryCard summary={summary} />
          <p className="text-xs text-emerald-600">✅ Saved — view in Consultation Summaries tab</p>
        </>
      )}
    </div>
  )
}

function SummaryCard({ summary }: { summary: Record<string, unknown> }) {
  const sufferings = summary.sufferings as string[] | undefined
  const medicines = summary.medicines_recommended as { medicine?: string; dose?: string; frequency?: string; duration?: string }[] | undefined

  return (
    <div className="p-4 bg-violet-50 dark:bg-violet-950/40 border border-violet-200 dark:border-violet-800 rounded-xl text-sm space-y-3 text-slate-800 dark:text-slate-200">
      <h4 className="font-semibold text-violet-900 dark:text-violet-200">🧠 Consultation Summary</h4>
      {summary.conclusion ? <p><strong>Conclusion:</strong> {String(summary.conclusion)}</p> : null}
      {summary.disease ? <p><strong>Disease:</strong> {String(summary.disease)}</p> : null}
      {sufferings?.length ? <p><strong>Sufferings:</strong> {sufferings.join(', ')}</p> : null}
      {medicines?.length ? (
        <div>
          <strong>Medicines:</strong>
          <ul className="list-disc ml-5 mt-1">
            {medicines.map((m, i) => (
              <li key={i}>{m.medicine} — {[m.dose, m.frequency, m.duration].filter(Boolean).join(' · ')}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {summary.medicine_changes ? <p><strong>Medicine changes:</strong> {String(summary.medicine_changes)}</p> : null}
      {summary.follow_up ? <p><strong>Follow-up:</strong> {String(summary.follow_up)}</p> : null}
    </div>
  )
}
