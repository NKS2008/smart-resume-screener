// script.js
// Talks to the deployed FastAPI backend on Render.

const API_BASE = "https://smart-resume-screener-rvc7.onrender.com";

async function createJob() {
  const title = document.getElementById("jobTitle").value;
  const description = document.getElementById("jobDescription").value;

  if (!title || !description) {
    alert("Please fill in both the job title and description");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, description }),
    });

    if (!res.ok) throw new Error("Failed to create job.");

    const data = await res.json();

    document.getElementById("jobStatus").innerText =
      `✅ Job created successfully!\nJob ID: ${data.job_id}`;
  } catch (err) {
    document.getElementById("jobStatus").innerText =
      `❌ ${err.message}`;
  }
}

async function uploadResume() {
  const fileInput = document.getElementById("resumeFile");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please choose a resume file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/resumes/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Upload failed. Only PDF or TXT resumes are supported.");

    const data = await res.json();

    document.getElementById("parsedResult").innerText =
      `✅ Resume Parsed Successfully

Candidate ID: ${data.candidate_id}
Name: ${data.name}
Email: ${data.email}
Phone: ${data.phone}

Skills:
${data.skills.join(", ")}

Experience:
${data.experience}

Education:
${data.education}`;
  } catch (err) {
    document.getElementById("parsedResult").innerText =
      `❌ ${err.message}`;
  }
}

async function runMatch() {
  const candidateId = document.getElementById("candidateId").value;
  const jobId = document.getElementById("jobId").value;

  if (!candidateId || !jobId) {
    alert("Enter both Candidate ID and Job ID.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/match`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        candidate_id: Number(candidateId),
        job_id: Number(jobId),
      }),
    });

    if (!res.ok) throw new Error("Could not run AI matching.");

    const data = await res.json();

    document.getElementById("matchResult").innerText =
      `🎯 Match Score: ${data.score}/10

Reason:
${data.justification}`;
  } catch (err) {
    document.getElementById("matchResult").innerText =
      `❌ ${err.message}`;
  }
}

async function loadShortlist() {
  const jobId = document.getElementById("shortlistJobId").value;

  if (!jobId) {
    alert("Enter a Job ID.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/shortlist/${jobId}`);

    if (!res.ok) throw new Error("Could not load shortlist.");

    const data = await res.json();

    const tbody = document.querySelector("#shortlistTable tbody");
    tbody.innerHTML = "";

    if (data.length === 0) {
      tbody.innerHTML =
        `<tr><td colspan="6">No shortlisted candidates found.</td></tr>`;
      return;
    }

    data.forEach((row, index) => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${index + 1}</td>
        <td>${row.name}</td>
        <td>${row.email}</td>
        <td>${row.skills}</td>
        <td><strong>${row.score}/10</strong></td>
        <td>${row.justification}</td>
      `;

      tbody.appendChild(tr);
    });
  } catch (err) {
    const tbody = document.querySelector("#shortlistTable tbody");
    tbody.innerHTML =
      `<tr><td colspan="6">❌ ${err.message}</td></tr>`;
  }
}