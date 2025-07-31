let currentTranscript = "";
let recognition;
let recording = false;
let isPaused = false; // For pause/resume
let selectedImageFile = null;

window.onload = () => {
  // --- Get all DOM elements ---
  const transcriptEl = document.getElementById("transcript");
  const recordBtn = document.getElementById("recordBtn");
  const saveBtn = document.getElementById("saveBtn");
  const recordIcon = document.getElementById("recordIcon");
  const waveform = document.getElementById("waveform");
  
  // Pause/Resume elements
  const pauseBtn = document.getElementById("pauseBtn");
  const pauseIcon = document.getElementById("pauseIcon");

  // OCR Elements
  const uploadBtn = document.getElementById("uploadBtn");
  const imageInput = document.getElementById("imageInput");
  const imagePreviewModal = document.getElementById("imagePreviewModal");
  const previewImage = document.getElementById("previewImage");
  const cancelUploadBtn = document.getElementById("cancelUploadBtn");
  const extractTextBtn = document.getElementById("extractTextBtn");
  const modalActions = document.getElementById("modal-actions");
  const modalLoading = document.getElementById("modal-loading");

  // Premium UX Elements
  const saveSessionModal = document.getElementById("saveSessionModal");
  const sessionNameInput = document.getElementById("sessionNameInput");
  const cancelSaveBtn = document.getElementById("cancelSaveBtn");
  const confirmSaveBtn = document.getElementById("confirmSaveBtn");
  const toast = document.getElementById("toast");
  const toastMessage = document.getElementById("toast-message");

  // --- Toast Notification Function ---
  function showToast(message, isError = false) {
    toastMessage.textContent = message;
    toast.className = `fixed bottom-8 right-8 text-white px-5 py-3 rounded-lg shadow-xl transform translate-y-0 opacity-100 transition-all duration-300 ${isError ? 'bg-red-600' : 'bg-gray-900'}`;
    setTimeout(() => {
      toast.className = toast.className.replace('translate-y-0 opacity-100', 'translate-y-20 opacity-0');
    }, 3000);
  }

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
    
    recognition.onend = function() {
      if (recording && !isPaused) {
        recognition.start();
      }
    };
  }

  // --- Start/Stop Recording Logic ---
  recordBtn.onclick = () => {
    if (recording) {
      recognition.stop();
      recording = false;
      isPaused = false;
      
      recordIcon.innerText = "mic";
      waveform.classList.remove("is-recording");
      pauseBtn.classList.add("hidden");
      uploadBtn.classList.remove("hidden");
      transcriptEl.placeholder = "Press the mic or camera to start...";
    } else {
      currentTranscript = "";
      transcriptEl.value = "";
      waveform.classList.remove("hidden"); // Ensure waveform is visible
      recognition.start();
      recording = true;
      isPaused = false;

      recordIcon.innerText = "stop";
      waveform.classList.add("is-recording");
      pauseIcon.innerText = "pause";
      pauseBtn.classList.remove("hidden");
      uploadBtn.classList.add("hidden");
      transcriptEl.placeholder = "Listening...";
    }
  };

  // --- Pause/Resume Logic ---
  pauseBtn.onclick = () => {
    if (!recording) return;

    if (isPaused) {
      recognition.start();
      isPaused = false;
      
      pauseIcon.innerText = "pause";
      waveform.classList.add("is-recording");
      transcriptEl.placeholder = "Listening...";
    } else {
      recognition.stop();
      isPaused = true;
      
      pauseIcon.innerText = "play_arrow";
      waveform.classList.remove("is-recording");
      transcriptEl.placeholder = "Paused...";
    }
  };

  // --- Save Transcript Logic ---
  saveBtn.onclick = () => {
    const content = transcriptEl.value.trim();
    if (!content) {
      showToast("Transcript is empty.", true);
      return;
    }
    sessionNameInput.value = "Untitled Session";
    saveSessionModal.classList.remove("hidden");
    sessionNameInput.focus();
  };

  cancelSaveBtn.onclick = () => {
    saveSessionModal.classList.add("hidden");
  };

  confirmSaveBtn.onclick = () => {
    const name = sessionNameInput.value.trim();
    if (!name) {
      showToast("Please enter a session name.", true);
      return;
    }

    const content = transcriptEl.value.trim();
    const token = localStorage.getItem("mednote_id_token");
    if (!token) {
      showToast("You must be logged in to save.", true);
      return;
    }

    confirmSaveBtn.disabled = true;
    confirmSaveBtn.textContent = "Saving...";

    fetch("/api/transcripts/save", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ name, content, timestamp: new Date().toISOString() })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "Saved") {
        showToast("✅ Saved successfully!");
        transcriptEl.value = "";
        currentTranscript = "";
        waveform.classList.remove("hidden"); // Show waveform again after saving
      } else {
        showToast(`Save failed: ${data.error || "Unknown error"}`, true);
      }
    })
    .catch(err => {
        showToast("Error saving transcript.", true);
        console.error("Save error:", err);
    })
    .finally(() => {
      confirmSaveBtn.disabled = false;
      confirmSaveBtn.textContent = "Save";
      saveSessionModal.classList.add("hidden");
    });
  };

  // --- OCR/Image Upload Logic ---
  uploadBtn.onclick = () => { imageInput.click(); };

  imageInput.onchange = (event) => {
    const file = event.target.files[0];
    if (file) {
      selectedImageFile = file;
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImage.src = e.target.result;
        imagePreviewModal.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  };

  cancelUploadBtn.onclick = () => {
    imagePreviewModal.classList.add("hidden");
    imageInput.value = "";
    selectedImageFile = null;
  };

  extractTextBtn.onclick = () => {
    if (!selectedImageFile) return;
    
    extractTextBtn.disabled = true;
    extractTextBtn.textContent = "Extracting...";
    modalActions.classList.add("hidden");
    modalLoading.classList.remove("hidden");

    const formData = new FormData();
    formData.append("image", selectedImageFile);
    const token = localStorage.getItem("mednote_id_token");

    fetch("/api/transcripts/extract-from-image", {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
      body: formData
    })
    .then(res => res.json().then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
        if (!ok) throw new Error(data.error || 'Extraction failed');
        currentTranscript = data.text;
        transcriptEl.value = currentTranscript;
        waveform.classList.add("hidden"); // Hide waveform after text extraction
        showToast("Text extracted successfully!");
    })
    .catch(err => {
        console.error("Extraction error:", err);
        showToast(`Error: ${err.message}`, true);
    })
    .finally(() => {
      extractTextBtn.disabled = false;
      extractTextBtn.textContent = "Extract Text";
      imagePreviewModal.classList.add("hidden");
      modalActions.classList.remove("hidden");
      modalLoading.classList.add("hidden");
      imageInput.value = "";
      selectedImageFile = null;
    });
  };
};
