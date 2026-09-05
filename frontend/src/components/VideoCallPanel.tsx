// import { useCallback, useEffect, useRef, useState } from 'react'
// import { Button } from './ui/Button'
// import { api } from '../lib/api'

// type Phase = 'idle' | 'call' | 'wrapup' | 'done'

// interface VideoCallPanelProps {
//   roomName: string
//   displayName: string
//   bookingId: string
//   onSummarySaved?: () => void
// }

// /** Public Jitsi servers that still allow anonymous rooms (meet.jit.si no longer does). */
// const JITSI_HOSTS = ['meet.ffmuc.net', 'jitsi.riot.im', 'meet.mayfirst.org']

// type SpeechRec = {
//   continuous: boolean
//   interimResults: boolean
//   lang: string
//   onresult: ((ev: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null
//   onerror: ((ev: { error?: string }) => void) | null
//   onend: (() => void) | null
//   start: () => void
//   stop: () => void
// }

// declare global {
//   interface Window {
//     JitsiMeetExternalAPI?: new (domain: string, options: Record<string, unknown>) => {
//       dispose: () => void
//       executeCommand: (command: string, ...args: unknown[]) => void
//       addListener: (event: string, listener: (...args: unknown[]) => void) => void
//     }
//     webkitSpeechRecognition?: new () => SpeechRec
//     SpeechRecognition?: new () => SpeechRec
//   }
// }

// function loadJitsiApi(domain: string): Promise<void> {
//   if (window.JitsiMeetExternalAPI) return Promise.resolve()
//   return new Promise((resolve, reject) => {
//     const existing = document.querySelector<HTMLScriptElement>(`script[data-jitsi-domain="${domain}"]`)
//     if (existing) {
//       existing.addEventListener('load', () => resolve())
//       existing.addEventListener('error', () => reject(new Error('Jitsi script failed')))
//       return
//     }
//     const script = document.createElement('script')
//     script.src = `https://${domain}/external_api.js`
//     script.async = true
//     script.dataset.jitsiDomain = domain
//     script.onload = () => resolve()
//     script.onerror = () => reject(new Error(`Could not load video from ${domain}`))
//     document.head.appendChild(script)
//   })
// }

// export function VideoCallPanel({ roomName, displayName, bookingId, onSummarySaved }: VideoCallPanelProps) {
//   const [phase, setPhase] = useState<Phase>('idle')
//   const [lineCount, setLineCount] = useState(0)
//   const [livePreview, setLivePreview] = useState('')
//   const [notes, setNotes] = useState('')
//   const [summary, setSummary] = useState<Record<string, unknown> | null>(null)
//   const [loading, setLoading] = useState(false)
//   const [error, setError] = useState('')
//   const [speechSupported, setSpeechSupported] = useState(true)
//   const [speechStatus, setSpeechStatus] = useState('Waiting for microphone…')
//   const [callStatus, setCallStatus] = useState('Connecting…')
//   const callStartRef = useRef(0)
//   const inCallRef = useRef(false)
//   const localLinesRef = useRef<string[]>([])
//   const recRef = useRef<SpeechRec | null>(null)
//   const jitsiApiRef = useRef<{ dispose: () => void } | null>(null)
//   const meetNodeRef = useRef<HTMLDivElement | null>(null)
//   const hostIndexRef = useRef(0)
//   const startSpeechRef = useRef<() => void>(() => {})

//   const safeRoom = roomName.replace(/[^a-zA-Z0-9-]/g, '')
//   const safeName = displayName.replace(/[<>"'\\]/g, '').slice(0, 60) || 'MediCure user'

//   const pushLine = useCallback(async (text: string, tsMs: number) => {
//     const cleaned = text.trim()
//     if (cleaned.length < 2) return
//     const line = `${displayName}: ${cleaned}`
//     localLinesRef.current.push(line)
//     setLineCount(localLinesRef.current.length)
//     setLivePreview(prev => (prev ? `${prev}\n${line}` : line))
//     setSpeechStatus('Listening…')
//     try {
//       await api.appendTranscriptLine(bookingId, displayName, cleaned, tsMs)
//     } catch {
//       /* keep local copy even if sync fails */
//     }
//   }, [bookingId, displayName])

