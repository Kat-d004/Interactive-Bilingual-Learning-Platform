/**
 * mic-recorder.js
 * Drop-in microphone recorder for the IBLP quiz pages.
 * Sends audio to recognize.php and shows the result.
 *
 * Usage: <script src="js/mic-recorder.js"></script>
 * Then call:  IBLPMic.attachTo(buttonElement, onResult)
 *
 * onResult(data) receives:
 *   { recognized: true,  number: 3, sesotho: "Tharo", confidence: 94.2 }
 *   { recognized: false, message: "Cannot recognize" }
 *   { error: "..." }
 */

const IBLPMic = (() => {
const ENDPOINT_ST = '/iblp/recognize_animals.php';   // Sesotho model
const ENDPOINT_EN = '/iblp/recognize_english.php?topic=animals'; // Whisper
  const SAMPLE_RATE  = 22050;
  const RECORD_MS    = 1000;             // record for 2.5 s then auto-stop

  let mediaRecorder = null;
  let audioChunks   = [];
  let isRecording   = false;

  // ── Core: record then POST ────────────────────────────────────────────────
  async function record(onStatusChange) {
    if (isRecording) return;

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      throw new Error('Microphone access denied: ' + e.message);
    }

    return new Promise((resolve, reject) => {
      audioChunks  = [];
      isRecording  = true;
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
            isRecording = false;
            stream.getTracks().forEach(t => t.stop());

            const blob = new Blob(audioChunks, { type: 'audio/wav' });
            onStatusChange && onStatusChange('sending');

            // Pick endpoint based on current language from app.js
            const lang = (typeof currentLanguage !== 'undefined') ? currentLanguage : 'st';
            const endpoint = lang === 'en' ? ENDPOINT_EN : ENDPOINT_ST;

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'audio/wav' },
                    body: blob,
                });
                const data = await response.json();
                resolve(data);
            } catch (err) {
                reject(new Error('Network error: ' + err.message));
            }
        };

      mediaRecorder.start();
      onStatusChange && onStatusChange('recording');

      // Auto-stop after RECORD_MS
      setTimeout(() => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
          mediaRecorder.stop();
        }
      }, RECORD_MS);
    });
  }

  // ── Attach to a button ────────────────────────────────────────────────────
  /**
   * @param {HTMLElement} btn       - The button to attach to
   * @param {Function}    onResult  - Called with the JSON result
   * @param {Object}      [opts]
   * @param {number}      [opts.recordMs=2500] - How long to record (ms)
   */
  function attachTo(btn, onResult, opts = {}) {
    const recordMs = opts.recordMs || RECORD_MS;

    btn.addEventListener('click', async () => {
      if (isRecording) return;

      const originalHTML = btn.innerHTML;
      btn.disabled = true;

      function setStatus(state) {
        if (state === 'recording') {
          btn.innerHTML = `
            <span style="display:inline-flex;align-items:center;gap:.4rem;">
              <span style="width:.7rem;height:.7rem;border-radius:50%;background:#ef4444;animation:ibp-pulse 1s infinite;display:inline-block;"></span>
              Recording…
            </span>`;
        } else if (state === 'sending') {
          btn.innerHTML = `
            <span style="display:inline-flex;align-items:center;gap:.4rem;">
              <span class="ibp-spinner"></span>
              Recognizing…
            </span>`;
        }
      }

      try {
        const data = await record(setStatus);
        onResult(data);
      } catch (err) {
        onResult({ error: err.message });
      } finally {
        btn.innerHTML = originalHTML;
        btn.disabled  = false;
      }
    });

    // Inject minimal keyframe CSS once
    if (!document.getElementById('ibp-mic-styles')) {
      const style = document.createElement('style');
      style.id = 'ibp-mic-styles';
      style.textContent = `
        @keyframes ibp-pulse {
          0%,100% { opacity:1; transform:scale(1); }
          50%      { opacity:.5; transform:scale(1.3); }
        }
        .ibp-spinner {
          display: inline-block;
          width: .9rem; height: .9rem;
          border: 2px solid currentColor;
          border-top-color: transparent;
          border-radius: 50%;
          animation: ibp-spin .7s linear infinite;
        }
        @keyframes ibp-spin { to { transform: rotate(360deg); } }
      `;
      document.head.appendChild(style);
    }
  }

  // ── Convenience: create a self-contained mic button ───────────────────────
  /**
   * Returns a <button> element with the mic icon.
   * Insert it wherever you like, then listen for the custom event
   * "iblp:recognized" on the button.
   */
  function createButton(label = 'Speak') {
    const btn = document.createElement('button');
    btn.className = 'btn btn-ghost speak-btn';
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="2" width="6" height="11" rx="3"/>
        <path d="M5 10a7 7 0 0014 0"/>
        <line x1="12" y1="19" x2="12" y2="22"/>
        <line x1="8"  y1="22" x2="16" y2="22"/>
      </svg>
      ${label}`;

    attachTo(btn, data => {
      btn.dispatchEvent(new CustomEvent('iblp:recognized', {
        bubbles: true, detail: data,
      }));
    });

    return btn;
  }

  return { attachTo, createButton, record };
})();
