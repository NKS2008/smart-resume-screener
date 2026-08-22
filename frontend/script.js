// script.js
// Talks to the FastAPI backend. Assumes the API is running on port 8000.
// (change this if you deploy it somewhere else)

const API_BASE = "http://localhost:8000";

async function createJob() {
  const title = document.getElementById("jobTitle").value;
  const description = document.getElementById("jobDescription").value;

  if (!title || !description) {
    alert("Please fill in both the job title and description");
    return;
  }

  const res = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description }),
  });

  const data = await res.json();
  document.getElementById("jobStatus").innerText =
    `Saved! Job ID = ${data.job_id}. Use this ID in step 3/4.`;
}

async function uploadResume() {
  const fileInput = document.getElementById("resumeFile");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please choose a resume file first");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/resumes/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    document.getElementById("parsedResult").innerText = "Upload failed. Check the file type.";
    return;
  }

  const data = await res.json();

  document.getElementById("parsedResult").innerText =
    `Candidate ID: ${data.candidate_id}\n` +
    `Name: ${data.name}\n` +
    `Email: ${data.email}\n` +
    `Phone: ${data.phone}\n` +
    `Skills: ${data.skills.join(", ")}\n` +
    `Experience: ${data.experience.slice(0, 200)}...\n` +
    `Education: ${data.education.slice(0, 200)}...`;
}

async function runMatch() {
  const candidateId = document.getElementById("candidateId").value;
  const jobId = document.getElementById("jobId").value;

  if (!candidateId || !jobId) {
    alert("Enter both candidate ID and job ID");
    return;
  }

  const res = await fetch(`${API_BASE}/match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_id: parseInt(candidateId),
      job_id: parseInt(jobId),
    }),
  });

  if (!res.ok) {
    document.getElementById("matchResult").innerText = "Could not run match. Check the IDs.";
    return;
  }

  const data = await res.json();
  document.getElementById("matchResult").innerText =
    `Score: ${data.score}/10\nJustification: ${data.justification}`;
}

async function loadShortlist() {
  const jobId = document.getElementById("shortlistJobId").value;
  if (!jobId) {
    alert("Enter a job ID");
    return;
  }

  const res = await fetch(`${API_BASE}/shortlist/${jobId}`);
  const data = await res.json();

  const tbody = document.querySelector("#shortlistTable tbody");
  tbody.innerHTML = "";

  data.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${row.name}</td>
      <td>${row.email}</td>
      <td>${row.skills}</td>
      <td>${row.score}</td>
      <td>${row.justification}</td>
    `;
    tbody.appendChild(tr);
  });
}