//   const stopSpeech = useCallback(() => {
//     const rec = recRef.current
//     recRef.current = null
//     if (!rec) return
//     rec.onend = null
//     rec.onerror = null
//     rec.onresult = null
//     try { rec.stop() } catch { /* already stopped */ }
//   }, [])

//   const startSpeech = useCallback(() => {
//     stopSpeech()
//     const SR = window.SpeechRecognition || window.webkitSpeechRecognition
//     if (!SR) {
//       setSpeechSupported(false)
//       setSpeechStatus('This browser cannot capture speech — type notes after the call (Chrome works best)')
//       return
//     }
//     const rec = new SR()
//     rec.continuous = true
//     rec.interimResults = true
//     rec.lang = 'en-IN'
//     rec.onresult = event => {
//       for (let i = event.resultIndex; i < event.results.length; i++) {
//         const result = event.results[i]
//         const tx = result[0]?.transcript?.trim() || ''
//         if (!tx) continue
//         if (result.isFinal) {
//           void pushLine(tx, Date.now() - callStartRef.current)
//         } else {
//           setSpeechStatus(`Hearing: “${tx.slice(0, 80)}”`)
//         }
//       }
//     }
//     rec.onerror = event => {
//       const err = event.error || 'unknown'
//       if (err === 'not-allowed') {
//         setSpeechSupported(false)
//         setSpeechStatus('Microphone blocked — allow mic access and rejoin, or type notes after the call')
//         return
//       }
//       if (err === 'no-speech' || err === 'aborted') return
//       setSpeechStatus(`Speech paused (${err}) — still listening…`)
//     }
//     rec.onend = () => {
//       if (!inCallRef.current || recRef.current !== rec) return
//       window.setTimeout(() => {
//         if (!inCallRef.current || recRef.current !== rec) return
//         try { rec.start() } catch { /* ignore */ }
//       }, 400)
//     }
//     recRef.current = rec
//     try {
//       rec.start()
//       setSpeechSupported(true)
//       setSpeechStatus('Listening — speak clearly near your microphone')
//     } catch {
//       setSpeechSupported(false)
//       setSpeechStatus('Could not start speech capture — type notes after the call')
//     }
//   }, [pushLine, stopSpeech])

//   startSpeechRef.current = startSpeech

//   useEffect(() => {
//     api.getMeetSummary(bookingId)
//       .then(res => {
//         if (res.summary) {
//           setSummary(res.summary)
//           setPhase('done')
//         }
//       })
//       .catch(() => {})
//   }, [bookingId])

//   useEffect(() => {
//     if (phase !== 'call') return
//     const timer = window.setInterval(() => {
//       api.getTranscript(bookingId)
//         .then(remote => {
//           if (!inCallRef.current) return
//           if (remote.count > localLinesRef.current.length && remote.formatted) {
//             setLivePreview(remote.formatted)
//             setLineCount(remote.count)
//           }
//         })
//         .catch(() => {})
//     }, 4000)
//     return () => window.clearInterval(timer)
//   }, [phase, bookingId])

//   useEffect(() => {
//     if (phase !== 'call') return
//     let cancelled = false
//     const container = meetNodeRef.current
//     if (!container) return

