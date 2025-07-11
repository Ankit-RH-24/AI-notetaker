let currentTranscript = "";
let recognition;
let recording = false;

const transcriptEl = document.getElementById("transcript");
const recordBtn = document.getElementById("recordBtn");
const saveBtn = document.getElementById("saveBtn");

// Initialize speech recognition
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-IN';

  recognition.onresult = function (event) {
    let interimTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const res = event.results[i];
      if (res.isFinal) {
        currentTranscript += res[0].transcript + " ";
      } else {
        interimTranscript += res[0].transcript;
      }
    }
    transcriptEl.value = currentTranscript + interimTranscript;
  };

  recognition.onerror = function (e) {
    console.error("Recognition error:", e.error);
  };

  recognition.onend = function () {
    if (recording) {
      recognition.start(); // auto-restart
    }
  };
} else {
  alert("Speech recognition not supported in this browser.");
}

// Toggle recording
recordBtn.onclick = () => {
  if (recording) {
    recognition.stop();
    recordBtn.innerText = "🎙️ Start Recording";
    recordBtn.classList.remove("bg-red-600");
    recordBtn.classList.add("bg-blue-600");
    recording = false;
  } else {
    currentTranscript = "";
    transcriptEl.value = "";
    recognition.start();
    recordBtn.innerText = "⏹️ Stop Recording";
    recordBtn.classList.remove("bg-blue-600");
    recordBtn.classList.add("bg-red-600");
    recording = true;
  }
};

// Save transcript
saveBtn.onclick = () => {
  const content = transcriptEl.value.trim();
  if (!content) {
    alert("Transcript is empty.");
    return;
  }

  const name = prompt("Enter a name for this transcript:", "Untitled");
  if (!name) return;

  const token = localStorage.getItem("mednote_id_token");
  if (!token) {
    alert("You must be logged in to save transcripts.");
    return;
  }

  const entry = {
    name,
    content,
    timestamp: new Date().toISOString()
  };

  fetch("/api/transcripts/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(entry)
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === "Saved") {
        alert("Saved successfully!");
        transcriptEl.value = "";
        currentTranscript = "";
      } else {
        alert("Save failed: " + (data.error || "Unknown error"));
      }
    })
    .catch(err => {
      console.error("Error saving:", err);
      alert("Error saving transcript.");
    });
};
