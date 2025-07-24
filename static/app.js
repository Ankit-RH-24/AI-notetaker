let currentTranscript = "";
let recognition;
let recording = false;
let selectedImageFile = null;

window.onload = () => {
  // --- Get all DOM elements ---
  const transcriptEl = document.getElementById("transcript");
  const recordBtn = document.getElementById("recordBtn");
  const saveBtn = document.getElementById("saveBtn");
  const recordIcon = document.getElementById("recordIcon");
  const waveform = document.getElementById("waveform");
  
  // OCR Elements
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
    recognition.onend = function() {
      if (recording) { recognition.start(); }
    };
  }

  // --- Start/Stop Recording Logic ---
  recordBtn.onclick = () => {
    if (recording) {
      recognition.stop();
      recording = false;
      recordIcon.innerText = "mic";
      waveform.classList.add("hidden");
      transcriptEl.classList.remove("animate-pulse");
      transcriptEl.placeholder = "Press the mic or camera to start...";
    } else {
      currentTranscript = "";
      transcriptEl.value = "";
      recognition.start();
      recording = true;
      recordIcon.innerText = "stop";
      waveform.classList.remove("hidden");
      transcriptEl.classList.add("animate-pulse");
      transcriptEl.placeholder = "Listening...";
    }
  };

  // --- Save Transcript Logic ---
  saveBtn.onclick = () => {
    const content = transcriptEl.value.trim();
    if (!content) return alert("Transcript is empty.");
    const name = prompt("Enter a name for this transcript:", "Untitled Session");
    if (!name) return;
    const token = localStorage.getItem("mednote_id_token");
    if (!token) return alert("You must be logged in to save transcripts.");

    fetch("/api/transcripts/save", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ name, content, timestamp: new Date().toISOString() })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "Saved") {
        alert("✅ Saved successfully!");
        transcriptEl.value = "";
        currentTranscript = "";
      } else {
        alert("❌ Save failed: " + (data.error || "Unknown error"));
      }
    });
  };

  // --- NEW: OCR/Image Upload Logic ---
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
        alert("Text extracted successfully!");
    })
    .catch(err => {
        console.error("Extraction error:", err);
        alert(`Error: ${err.message}`);
    })
    .finally(() => {
      imagePreviewModal.classList.add("hidden");
      modalActions.classList.remove("hidden");
      modalLoading.classList.add("hidden");
      imageInput.value = "";
      selectedImageFile = null;
    });
  };
};