//     const startHost = async (index: number) => {
//       const domain = JITSI_HOSTS[index]
//       hostIndexRef.current = index
//       setCallStatus(`Connecting to ${domain}…`)
//       container.replaceChildren()
//       try {
//         document.querySelectorAll('script[data-jitsi-domain]').forEach(el => el.remove())
//         await loadJitsiApi(domain)
//         const JitsiCtor = window.JitsiMeetExternalAPI
//         if (cancelled || !JitsiCtor) throw new Error('Video API missing')
//         const apiInstance = new JitsiCtor(domain, {
//           roomName: safeRoom,
//           parentNode: container,
//           width: '100%',
//           height: 420,
//           userInfo: { displayName: safeName },
//           configOverwrite: {
//             prejoinPageEnabled: false,
//             prejoinConfig: { enabled: false },
//             startWithAudioMuted: false,
//             startWithVideoMuted: false,
//             disableDeepLinking: true,
//             enableWelcomePage: false,
//             requireDisplayName: false,
//             enableLobby: false,
//             hideConferenceSubject: true,
//             disableInviteFunctions: true,
//             analytics: { disabled: true },
//             p2p: { enabled: true },
//           },
//           interfaceConfigOverwrite: {
//             SHOW_JITSI_WATERMARK: false,
//             SHOW_BRAND_WATERMARK: false,
//             SHOW_POWERED_BY: false,
//             DISABLE_JOIN_LEAVE_NOTIFICATIONS: true,
//             HIDE_INVITE_MORE_HEADER: true,
//             TOOLBAR_BUTTONS: ['microphone', 'camera', 'hangup', 'chat', 'tileview', 'fullscreen', 'settings'],
//           },
//         })
//         jitsiApiRef.current = apiInstance
//         apiInstance.addListener('videoConferenceJoined', () => {
//           if (cancelled) return
//           setCallStatus('In call — no login needed')
//           startSpeechRef.current()
//         })
//         apiInstance.addListener('participantJoined', () => {
//           if (!cancelled) setCallStatus('In call — another participant joined')
//         })
//         apiInstance.addListener('authenticationRequired', () => {
//           if (cancelled) return
//           apiInstance.dispose()
//           jitsiApiRef.current = null
//           const next = index + 1
//           if (next < JITSI_HOSTS.length) void startHost(next)
//           else setCallStatus('Could not start a login-free room. Try Chrome and rejoin.')
//         })
//         setCallStatus('Waiting for room… speak to capture the transcript')
//       } catch {
//         const next = index + 1
//         if (!cancelled && next < JITSI_HOSTS.length) void startHost(next)
//         else if (!cancelled) setError('Could not start the video room. Check your network and try again.')
//       }
//     }

//     void startHost(0)
//     return () => {
//       cancelled = true
//       try { jitsiApiRef.current?.dispose() } catch { /* ignore */ }
//       jitsiApiRef.current = null
//     }
//   }, [phase, safeRoom, safeName])

//   const requestMicAndStart = async () => {
//     setError('')
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
//       stream.getTracks().forEach(t => t.stop())
//     } catch {
//       setSpeechSupported(false)
//       setSpeechStatus('Microphone permission denied — you can still type notes after the call')
//     }
//     localLinesRef.current = []
//     callStartRef.current = Date.now()
//     setLineCount(0)
//     setLivePreview('')
//     setNotes('')
//     setSummary(null)
//     inCallRef.current = true
//     startSpeech()
//     setPhase('call')
//   }

//   const finishCall = async () => {
//     inCallRef.current = false
//     stopSpeech()
//     try { jitsiApiRef.current?.dispose() } catch { /* ignore */ }
//     jitsiApiRef.current = null
//     setLoading(true)
//     setError('')
//     try {
//       const remote = await api.getTranscript(bookingId)
//       const merged = remote.formatted?.trim() || localLinesRef.current.join('\n')
//       setNotes(merged)
//       setLineCount(remote.count || localLinesRef.current.length)
//       if (merged) setLivePreview(merged)
//     } catch {
//       setNotes(localLinesRef.current.join('\n'))
//     } finally {
//       setLoading(false)
//       setPhase('wrapup')
//     }
//   }

//   const generateSummary = async () => {
//     const transcript = notes.trim() || livePreview.trim() || localLinesRef.current.join('\n')
//     if (transcript.trim().length < 15) {
//       setError('Add consultation notes below (symptoms discussed, medicines prescribed, follow-up). At least one sentence.')
//       return
//     }
//     setLoading(true)
//     setError('')
//     try {
//       const result = await api.createMeetSummary(bookingId, transcript)
//       setSummary(result.summary as Record<string, unknown>)
//       setPhase('done')
//       onSummarySaved?.()
//     } catch (e) {
//       setError(e instanceof Error ? e.message : 'Failed to generate summary')
//     } finally {
//       setLoading(false)
//     }
//   }

