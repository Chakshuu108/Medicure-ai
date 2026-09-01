"""
meet_ui.py — Video call + fully automated speech transcription + AI summary.

Summary trigger flow (fixed):
  - Jitsi fires readyToClose/videoConferenceLeft → JS sets hidden input to "1"
  - _auto_summary_poller fragment detects "1", calls merge_and_summarize()
  - On success: sets session_state flag "summary_ready_{slot_id}" = True
  - The fragment itself renders the summary card directly (no st.rerun() needed)
  - Both doctor and patient fragments independently poll DB and render card
"""

import time
import json
import streamlit as st


# ── Jitsi iframe HTML ─────────────────────────────────────────────────────────

def _jitsi_html(room_name: str, display_name: str, call_end_input_key: str) -> str:
    """
    Embeds Jitsi as a plain <iframe> using the direct URL approach.

    Why: Both meet.jit.si and 8x8.vc External API JS now require a registered
    JaaS account and block anonymous connections with "not allowed to join".
    The plain iframe URL (meet.jit.si/#config...) still works anonymously.

    Call-end detection: listens for postMessage events from the Jitsi iframe
    (it emits 'readyToClose' and 'hangup' messages) and also polls every 5s
    checking if the iframe src went blank (user closed). On detection writes
    "1" into the hidden Streamlit text_input via parent document access.
    """
    safe_room = "".join(c for c in room_name if c.isalnum() or c == "-")
    safe_name = display_name.replace("'", "").replace('"', "").replace("\\", "").replace("#", "")
    safe_key  = call_end_input_key.replace('"', "").replace("'", "")

    # Jitsi URL config params — all via fragment hash to skip prejoin and auth
    jitsi_url = (
        f"https://meet.jit.si/{safe_room}"
        f"#userInfo.displayName=\"{safe_name}\""
        f"&config.prejoinPageEnabled=false"
        f"&config.startWithAudioMuted=false"
        f"&config.startWithVideoMuted=false"
        f"&config.disableDeepLinking=true"
        f"&config.enableWelcomePage=false"
        f"&config.requireDisplayName=false"
        f"&config.p2p.enabled=true"
        f"&interfaceConfig.SHOW_JITSI_WATERMARK=false"
        f"&interfaceConfig.TOOLBAR_ALWAYS_VISIBLE=true"
        f"&interfaceConfig.DISABLE_JOIN_LEAVE_NOTIFICATIONS=true"
    )

    html = """<!DOCTYPE html>
<html>
<head>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#0f0f1a; width:100%; height:572px; overflow:hidden; }
  #meet-frame {
    width:100%; height:572px; border:2px solid #7C3AED;
    border-radius:12px; overflow:hidden; display:block;
  }
  #end-btn {
    position:absolute; bottom:14px; right:14px; z-index:99;
    background:#EF4444; color:#fff; border:none; border-radius:8px;
    padding:8px 18px; font-size:0.85rem; font-weight:600;
    cursor:pointer; box-shadow:0 2px 8px rgba(239,68,68,0.4);
  }
  #end-btn:hover { background:#DC2626; }
</style>
</head>
<body style="position:relative;">

<iframe
  id="meet-frame"
  src="JITSI_URL_PLACEHOLDER"
  allow="camera; microphone; display-capture; fullscreen; autoplay"
  allowfullscreen
></iframe>

<button id="end-btn" onclick="endCall()">📴 End &amp; Get Summary</button>

<script>
var ended = false;

function signalCallEnd() {
  if (ended) return;
  ended = true;
  try {
    var doc = window.parent.document;
    var els = doc.querySelectorAll("input");
    for (var i = 0; i < els.length; i++) {
      var lbl = els[i].getAttribute("aria-label") || "";
      if (lbl === "END_KEY_PLACEHOLDER") {
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        setter.call(els[i], "1");
        els[i].dispatchEvent(new Event("input", { bubbles: true }));
        break;
      }
    }
  } catch(e) {}
}

function endCall() {
  // Hide iframe so call drops
  var fr = document.getElementById("meet-frame");
  fr.src = "about:blank";
  document.getElementById("end-btn").style.display = "none";
  signalCallEnd();
}

// Listen for postMessage events from Jitsi iframe
window.addEventListener("message", function(e) {
  try {
    var data = (typeof e.data === "string") ? JSON.parse(e.data) : e.data;
    var evt = data && (data.event || data.type || "");
    if (
      evt === "readyToClose" ||
      evt === "videoConferenceLeft" ||
      evt === "hangup" ||
      evt === "CONFERENCE_LEFT"
    ) {
      signalCallEnd();
    }
  } catch(x) {}
});
</script>
</body>
</html>"""

    html = html.replace("JITSI_URL_PLACEHOLDER", jitsi_url)
    html = html.replace("END_KEY_PLACEHOLDER", safe_key)
    return html


