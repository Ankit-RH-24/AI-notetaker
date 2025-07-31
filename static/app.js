let currentTranscript = "";
let recognition;
let recording = false;
let isPaused = false; // New state for tracking pause
let selectedImageFile = null;

window.onload = () => {
  // --- Get all DOM elements ---
  const transcriptEl = document.getElementById("transcript");
  const recordBtn = document.getElementById("recordBtn");
  const saveBtn = document.getElementById("saveBtn");
  const recordIcon = document.getElementById("recordIcon");
  const waveform = document.getElementById("waveform");
  
  // NEW: Pause/Resume elements
  const pauseBtn = document.getElementById("pauseBtn");
  const pauseIcon = document.getElementById("pauseIcon");

  const uploadBtn = document.getElementById("uploadBtn");
  const imageInput = document.getElementById("imageInput");
  const imagePreviewModal = document.getElementById("imagePreviewModal");
  const previewImage = document.getElementById("previewImage");
  const cancelUploadBtn = document.getElementById("cancelUploadBtn");
  const extractTextBtn = document.getElementById("extractTextBtn");
  const modalActions = document.getElementById("modal-actions");
  const modalLoading = document.getElementById("modal-loading");

  // --- Speech Recognition Logic ---
  if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onresult = function(event) {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          currentTranscript += event.results[i][0].transcript + ' ';
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      transcriptEl.value = currentTranscript + interimTranscript;
    };
    
    // UPDATED: onend logic to respect the paused state
    recognition.onend = function() {
      if (recording && !isPaused) {
        recognition.start();
      }
    };
  }

  // --- Start/Stop Recording Logic ---
  recordBtn.onclick = () => {
    // This button now functions as a "Start" and "Stop Session" button
    if (recording) {
      // --- Stop Recording ---
      recognition.stop();
      recording = false;
      isPaused = false;
      
      // Reset UI to initial state
      recordIcon.innerText = "mic";
      waveform.classList.remove("is-recording");
      pauseBtn.classList.add("hidden");
      uploadBtn.classList.remove("hidden");
      transcriptEl.placeholder = "Press the mic or camera to start...";
    } else {
      // --- Start Recording ---
      currentTranscript = "";
      transcriptEl.value = "";
      recognition.start();
      recording = true;
      isPaused = false;

      // Update UI to recording state
      recordIcon.innerText = "stop";
      waveform.classList.add("is-recording");
      pauseIcon.innerText = "pause";
      pauseBtn.classList.remove("hidden");
      uploadBtn.classList.add("hidden"); // Hide upload during recording
      transcriptEl.placeholder = "Listening...";
    }
  };

  // --- NEW: Pause/Resume Logic ---
  pauseBtn.onclick = () => {
    if (!recording) return; // Should not be clickable if not recording

    if (isPaused) {
      // --- Resume Recording ---
      recognition.start();
      isPaused = false;
      
      // Update UI
      pauseIcon.innerText = "pause";
      waveform.classList.add("is-recording");
      transcriptEl.placeholder = "Listening...";
    } else {
      // --- Pause Recording ---
      recognition.stop();
      isPaused = true;
      
      // Update UI
      pauseIcon.innerText = "play_arrow"; // Play icon for "Resume"
      waveform.classList.remove("is-recording");
      transcriptEl.placeholder = "Paused...";
    }
  };

  // --- Save Transcript & OCR Logic (Unchanged)---
  // ... (The rest of your save and OCR logic remains the same) ...
};