//   if (phase === 'idle') {
//     return (
//       <div className="mt-3 p-4 bg-primary-50 dark:bg-primary-950/40 border border-primary-200 dark:border-primary-800 rounded-xl">
//         <p className="text-sm text-primary-800 dark:text-primary-200 mb-1">
//           Video room: <code className="bg-white dark:bg-slate-800 px-2 py-0.5 rounded text-xs">{safeRoom}</code>
//         </p>
//         <p className="text-xs text-slate-500 mb-3">
//           Doctor and patient join the same room. Allow the microphone — speech is captured for the AI summary. No Jitsi account or login.
//         </p>
//         <Button onClick={requestMicAndStart}>🎥 Join Video Call</Button>
//       </div>
//     )
//   }

//   if (phase === 'call') {
//     return (
//       <div className="mt-3 space-y-3 relative">
//         <div
//           ref={meetNodeRef}
//           className="w-full h-[420px] rounded-xl border-2 border-primary-500 overflow-hidden bg-slate-950"
//         />
//         <div className="p-3 portal-surface rounded-xl text-xs space-y-2">
//           <p className="text-slate-600 dark:text-slate-300">{callStatus}</p>
//           <p className="text-slate-600 dark:text-slate-300">
//             🎙 <strong>{lineCount}</strong> sentence(s) captured · {speechStatus}
//             {!speechSupported && ' · Type notes after ending the call'}
//           </p>
//           {livePreview && (
//             <div className="max-h-24 overflow-y-auto text-slate-700 dark:text-slate-200 whitespace-pre-wrap bg-white dark:bg-slate-900 rounded-lg p-2 border border-slate-100 dark:border-slate-700">
//               {livePreview}
//             </div>
//           )}
//           {!livePreview && (
//             <p className="text-slate-500">Speak clearly near your microphone. Each side captures their own speech for the summary.</p>
//           )}
//         </div>
//         <Button variant="secondary" onClick={finishCall} loading={loading}>
//           📴 End Call &amp; Generate Summary
//         </Button>
//       </div>
//     )
//   }

//   return (
//     <div className="mt-3 space-y-3">
//       {phase === 'wrapup' && (
//         <>
//           <div className="p-4 portal-banner-warning">
//             <p className="text-sm font-medium mb-2">Consultation transcript</p>
//             <p className="text-xs mb-3 opacity-90">
//               {lineCount > 0
//                 ? `${lineCount} line(s) captured from the call (doctor + patient). Edit if needed, then generate.`
//                 : 'No speech was captured automatically. Type what was discussed, then generate the summary.'}
//             </p>
//             <textarea
//               value={notes}
//               onChange={e => setNotes(e.target.value)}
//               placeholder="e.g. Patient complained of headache and fever. Doctor prescribed Paracetamol 500mg twice daily for 3 days. Advised rest and follow-up in 1 week."
//               className="portal-input w-full h-32 resize-none"
//             />
//           </div>
//           {error && <p className="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">{error}</p>}
//           <Button onClick={generateSummary} loading={loading} className="w-full">
//             🧠 Generate &amp; Save Summary
//           </Button>
//         </>
//       )}
//       {phase === 'done' && summary && (
//         <>
//           <SummaryCard summary={summary} />
//           <p className="text-xs text-emerald-600">✅ Saved — view in Consultation Summaries tab</p>
//         </>
//       )}
//     </div>
//   )
// }

// function SummaryCard({ summary }: { summary: Record<string, unknown> }) {
//   const sufferings = summary.sufferings as string[] | undefined
//   const medicines = summary.medicines_recommended as { medicine?: string; dose?: string; frequency?: string; duration?: string }[] | undefined