# ── Speech capture HTML ───────────────────────────────────────────────────────

def _speech_capture_html(unique_key: str) -> str:
    """
    0-height invisible iframe that auto-starts Web Speech API.
    Pushes final sentences as JSON into the hidden transcript text_input.
    """
    js_key = unique_key.replace('"', "").replace("'", "").replace("\\", "")

    html = """<!DOCTYPE html>
<html>
<head><style>body{margin:0;padding:0;overflow:hidden;background:transparent;height:1px;}</style></head>
<body>
<script>
(function(){
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  var t0 = Date.now();
  var r = new SR();
  r.continuous = true;
  r.interimResults = false;
  r.lang = '';

  function push(text, ts) {
    var payload = JSON.stringify({text: text, ts_ms: ts});
    try {
      var doc = window.parent.document;
      var els = doc.querySelectorAll("input");
      for (var i = 0; i < els.length; i++) {
        var lbl = els[i].getAttribute("aria-label") || "";
        if (lbl === "TS_KEY_PLACEHOLDER") {
          var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          s.call(els[i], payload);
          els[i].dispatchEvent(new Event('input', {bubbles: true}));
          break;
        }
      }
    } catch(e) {}
  }

  r.onresult = function(e) {
    for (var i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        var tx = e.results[i][0].transcript.trim();
        var ts = Date.now() - t0;
        if (tx.length > 1) push(tx, ts);
      }
    }
  };
  r.onerror = function(e) {
    if (e.error !== 'no-speech' && e.error !== 'aborted')
      setTimeout(function(){ try { r.start(); } catch(x) {} }, 2000);
  };
  r.onend = function() {
    setTimeout(function(){ try { r.start(); } catch(x) {} }, 400);
  };
  try { r.start(); } catch(x) {}
})();
</script>
</body>
</html>"""

    html = html.replace("TS_KEY_PLACEHOLDER", js_key)
    return html


# ── Hidden input CSS hider ────────────────────────────────────────────────────

def _hide_input_css(*aria_labels) -> str:
    rules = ""
    for lbl in aria_labels:
        rules += (
            f'div[data-testid="stTextInput"]:has(input[aria-label="{lbl}"]) '
            "{position:absolute!important;opacity:0!important;"
            "pointer-events:none!important;height:0!important;"
            "overflow:hidden!important;margin:0!important;padding:0!important;}"
        )
    return f"<style>{rules}</style>"


# ── Main render_meeting ───────────────────────────────────────────────────────

def render_meeting(room_name: str, display_name: str, sender_label: str, role: str = "doctor"):
    """
    Renders the Jitsi video call (full width, no file sharing).
    Embeds invisible speech capture and transcript-saving fragment.
    The hidden 'call_ended' input is keyed by room+role and shared with
    render_consultation_summary_section via st.session_state.
    """
    from data.database import save_transcript_line

    saved_ts_key   = f"ts_saved_{room_name}_{role}"
    call_start_key = f"call_start_{room_name}_{role}"
    input_key      = f"ts_bridge_{room_name}_{role}"
    # ⚠ This key is also read by render_consultation_summary_section
    call_end_key   = f"call_ended_{room_name}"   # NOT role-specific — shared between doctor/patient

    if saved_ts_key not in st.session_state:
        st.session_state[saved_ts_key] = set()
    if call_start_key not in st.session_state:
        st.session_state[call_start_key] = int(time.time() * 1000)

    call_start_ms = st.session_state[call_start_key]

    # ── Jitsi (full width) ────────────────────────────────────────────────────
    st.components.v1.html(_jitsi_html(room_name, display_name, call_end_key), height=572)

    # Hidden text_input: transcript bridge (JS → Python)
    st.text_input(label=input_key,    key=f"ti_{input_key}",
                  label_visibility="collapsed", placeholder="")
    # Hidden text_input: call-ended signal (JS → Python)
    st.text_input(label=call_end_key, key=f"ti_{call_end_key}",
                  label_visibility="collapsed", placeholder="")

    st.markdown(_hide_input_css(input_key, call_end_key), unsafe_allow_html=True)

    # Invisible speech capture
    st.components.v1.html(_speech_capture_html(input_key), height=1, scrolling=False)

    @st.fragment(run_every=3)
    def _transcript_saver():
        raw = st.session_state.get(f"ti_{input_key}", "")
        if raw and raw not in st.session_state[saved_ts_key]:
            try:
                parsed = json.loads(raw)
                text   = parsed.get("text", "").strip()
                ts_ms  = parsed.get("ts_ms", int(time.time() * 1000) - call_start_ms)
                if text and len(text) > 1:
                    abs_ts = call_start_ms + ts_ms
                    save_transcript_line(room_name, sender_label, text, abs_ts)
                    st.session_state[saved_ts_key].add(raw)
            except Exception:
                pass

        from data.database import get_transcript_lines
        lines    = get_transcript_lines(room_name)
        my_lines = [l for l in lines if l["speaker_label"] == sender_label]
        cnt      = len(my_lines)
        if cnt:
            st.markdown(
                f'<div style="font-size:0.65rem;color:#34D399;margin-top:2px;">'
                f'🎙 {cnt} sentence{"s" if cnt != 1 else ""} captured from your mic</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="font-size:0.65rem;color:#475569;margin-top:2px;">'
                '🎙 Listening… (allow mic if prompted)</div>',
                unsafe_allow_html=True
            )

    _transcript_saver()


# ── Consultation summary section ──────────────────────────────────────────────