//   return (
//     <div className="p-4 bg-violet-50 dark:bg-violet-950/40 border border-violet-200 dark:border-violet-800 rounded-xl text-sm space-y-3 text-slate-800 dark:text-slate-200">
//       <h4 className="font-semibold text-violet-900 dark:text-violet-200">🧠 Consultation Summary</h4>
//       {summary.conclusion ? <p><strong>Conclusion:</strong> {String(summary.conclusion)}</p> : null}
//       {summary.disease ? <p><strong>Disease:</strong> {String(summary.disease)}</p> : null}
//       {sufferings?.length ? <p><strong>Sufferings:</strong> {sufferings.join(', ')}</p> : null}
//       {medicines?.length ? (
//         <div>
//           <strong>Medicines:</strong>
//           <ul className="list-disc ml-5 mt-1">
//             {medicines.map((m, i) => (
//               <li key={i}>{m.medicine} — {[m.dose, m.frequency, m.duration].filter(Boolean).join(' · ')}</li>
//             ))}
//           </ul>
//         </div>
//       ) : null}
//       {summary.medicine_changes ? <p><strong>Medicine changes:</strong> {String(summary.medicine_changes)}</p> : null}
//       {summary.follow_up ? <p><strong>Follow-up:</strong> {String(summary.follow_up)}</p> : null}
//     </div>
//   )
// }


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

/** Public Jitsi servers that still allow anonymous rooms (meet.jit.si no longer does). */
const JITSI_HOSTS = ['meet.ffmuc.net', 'jitsi.riot.im', 'meet.mayfirst.org']

type SpeechRec = {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((ev: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null
  onerror: ((ev: { error?: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

declare global {
  interface Window {
    JitsiMeetExternalAPI?: new (domain: string, options: Record<string, unknown>) => {
      dispose: () => void
      executeCommand: (command: string, ...args: unknown[]) => void
      addListener: (event: string, listener: (...args: unknown[]) => void) => void
    }
    webkitSpeechRecognition?: new () => SpeechRec
    SpeechRecognition?: new () => SpeechRec
  }
}

function loadJitsiApi(domain: string): Promise<void> {
  if (window.JitsiMeetExternalAPI) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[data-jitsi-domain="${domain}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Jitsi script failed')))
      return
    }
    const script = document.createElement('script')
    script.src = `https://${domain}/external_api.js`
    script.async = true
    script.dataset.jitsiDomain = domain
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`Could not load video from ${domain}`))
    document.head.appendChild(script)
  })
}

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
  const [callStatus, setCallStatus] = useState('Connecting…')
  const [selectedLang, setSelectedLang] = useState('hi-IN')
  const callStartRef = useRef(0)
  const inCallRef = useRef(false)
  const localLinesRef = useRef<string[]>([])
  const recRef = useRef<SpeechRec | null>(null)
  const jitsiApiRef = useRef<{ dispose: () => void } | null>(null)
  const meetNodeRef = useRef<HTMLDivElement | null>(null)
  const hostIndexRef = useRef(0)
  // flag so we only ever start speech once per call
  const speechStartedRef = useRef(false)

  const safeRoom = roomName.replace(/[^a-zA-Z0-9-]/g, '')
  const safeName = displayName.replace(/[<>"'\\]/g, '').slice(0, 60) || 'MediCure user'

  const pushLine = useCallback(async (text: string, tsMs: number) => {
    const cleaned = text.trim()
    if (cleaned.length < 2) return
    const line = `${displayName}: ${cleaned}`
    localLinesRef.current.push(line)
    setLineCount(localLinesRef.current.length)
    setLivePreview(prev => (prev ? `${prev}\n${line}` : line))
    setSpeechStatus('Listening…')
    try {
      await api.appendTranscriptLine(bookingId, displayName, cleaned, tsMs)
    } catch {
      /* keep local copy even if sync fails */
    }
  }, [bookingId, displayName])

  const stopSpeech = useCallback(() => {
    const rec = recRef.current
    recRef.current = null
    if (!rec) return
    rec.onend = null
    rec.onerror = null
    rec.onresult = null
    try { rec.stop() } catch { /* already stopped */ }
  }, [])

  // FIX 1: startSpeech is now a plain function stored in a ref, not a useCallback.
  // This avoids stale closure issues and the double-start problem.
  const startSpeech = useCallback(() => {
    // FIX 2: Guard — only start speech once per call session
    if (speechStartedRef.current) return
    speechStartedRef.current = true

    stopSpeech()

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      setSpeechSupported(false)
      setSpeechStatus('This browser cannot capture speech — type notes after the call (Chrome works best)')
      return
    }

    const rec = new SR()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = selectedLang

    rec.onresult = event => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const tx = result[0]?.transcript?.trim() || ''
        if (!tx) continue
        if (result.isFinal) {
          void pushLine(tx, Date.now() - callStartRef.current)
        } else {
          setSpeechStatus(`Hearing: "${tx.slice(0, 80)}"`)
        }
      }
    }

    rec.onerror = event => {
      const err = event.error || 'unknown'
      if (err === 'not-allowed') {
        setSpeechSupported(false)
        setSpeechStatus('Microphone blocked — allow mic access and rejoin, or type notes after the call')
        return
      }
      if (err === 'language-not-supported') {
        // Fallback to en-US if selected language isn't available on this device
        try { rec.lang = 'en-US'; rec.start() } catch { /* ignore */ }
        return
      }
      if (err === 'no-speech' || err === 'aborted') return
      setSpeechStatus(`Speech paused (${err}) — still listening…`)
    }

    // FIX 5: onend restart — use a simple inCallRef check, no instance comparison
    rec.onend = () => {
      if (!inCallRef.current) return
      window.setTimeout(() => {
        if (!inCallRef.current) return
        try { rec.start() } catch { /* ignore */ }
      }, 300)
    }

    recRef.current = rec
    try {
      rec.start()
      setSpeechSupported(true)
      setSpeechStatus('Listening — speak clearly near your microphone')
    } catch {
      setSpeechSupported(false)
      setSpeechStatus('Could not start speech capture — type notes after the call')
    }
  }, [pushLine, stopSpeech])

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

  useEffect(() => {
    if (phase !== 'call') return
    const timer = window.setInterval(() => {
      api.getTranscript(bookingId)
        .then(remote => {
          if (!inCallRef.current) return
          if (remote.count > localLinesRef.current.length && remote.formatted) {
            setLivePreview(remote.formatted)
            setLineCount(remote.count)
          }
        })
        .catch(() => {})
    }, 4000)
    return () => window.clearInterval(timer)
  }, [phase, bookingId])

  useEffect(() => {
    if (phase !== 'call') return
    let cancelled = false
    const container = meetNodeRef.current
    if (!container) return

    const startHost = async (index: number) => {
      const domain = JITSI_HOSTS[index]
      hostIndexRef.current = index
      setCallStatus(`Connecting to ${domain}…`)
      container.replaceChildren()
      try {
        document.querySelectorAll('script[data-jitsi-domain]').forEach(el => el.remove())
        await loadJitsiApi(domain)
        const JitsiCtor = window.JitsiMeetExternalAPI
        if (cancelled || !JitsiCtor) throw new Error('Video API missing')
        const apiInstance = new JitsiCtor(domain, {
          roomName: safeRoom,
          parentNode: container,
          width: '100%',
          height: 420,
          userInfo: { displayName: safeName },
          configOverwrite: {
            prejoinPageEnabled: false,
            prejoinConfig: { enabled: false },
            startWithAudioMuted: false,
            startWithVideoMuted: false,
            disableDeepLinking: true,
            enableWelcomePage: false,
            requireDisplayName: false,
            enableLobby: false,
            hideConferenceSubject: true,
            disableInviteFunctions: true,
            analytics: { disabled: true },
            p2p: { enabled: true },
          },
          interfaceConfigOverwrite: {
            SHOW_JITSI_WATERMARK: false,
            SHOW_BRAND_WATERMARK: false,
            SHOW_POWERED_BY: false,
            DISABLE_JOIN_LEAVE_NOTIFICATIONS: true,
            HIDE_INVITE_MORE_HEADER: true,
            TOOLBAR_BUTTONS: ['microphone', 'camera', 'hangup', 'chat', 'tileview', 'fullscreen', 'settings'],
          },
        })
        jitsiApiRef.current = apiInstance
        apiInstance.addListener('videoConferenceJoined', () => {
          if (cancelled) return
          setCallStatus('In call — no login needed')
          // FIX 6: startSpeech guard ensures this is a no-op if already started
          startSpeech()
        })
        apiInstance.addListener('participantJoined', () => {
          if (!cancelled) setCallStatus('In call — another participant joined')
        })
        apiInstance.addListener('authenticationRequired', () => {
          if (cancelled) return
          apiInstance.dispose()
          jitsiApiRef.current = null
          const next = index + 1
          if (next < JITSI_HOSTS.length) void startHost(next)
          else setCallStatus('Could not start a login-free room. Try Chrome and rejoin.')
        })
        setCallStatus('Waiting for room… speak to capture the transcript')
      } catch {
        const next = index + 1
        if (!cancelled && next < JITSI_HOSTS.length) void startHost(next)
        else if (!cancelled) setError('Could not start the video room. Check your network and try again.')
      }
    }

    void startHost(0)
    return () => {
      cancelled = true
      try { jitsiApiRef.current?.dispose() } catch { /* ignore */ }
      jitsiApiRef.current = null
    }
  }, [phase, safeRoom, safeName, startSpeech])

  const requestMicAndStart = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop())
    } catch {
      setSpeechSupported(false)
      setSpeechStatus('Microphone permission denied — you can still type notes after the call')
    }
    localLinesRef.current = []
    callStartRef.current = Date.now()
    setLineCount(0)
    setLivePreview('')
    setNotes('')
    setSummary(null)
    inCallRef.current = true
    // FIX 7: Reset the speech-started guard for the new call session
    speechStartedRef.current = false
    // FIX 8: Start speech ONLY here, NOT again from videoConferenceJoined
    // (videoConferenceJoined will call startSpeech too but the guard blocks it)
    startSpeech()
    setPhase('call')
  }

  const finishCall = async () => {
    inCallRef.current = false
    stopSpeech()
    try { jitsiApiRef.current?.dispose() } catch { /* ignore */ }
    jitsiApiRef.current = null
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
          Doctor and patient join the same room. Allow the microphone — speech is captured for the AI summary. No Jitsi account or login.
        </p>
        <div className="mb-3">
          <label className="text-xs text-slate-600 dark:text-slate-400 block mb-1">🎙 Speech language</label>
          <select
            value={selectedLang}
            onChange={e => setSelectedLang(e.target.value)}
            className="portal-input text-sm w-full"
          >
            <option value="hi-IN">Hindi / हिंदी (captures Hindi + English mix best)</option>
            <option value="en-IN">English — Indian accent</option>
            <option value="pa-IN">Punjabi / ਪੰਜਾਬੀ</option>
            <option value="en-US">English — US (most reliable fallback)</option>
          </select>
          <p className="text-xs text-slate-400 mt-1">Hindi mode works best for mixed Hindi-English conversations. Each person picks on their own device.</p>
        </div>
        <Button onClick={requestMicAndStart}>🎥 Join Video Call</Button>
      </div>
    )
  }

  if (phase === 'call') {
    return (
      <div className="mt-3 space-y-3 relative">
        <div
          ref={meetNodeRef}
          className="w-full h-[420px] rounded-xl border-2 border-primary-500 overflow-hidden bg-slate-950"
        />
        <div className="p-3 portal-surface rounded-xl text-xs space-y-2">
          <p className="text-slate-600 dark:text-slate-300">{callStatus}</p>
          <p className="text-slate-600 dark:text-slate-300">
            🎙 <strong>{lineCount}</strong> sentence(s) captured · {speechStatus}
            {!speechSupported && ' · Type notes after ending the call'}
          </p>
          {livePreview && (
            <div className="max-h-24 overflow-y-auto text-slate-700 dark:text-slate-200 whitespace-pre-wrap bg-white dark:bg-slate-900 rounded-lg p-2 border border-slate-100 dark:border-slate-700">
              {livePreview}
            </div>
          )}
          {!livePreview && (
            <p className="text-slate-500">Speak clearly near your microphone. Each side captures their own speech for the summary.</p>
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
                : 'No speech was captured automatically. Type what was discussed, then generate the summary.'}
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