def render_consultation_summary_section(
    room_name: str,
    slot_id: str,
    doctor_id: str,
    patient_id: str,
    role: str = "doctor"
):
    """
    Fully automated summary — no button on either side.

    Key design decisions (fixes):
    - call_end_key is room-only (NOT role-specific) so both doctor and patient
      sides detect the same Jitsi hangup event.
    - Summary generation and rendering both happen INSIDE the fragment, so
      no st.rerun() is needed — the fragment re-renders the card in-place.
    - summary_generating_key prevents double-generation across fragment ticks.
    - Both sides independently poll DB; whoever gets there first generates,
      the other side just reads and renders.
    """
    from data.database import get_transcript_lines, get_meet_summary
    from core.meet_summary import merge_and_summarize, render_summary_card

    # Shared call-end key — must match what render_meeting() registered
    call_end_key        = f"call_ended_{room_name}"   # room-only, not role-specific
    summary_gen_key     = f"summary_generating_{slot_id}"

    st.markdown("---")
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
        '<span style="font-size:1.2rem;">🧠</span>'
        '<span style="font-weight:700;font-size:1rem;color:#A78BFA;">Consultation Summary</span>'
        '<span style="font-size:0.72rem;color:#475569;padding:2px 8px;border-radius:10px;'
        'background:rgba(124,58,237,0.1);border:1px solid #2d2d44;">'
        'AI · fully automated · any language'
        '</span></div>',
        unsafe_allow_html=True
    )

    # ── Polling fragment — handles both generation AND rendering ──────────────
    @st.fragment(run_every=4)
    def _auto_summary_poller():
        from data.database import get_transcript_lines, get_meet_summary
        from core.meet_summary import merge_and_summarize, render_summary_card

        # ── 1. Check if summary already exists in DB ──────────────────────────
        existing = get_meet_summary(slot_id)
        if existing:
            try:
                saved_summary = json.loads(existing["summary_json"])
            except Exception:
                saved_summary = {"error": "Could not parse saved summary."}
            render_summary_card(saved_summary, existing.get("created_at", ""))
            st.success("✅ Summary saved. View it anytime in the **📋 Consultation Summaries** tab.")
            return

        # ── 2. Check if call has ended ────────────────────────────────────────
        call_ended  = st.session_state.get(f"ti_{call_end_key}", "") == "1"
        generating  = st.session_state.get(summary_gen_key, False)
        lines       = get_transcript_lines(room_name)
        total       = len(lines)

        if call_ended and not generating and total > 0:
            # Doctor side takes priority to avoid double-generation.
            # Patient side waits one extra cycle (4s) then generates if doctor hasn't.
            should_generate = (role == "doctor")
            if not should_generate and role == "patient":
                # Patient generates only if still nothing in DB after the delay
                should_generate = True  # fragment already waited 4s since last tick

            if should_generate:
                st.session_state[summary_gen_key] = True
                st.markdown(
                    '<div style="background:#1a1a2e;border:1px solid #7C3AED;border-radius:10px;'
                    'padding:16px;text-align:center;color:#A78BFA;font-size:0.85rem;">'
                    '🧠 Generating consultation summary…'
                    '</div>',
                    unsafe_allow_html=True
                )
                result = merge_and_summarize(room_name, slot_id, doctor_id, patient_id)
                st.session_state[summary_gen_key] = False

                if "error" not in result:
                    # Re-fetch from DB and render immediately — no st.rerun() needed
                    fresh = get_meet_summary(slot_id)
                    if fresh:
                        try:
                            s = json.loads(fresh["summary_json"])
                        except Exception:
                            s = result
                        render_summary_card(s, fresh.get("created_at", ""))
                    else:
                        render_summary_card(result, "")
                    st.success("✅ Summary saved. View it anytime in the **📋 Consultation Summaries** tab.")
                else:
                    st.error(f"⚠️ Summary error: {result['error']}")
            else:
                # Waiting for doctor to generate
                st.markdown(
                    '<div style="background:#1a1a2e;border:1px dashed #2d2d44;border-radius:10px;'
                    'padding:16px;text-align:center;color:#475569;font-size:0.82rem;">'
                    '⏳ Finalizing summary…'
                    '</div>',
                    unsafe_allow_html=True
                )
            return

        # ── 3. Show live transcript stats while call is active ────────────────
        if call_ended and total == 0:
            st.markdown(
                '<div style="background:#1a1a2e;border:1px dashed #2d2d44;border-radius:10px;'
                'padding:20px;text-align:center;color:#475569;font-size:0.82rem;">'
                '<div style="font-size:1.8rem;margin-bottom:8px;">⚠️</div>'
                'Call ended but no transcript was captured.<br>'
                '<span style="color:#64748b;font-size:0.75rem;">Mic permission may have been denied.</span>'
                '</div>',
                unsafe_allow_html=True
            )
            return

        if total == 0:
            st.markdown(
                '<div style="background:#1a1a2e;border:1px dashed #2d2d44;border-radius:10px;'
                'padding:20px;text-align:center;color:#475569;font-size:0.82rem;">'
                '<div style="font-size:1.8rem;margin-bottom:8px;">🎙</div>'
                'Listening to the consultation…<br>Allow mic permission when prompted.<br>'
                '<span style="color:#7C3AED;font-size:0.78rem;">'
                '✨ Summary appears automatically when the call ends.'
                '</span></div>',
                unsafe_allow_html=True
            )
        else:
            doc_lines = [l for l in lines if "dr." in l["speaker_label"].lower()
                         or "doctor" in l["speaker_label"].lower()]
            pat_lines = [l for l in lines if "dr." not in l["speaker_label"].lower()
                         and "doctor" not in l["speaker_label"].lower()]
            col_a, col_b = st.columns(2)
            with col_a:
                dc = len(doc_lines)
                st.markdown(
                    '<div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:8px;'
                    'padding:10px;text-align:center;">'
                    '<div style="font-size:1.2rem;">👨‍⚕️</div>'
                    '<div style="font-size:0.75rem;font-weight:600;color:#A78BFA;">Doctor</div>'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">{dc}</div>'
                    '<div style="font-size:0.65rem;color:#475569;">sentences captured</div>'
                    '</div>', unsafe_allow_html=True
                )
            with col_b:
                pc = len(pat_lines)
                st.markdown(
                    '<div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:8px;'
                    'padding:10px;text-align:center;">'
                    '<div style="font-size:1.2rem;">🧑</div>'
                    '<div style="font-size:0.75rem;font-weight:600;color:#34D399;">Patient</div>'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">{pc}</div>'
                    '<div style="font-size:0.65rem;color:#475569;">sentences captured</div>'
                    '</div>', unsafe_allow_html=True
                )
            st.markdown(
                '<div style="font-size:0.75rem;color:#7C3AED;text-align:center;margin-top:8px;">'
                '✨ Summary will appear automatically when the call ends.'
                '</div>', unsafe_allow_html=True
            )

    _auto_summary_poller()
