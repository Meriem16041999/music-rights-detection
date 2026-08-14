import { useRef, useState, useEffect } from "react";
import axios from "axios";
import "./App.css";
import HistoryPage from "./HistoryPage";
 


const API = "http://localhost:8000";

function App() {
  const videoRef = useRef(null);
  const mdpVideoRef = useRef(null);
  const mdpMappingRef = useRef(null);
  const classicVideoRef = useRef(null);
  const classicMappingRef = useRef(null);
  const [mode, setMode] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
   
  const [acrHits, setAcrHits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conductorType, setConductorType] = useState("Lundi-Jeudi");
  const waveformRef = useRef(null);
  const [cleanAudio, setCleanAudio] = useState(false);
 
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [classicIntro, setClassicIntro] = useState("GEN_TALENT");
  const [page, setPage] = useState("workspace");
  const [projects, setProjects] = useState([]);
  const [currentProjectId, setCurrentProjectId] = useState(null);
  const [projectName, setProjectName] = useState("");
  const [pixelsPerSecond, setPixelsPerSecond] = useState(8);
  const [timelineScrollLeft, setTimelineScrollLeft] = useState(0);
  const [rows, setRows] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const selectedRow =
  selectedIndex !== null
    ? rows[selectedIndex]
    : null;
  
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] =
    useState("idle");
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] =
    useState("");
  const [currentChunk, setCurrentChunk] =
    useState(0);
  const [totalChunks, setTotalChunks] =
    useState(0);
  const [jobError, setJobError] = useState("");
 useEffect(() => {
  if (!jobId) {
    return;
  }

  let stopped = false;
  let timer = null;

  const pollJob = async () => {
    try {
      const response = await fetch(
        `${API}/jobs/${jobId}`
      );

      if (!response.ok) {
        throw new Error(
          "Impossible de récupérer le statut du job"
        );
      }

      const job = await response.json();

      if (stopped) {
        return;
      }

      setJobStatus(job.status || "idle");
      setProgress(job.progress || 0);
      setProgressMessage(job.message || "");
      setCurrentChunk(job.current_chunk || 0);
      setTotalChunks(job.total_chunks || 0);

      if (job.status === "done") {
        setRows(job.result?.rows || []);
        setAcrHits(job.result?.acr_hits || []);
        setVideoDuration(
          job.result?.video_duration || 0
        );

        setLoading(false);
        return;
      }

      if (
        job.status === "error" ||
        job.status === "cancelled"
      ) {
        setLoading(false);
        setJobError(job.error || "");
        return;
      }

      timer = window.setTimeout(
        pollJob,
        1000
      );
    } catch (error) {
      console.error("POLLING ERROR:", error);

      if (!stopped) {
        timer = window.setTimeout(
          pollJob,
          3000
        );
      }
    }
  };

  pollJob();

  return () => {
    stopped = true;
    

    if (timer) {
      window.clearTimeout(timer);
    }
  };
}, [jobId]);
 
 
function secondsToTimecode(sec) {
  sec = Math.max(0, Math.round(Number(sec) || 0));
  const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  const s = String(sec % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function durationOf(row) {
  return Math.max(1, Number(row.end_sec || 0) - Number(row.start_sec || 0));
}

function shiftFollowingLocal(inputRows, changedIndex, newEndSec) {
  const updated = inputRows.map((r) => ({ ...r }));

  const start = Number(updated[changedIndex].start_sec || 0);
  const end = Math.max(start + 1, Math.round(newEndSec));

  updated[changedIndex].end_sec = end;
  updated[changedIndex].time_out = secondsToTimecode(end);
  updated[changedIndex].duration = secondsToTimecode(end - start);

  let cursor = end;

  for (let i = changedIndex + 1; i < updated.length; i++) {
    const dur = durationOf(updated[i]);

    updated[i].start_sec = cursor;
    updated[i].end_sec = cursor + dur;
    updated[i].time_in = secondsToTimecode(cursor);
    updated[i].time_out = secondsToTimecode(cursor + dur);
    updated[i].duration = secondsToTimecode(dur);

    cursor += dur;
  }

  return updated;
}
function timelineWidth() {
  return Math.max(
    1200,
    timelineDuration() * pixelsPerSecond
  );
}

function formatTimelineLabel(sec) {
  sec = Math.max(0, Math.floor(sec));

  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;

  if (h > 0) {
    return `${String(h).padStart(2, "0")}:${String(m).padStart(
      2,
      "0"
    )}:${String(s).padStart(2, "0")}`;
  }

  return `${String(m).padStart(2, "0")}:${String(s).padStart(
    2,
    "0"
  )}`;
}

function getProjectQualitySummary() {
  const summary = {
    total: rows.length,
    validated: 0,
    review: 0,
    missing: 0,
    internal: 0,
    pending: 0,
  };

  rows.forEach((row) => {
    const status =
      getQualityStatus(row);

    if (
      status.code === "validated"
    ) {
      summary.validated += 1;
    }

    else if (
      status.code === "review"
    ) {
      summary.review += 1;
    }

    else if (
      status.code === "missing"
    ) {
      summary.missing += 1;
    }

    else if (
      status.code === "internal"
    ) {
      summary.internal += 1;
    }

    else {
      summary.pending += 1;
    }
  });

  const relevant =
    summary.total -
    summary.internal;

  const score =
    relevant > 0
      ? Math.round(
          (
            summary.validated /
            relevant
          ) * 100
        )
      : 0;

  return {
    ...summary,
    score,
  };
}
function getQualityStatus(row) {
  const manualStatus = String(
    row.statut_validation || ""
  );

  if (manualStatus === "validated") {
    return {
      code: "validated",
      label: "Validé",
    };
  }

  if (manualStatus === "review") {
    return {
      code: "review",
      label: "À vérifier",
    };
  }

  const sacemStatus = String(
    row.statut_sacem || ""
  );

  if (
    sacemStatus === "not_found" ||
    sacemStatus === "blocked" ||
    sacemStatus.startsWith("error")
  ) {
    return {
      code: "missing",
      label: "Non trouvé",
    };
  }

  if (sacemStatus === "found") {
    return {
      code: "review",
      label: "À vérifier",
    };
  }

  return {
    code: "pending",
    label: "En attente",
  };
}

function timelineTickStep() {
  if (pixelsPerSecond >= 20) return 5;
  if (pixelsPerSecond >= 10) return 10;
  if (pixelsPerSecond >= 5) return 30;
  if (pixelsPerSecond >= 2) return 60;

  return 120;
}

function buildTimelineTicks() {
  const step = timelineTickStep();
  const duration = Math.ceil(timelineDuration());

  const ticks = [];

  for (let sec = 0; sec <= duration; sec += step) {
    ticks.push(sec);
  }

  return ticks;
}

function updateSegmentTimes(index, newStart, newEnd) {
  const updated = rows.map((r) => ({ ...r }));

  newStart = Math.max(0, Math.round(newStart));
  newEnd = Math.max(newStart + 1, Math.round(newEnd));

  updated[index].start_sec = newStart;
  updated[index].end_sec = newEnd;
  updated[index].time_in = secondsToTimecode(newStart);
  updated[index].time_out = secondsToTimecode(newEnd);
  updated[index].duration = secondsToTimecode(newEnd - newStart);

  setRows(updated);
}
async function cancelAnalysis() {
  if (!jobId) {
    return;
  }

  await fetch(
    `${API}/jobs/${jobId}/cancel`,
    {
      method: "POST",
    }
  );

  setProgressMessage(
    "Interruption demandée..."
  );
}


async function resumeAnalysis() {
  if (!jobId) {
    return;
  }

  await fetch(
    `${API}/jobs/${jobId}/resume`,
    {
      method: "POST",
    }
  );

  setLoading(true);
  setJobStatus("pending");
  setJobError("");
}

function onMoveSegment(e, index) {
  e.preventDefault();
  e.stopPropagation();

  const track =
    e.currentTarget.closest(".edit-timeline");

  if (!track) {
    return;
  }

  const rect =
    track.getBoundingClientRect();

  const total = timelineDuration();

  const row = rows[index];

  const originalStart = Number(
    row.start_sec || 0
  );

  const originalEnd = Number(
    row.end_sec || 0
  );

  const duration =
    originalEnd - originalStart;

  const startX = e.clientX;

  function onMove(moveEvent) {
    const deltaPx =
      moveEvent.clientX - startX;

    const deltaSec = Math.round(
      (deltaPx / rect.width) * total
    );

    const newStart = Math.max(
      0,
      originalStart + deltaSec
    );

    updateSegmentTimes(
      index,
      newStart,
      newStart + duration
    );
  }

  function onUp() {
    window.removeEventListener(
      "mousemove",
      onMove
    );

    window.removeEventListener(
      "mouseup",
      onUp
    );
  }

  window.addEventListener(
    "mousemove",
    onMove
  );

  window.addEventListener(
    "mouseup",
    onUp
  );
}

function addRowAtTime(sec) {
  const start = Math.max(0, Math.round(sec));
  const end = start + 10;

  const newRow = {
    index: rows.length,
    title: "NOUVELLE MUSIQUE",
    acr_title: "",
    time_in: secondsToTimecode(start),
    time_out: secondsToTimecode(end),
    duration: secondsToTimecode(end - start),
    start_sec: start,
    end_sec: end,
    score: "",
    source: "manuel",
  };

  const updated = [...rows, newRow].sort(
    (a, b) => Number(a.start_sec || 0) - Number(b.start_sec || 0)
  );

  setRows(updated);
  setSelectedIndex(updated.findIndex((r) => r === newRow));
}

 

function timecodeToSeconds(tc) {
  const parts = String(tc || "00:00:00").split(":").map(Number);
  const h = parts[0] || 0;
  const m = parts[1] || 0;
  const s = parts[2] || 0;
  return h * 3600 + m * 60 + s;
}

function laneForSegment(row, index) {
  const lanes = mode === "mdp" ? 3 : 4;
  return index % lanes;
}

function applyOnlyThisRow(index) {
  const updated = rows.map((r) => ({ ...r }));

  const start = timecodeToSeconds(updated[index].time_in);
  let end = timecodeToSeconds(updated[index].time_out);

  if (end <= start) {
    end = start + 1;
  }

  updated[index].start_sec = start;
  updated[index].end_sec = end;
  updated[index].time_in = secondsToTimecode(start);
  updated[index].time_out = secondsToTimecode(end);
  updated[index].duration = secondsToTimecode(end - start);

  setRows(updated);
}

function totalsByTitle() {
  const map = {};

  rows.forEach((r) => {
    const title = r.title || "Sans titre";
    const dur = durationOf(r);

    map[title] = (map[title] || 0) + dur;
  });

  return Object.entries(map).map(([title, seconds]) => ({
    title,
    seconds,
    duration: secondsToTimecode(seconds),
  }));
}

function timelineDuration() {
  if (videoDuration > 0) return videoDuration;
  if (!rows.length) return 1;
  return Math.max(...rows.map((r) => Number(r.end_sec || 0)), 1);
}

function selectRow(index) {
  setSelectedIndex(index);
  const row = rows[index];
  if (row) jumpTo(row.start_sec);
}

function updateSelected(field, value) {
  if (selectedIndex === null) return;
  updateRow(selectedIndex, field, value);
}
function resetWorkspace(nextMode) {
  setPage("workspace");
  setMode(nextMode);
  setVideoUrl(null);
  setRows([]);
  setAcrHits([]);
  setCurrentProjectId(null);
  setProjectName("");
}

  function onVideoFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setVideoUrl(URL.createObjectURL(file));
  }
 

  
 
async function loadProjects() {
  try {
    const response = await fetch(
      `${API}/projects`
    );

    if (!response.ok) {
      throw new Error(
        `Erreur HTTP ${response.status}`
      );
    }

    const data = await response.json();

    setProjects(data.projects || []);
  } catch (error) {
    console.error(
      "LOAD PROJECTS ERROR:",
      error
    );
  }
}
async function saveProject() {
  if (!projectName.trim()) {
    alert("Entre un nom d'émission.");
    return;
  }

  if (!rows.length) {
    alert("Aucun résultat à sauvegarder.");
    return;
  }

  const qualitySummary =
    getProjectQualitySummary();

  const formData = new FormData();

  formData.append(
    "name",
    projectName.trim()
  );

  formData.append(
    "mode",
    mode
  );
const selectedVideo =
  mode === "mdp"
    ? mdpVideoRef.current?.files?.[0]
    : classicVideoRef.current?.files?.[0];

const existingProject =
  projects.find(
    (project) =>
      project.id === currentProjectId
  );

const videoName =
  selectedVideo?.name ||
  existingProject?.video_name ||
  "";

 
  
  formData.append(
  "video_name",
  videoName
);

  formData.append(
    "rows_json",
    JSON.stringify(rows)
  );

  formData.append(
    "metadata_json",
    JSON.stringify({
      conductorType,
      classicIntro,
      cleanAudio,
      videoDuration,
      segmentCount: rows.length,
      validatedCount:
        qualitySummary.validated,
      reviewCount:
        qualitySummary.review,
      missingCount:
        qualitySummary.missing,
      qualityScore:
        qualitySummary.score,
    })
  );

  const url = currentProjectId
    ? `${API}/projects/${currentProjectId}`
    : `${API}/projects`;

  const method = currentProjectId
    ? "PUT"
    : "POST";

  const response = await fetch(url, {
    method,
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      `Erreur HTTP ${response.status}`
    );
  }

  if (data.project_id) {
    setCurrentProjectId(
      data.project_id
    );
  }

  await loadProjects();

  alert(
    currentProjectId
      ? "Projet mis à jour."
      : "Projet sauvegardé."
  );
}
async function openProject(projectId) {
  try {
    const response = await fetch(
      `${API}/projects/${projectId}`
    );

    if (!response.ok) {
      throw new Error(
        `Erreur HTTP ${response.status}`
      );
    }

    const project =
      await response.json();

    setCurrentProjectId(project.id);
    setProjectName(project.name || "");
    setMode(project.mode || "");

    setRows(project.rows || []);

    setConductorType(
      project.metadata?.conductorType ||
        "Lundi-Jeudi"
    );

    setClassicIntro(
      project.metadata?.classicIntro ||
        "NONE"
    );

    setCleanAudio(
      Boolean(
        project.metadata?.cleanAudio
      )
    );

    setVideoDuration(
      Number(
        project.metadata?.videoDuration ||
          0
      )
    );

    setSelectedIndex(null);

    setPage("workspace");
  } catch (error) {
    console.error(
      "OPEN PROJECT ERROR:",
      error
    );

    alert(
      "Impossible d'ouvrir ce projet."
    );
  }
}
async function analyzeClassic() {
  const file =
    classicVideoRef.current?.files?.[0];

  if (!file) {
    alert("Choisis une vidéo d’abord.");
    return;
  }

  const formData = new FormData();

  formData.append("video", file);
  formData.append(
    "conductor_type",
    conductorType
  );
  formData.append(
    "intro_type",
    classicIntro
  );
  formData.append(
    "clean_audio",
    cleanAudio ? "YES" : "NO"
  );

  const mappingFile =
    classicMappingRef.current?.files?.[0];

  if (mappingFile) {
    formData.append(
      "mapping",
      mappingFile
    );
  }

  setLoading(true);
  setProgress(0);
  setJobError("");
  setProgressMessage(
    "Envoi de la vidéo..."
  );

  try {
    const response = await axios.post(
      `${API}/analyze-acr/start`,
      formData,
      {
        headers: {
          "Content-Type":
            "multipart/form-data",
        },
      }
    );

    setJobId(response.data.job_id);
    setJobStatus("pending");
  } catch (error) {
    console.error(
      "ANALYZE CLASSIC ERROR:",
      error
    );

    setLoading(false);
    setJobStatus("error");
    setJobError(
      "Impossible de démarrer l’analyse."
    );
  }
}
function jumpTo(sec) {
  const time = Number(sec || 0);

  if (videoRef.current) {
    videoRef.current.currentTime = time;
    videoRef.current.play();
  }

  setCurrentTime(time);
}
  

  async function downloadM6() {
  if (!rows.length) {
    alert("Aucune donnée à exporter.");
    return;
  }
  
  const formData = new FormData();
  formData.append("rows_json", JSON.stringify(rows));

  const res = await axios.post(`${API}/download-m6`, formData, {
    responseType: "blob",
  });

function timelineClickToSeek(e) {
  if (e.target.closest(".segment-block")) {
    return;
  }

  const rect =
    e.currentTarget.getBoundingClientRect();

  const x =
    e.clientX - rect.left;

  const sec =
    (x / rect.width) * timelineDuration();

  jumpTo(sec);
}

 

  const url = window.URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = "declaration_m6.xlsx";
  a.click();
  window.URL.revokeObjectURL(url);
}

  function updateRow(index, field, value) {
    const updated = [...rows];
    updated[index] = { ...updated[index], [field]: value };
    setRows(updated);
  }

  async function deleteProject(projectId) {
   const confirmed = window.confirm(
    "Supprimer définitivement ce projet ?"
   );

  if (!confirmed) {
    return;
  }

  try {
    const response = await fetch(
      `${API}/projects/${projectId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      const errorText = await response.text();

      throw new Error(
        errorText || "Impossible de supprimer le projet"
      );
    }

    setProjects((previousProjects) =>
      previousProjects.filter(
        (project) => project.id !== projectId
      )
    );

    if (currentProjectId === projectId) {
      setCurrentProjectId(null);
      setProjectName("");
      setRows([]);
    }
  } catch (error) {
    console.error(error);

    alert(
      `Erreur lors de la suppression : ${
        error?.message || "erreur inconnue"
      }`
    );
  }
}
  function colorClassForTitle(title) {
  const t = String(title || "").toUpperCase().trim();

  if (t.includes("MUSIQUE NON RECONNUE")) return "seg-unknown";
  if (t.includes("GENERIQUE")) return "seg-generique";
  if (t.includes("JINGLE")) return "seg-jingle";
  if (t.includes("TALK")) return "seg-talk";
  if (t.includes("CHRONO")) return "seg-chrono";
  if (t.includes("REFLEXION")) return "seg-reflexion";

  // FIN doit être un mot entier, pas une partie de FINGERZ
  if (/\bFIN\b/.test(t) || t.includes("FIN GAGNANTE")) {
    return "seg-fin";
  }

  return "seg-classic";
}
function addRowAfter(index) {
  const current = rows[index];

  if (!current) return;

  const start =
    Number(current.end_sec) ||
    timecodeToSeconds(current.time_out);

  const end = start + 10;

  const newRow = {
    index: rows.length,
    title: "NOUVELLE MUSIQUE",
    acr_title: "",
    artist: "",
    time_in: secondsToTimecode(start),
    time_out: secondsToTimecode(end),
    duration: secondsToTimecode(end - start),
    start_sec: start,
    end_sec: end,
    score: "",
    source: "manuel",
  };

  const updated = [...rows];

  updated.splice(
    index + 1,
    0,
    newRow
  );

  // Réindexer
  const reindexed = updated.map(
    (row, i) => ({
      ...row,
      index: i,
    })
  );

  setRows(reindexed);
  setSelectedIndex(index + 1);
}


function applyShift(index) {
  if (index === null || index === undefined) {
    return;
  }

  const updated = rows.map(
    (row) => ({ ...row })
  );

  const current = updated[index];

  if (!current) return;

  const start =
    timecodeToSeconds(current.time_in);

  let end =
    timecodeToSeconds(current.time_out);

  if (end <= start) {
    end = start + 1;
  }

  current.start_sec = start;
  current.end_sec = end;
  current.time_in =
    secondsToTimecode(start);
  current.time_out =
    secondsToTimecode(end);
  current.duration =
    secondsToTimecode(end - start);

  // En mode MDP :
  // recaler tous les segments suivants
  let cursor = end;

  for (
    let i = index + 1;
    i < updated.length;
    i++
  ) {
    const duration =
      durationOf(updated[i]);

    updated[i].start_sec = cursor;
    updated[i].end_sec =
      cursor + duration;

    updated[i].time_in =
      secondsToTimecode(cursor);

    updated[i].time_out =
      secondsToTimecode(
        cursor + duration
      );

    updated[i].duration =
      secondsToTimecode(duration);

    cursor += duration;
  }

  setRows(updated);
}
function onMoveProSegment(event, index) {
  if (event.target.closest(".pro-resize-handle")) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();

  const row = rows[index];

  const originalStart = Number(row.start_sec || 0);
  const originalEnd = Number(row.end_sec || 0);
  const duration = Math.max(
    1,
    originalEnd - originalStart
  );

  const startX = event.clientX;

  function onMove(moveEvent) {
    const deltaPx =
      moveEvent.clientX - startX;

    const deltaSec = Math.round(
      deltaPx / pixelsPerSecond
    );

    const nextStart = Math.max(
      0,
      originalStart + deltaSec
    );

    updateSegmentTimes(
      index,
      nextStart,
      nextStart + duration
    );
  }

  function onUp() {
    window.removeEventListener(
      "mousemove",
      onMove
    );

    window.removeEventListener(
      "mouseup",
      onUp
    );
  }

  window.addEventListener(
    "mousemove",
    onMove
  );

  window.addEventListener(
    "mouseup",
    onUp
  );
}


function onResizeProLeft(event, index) {
  event.preventDefault();
  event.stopPropagation();

  const originalEnd = Number(
    rows[index].end_sec || 0
  );

  const startX = event.clientX;

  const originalStart = Number(
    rows[index].start_sec || 0
  );

  function onMove(moveEvent) {
    const deltaPx =
      moveEvent.clientX - startX;

    const deltaSec = Math.round(
      deltaPx / pixelsPerSecond
    );

    const nextStart = Math.max(
      0,
      Math.min(
        originalEnd - 1,
        originalStart + deltaSec
      )
    );

    updateSegmentTimes(
      index,
      nextStart,
      originalEnd
    );
  }

  function onUp() {
    window.removeEventListener(
      "mousemove",
      onMove
    );

    window.removeEventListener(
      "mouseup",
      onUp
    );
  }

  window.addEventListener(
    "mousemove",
    onMove
  );

  window.addEventListener(
    "mouseup",
    onUp
  );
}


function onResizeProRight(event, index) {
  event.preventDefault();
  event.stopPropagation();

  const originalStart = Number(
    rows[index].start_sec || 0
  );

  const originalEnd = Number(
    rows[index].end_sec || 0
  );

  const startX = event.clientX;

  function onMove(moveEvent) {
    const deltaPx =
      moveEvent.clientX - startX;

    const deltaSec = Math.round(
      deltaPx / pixelsPerSecond
    );

    const nextEnd = Math.max(
      originalStart + 1,
      originalEnd + deltaSec
    );

    if (mode === "mdp") {
      setRows((previousRows) =>
        shiftFollowingLocal(
          previousRows,
          index,
          nextEnd
        )
      );

      return;
    }

    updateSegmentTimes(
      index,
      originalStart,
      nextEnd
    );
  }

  function onUp() {
    window.removeEventListener(
      "mousemove",
      onMove
    );

    window.removeEventListener(
      "mouseup",
      onUp
    );
  }

  window.addEventListener(
    "mousemove",
    onMove
  );

  window.addEventListener(
    "mouseup",
    onUp
  );
}
async function analyzeMdp() {
  const file =
    mdpVideoRef.current?.files?.[0];

  if (!file) {
    alert("Choisis une vidéo MDP.");
    return;
  }

  setLoading(true);

  try {
    const formData = new FormData();

    formData.append("video", file);

    formData.append(
      "conductor_type",
      conductorType
    );

    const response = await axios.post(
      `${API}/analyze-mdp`,
      formData,
      {
        headers: {
          "Content-Type":
            "multipart/form-data",
        },
      }
    );

    setRows(
      response.data.rows || []
    );

    setAcrHits([]);

    setSelectedIndex(null);

  } catch (error) {
    console.error(
      "ERREUR ANALYSE MDP:",
      error
    );

    alert(
      "Erreur pendant l'analyse MDP."
    );

  } finally {
    setLoading(false);
  }
}
async function saveProjectExcel() {
  if (!rows.length) {
    alert("Aucun projet à sauvegarder.");
    return;
  }

  const formData = new FormData();

  formData.append(
    "rows_json",
    JSON.stringify(rows)
  );

  formData.append(
    "metadata_json",
    JSON.stringify({
      mode,
      conductorType,
      videoName:
        classicVideoRef.current?.files?.[0]?.name ||
        mdpVideoRef.current?.files?.[0]?.name ||
        "",
      savedAt: new Date().toISOString(),
    })
  );

  const response = await fetch(
    `${API}/save-project-excel`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error("Erreur sauvegarde projet");
  }

  const blob = await response.blob();

  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");

  a.href = url;
  a.download = "Projet_Emission.xlsx";

  a.click();

  window.URL.revokeObjectURL(url);
}
   
 

  function deleteRow(index) {
    setRows(rows.filter((_, i) => i !== index));
  }
async function enrichSacem() {
  if (!rows.length) {
    alert("Aucun titre à enrichir.");
    return;
  }

  const formData = new FormData();
  formData.append("rows_json", JSON.stringify(rows));

  const mappingFile =
    classicMappingRef.current?.files?.[0];

  if (mappingFile) {
    formData.append("mapping", mappingFile);
  }

  setLoading(true);

  try {
    const res = await axios.post(
      `${API}/enrich-sacem`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    setRows(res.data.rows || []);
  } catch (err) {
    console.error(err);
    alert("Erreur SACEM.");
  } finally {
    setLoading(false);
  }
} // ferme enrichSacem
function buildSacemSearchUrl(row) {
  const title = String(row?.title || "").trim();
  const artist = String(row?.artist || "").trim();

  const query = artist
    ? `${title},${artist}`
    : title;

  return (
    "https://www.repertoire.sacem.fr/resultats" +
    "?filters=titles,parties" +
    "&query=" +
    encodeURIComponent(query) +
    "#searchBtn"
  );
}

return (
  <div
    className={`app ${
      page === "history"
        ? "app-history"
        : ""
    }`}
  >
   <aside className="sidebar">
  <div className="sidebar-brand">
    <h2>Music Rights</h2>
    <span>Rights workflow</span>
  </div>

  <nav className="sidebar-nav">
    <button
      className={page === "workspace" ? "nav-btn active" : "nav-btn"}
      onClick={() => setPage("workspace")}
    >
      Projet
    </button>

    <button
      className={page === "history" ? "nav-btn active" : "nav-btn"}
      onClick={() => {
        setPage("history");
        loadProjects();
      }}
    >
      Historique émissions
    </button>

    <button
      className={page === "history-mdp" ? "nav-btn active" : "nav-btn"}
      onClick={() => {
        setPage("history-mdp");
        loadProjects();
      }}
    >
      Historique MDP
    </button>
  </nav>

  <div className="sidebar-section">
    <span className="sidebar-label">Type de projet</span>

    <div className="mode-switch">
      <button
        className={mode === "mdp" ? "mode-btn active" : "mode-btn"}
        onClick={() => resetWorkspace("mdp")}
      >
        Mot de Passe / MDP
      </button>

      <button
        className={mode === "classic" ? "mode-btn active" : "mode-btn"}
        onClick={() => resetWorkspace("classic")}
      >
        Émission classique
      </button>
    </div>
  </div>

  {mode === "classic" && (
    <div className="sidebar-section">
      <span className="sidebar-label">Analyse</span>

      <label className="field-label">Vidéo</label>
      <input
        ref={classicVideoRef}
        type="file"
        accept="video/*"
        onChange={onVideoFile}
      />

      <label className="field-label">
        Excel correspondance
      </label>
      <input
        ref={classicMappingRef}
        type="file"
        accept=".xlsx,.csv"
      />

      <label className="field-label">Intro fixe</label>
      <select
        value={classicIntro}
        onChange={(e) => setClassicIntro(e.target.value)}
      >
        <option value="NONE">Aucune</option>
        <option value="GEN_TALENT">Générique Talent</option>
        <option value="GEN_ADP">Générique ADP</option>
        <option value="AUTO">Détection automatique</option>
      </select>

      

      <button
        className="primary-btn"
        onClick={analyzeClassic}
        disabled={loading}
      >
        Analyser ACRCloud
      </button>

      <button
        className="secondary-btn"
        onClick={enrichSacem}
        disabled={!rows.length}
      >
        Remplir SACEM
      </button>

      <button
        className="secondary-btn"
        onClick={downloadM6}
        disabled={!rows.length}
      >
        Télécharger Excel M6
      </button>
    </div>
  )}

  {mode === "mdp" && (
    <div className="sidebar-section">
      <span className="sidebar-label">Analyse MDP</span>

      <label className="field-label">Vidéo</label>
      <input
        ref={mdpVideoRef}
        type="file"
        accept="video/*"
        onChange={onVideoFile}
      />

      <label className="field-label">
        Excel correspondance
      </label>
      <input
        ref={mdpMappingRef}
        type="file"
        accept=".xlsx,.csv"
      />

      <select
        value={conductorType}
        onChange={(e) => setConductorType(e.target.value)}
      >
        <option>Lundi-Jeudi</option>
        <option>Vendredi</option>
      </select>

      <button
        className="primary-btn"
        onClick={analyzeMdp}
        disabled={loading}
      >
        Analyser MDP
      </button>
    </div>
  )}

  {mode && (
    <div className="sidebar-section sidebar-project">
      <span className="sidebar-label">Projet</span>

      <input
        value={projectName}
        onChange={(e) => setProjectName(e.target.value)}
        placeholder="Nom de l’émission"
      />

      <button
        className="save-btn"
        onClick={saveProject}
      >
        {currentProjectId
          ? "Mettre à jour le projet"
          : "Sauvegarder le projet"}
      </button>
    </div>
  )}
</aside>
 <main>
  {page === "history" ? (
    <HistoryPage
      projects={projects.filter(
        (project) => project.mode === "classic"
      )}
      onOpen={openProject}
      onDelete={deleteProject}
      onBack={() => setPage("workspace")}
      title="Historique des émissions"
    />
  ) : page === "history-mdp" ? (
    <HistoryPage
      projects={projects.filter(
        (project) => project.mode === "mdp"
      )}
      onOpen={openProject}
      onDelete={deleteProject}
      onBack={() => setPage("workspace")}
      title="Historique MDP"
    />
  ) : (
  <div className="main-container">
      {!mode && (
        <div className="home">
          <h1>Choisis un mode</h1>
          <p>
            MDP pour Mot de Passe, émission classique pour
            ACRCloud + SACEM + export M6.
          </p>
        </div>
      )}

      {videoUrl && (
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          className="video"
          onTimeUpdate={(e) =>
            setCurrentTime(e.currentTarget.currentTime)
          }
        />
      )}
         
  
  {rows.length > 0 && (
  <section className="pro-timeline-card">
    <div className="pro-timeline-header">
      <div>
        <h3>Timeline</h3>
        <span>{rows.length} segment(s)</span>
      </div>

      <div className="timeline-zoom">
        <button
          type="button"
          onClick={() =>
            setPixelsPerSecond((value) =>
              Math.max(1, value - 1)
            )
          }
        >
          −
        </button>

        <input
          type="range"
          min="1"
          max="30"
          value={pixelsPerSecond}
          onChange={(event) =>
            setPixelsPerSecond(Number(event.target.value))
          }
        />

        <button
          type="button"
          onClick={() =>
            setPixelsPerSecond((value) =>
              Math.min(30, value + 1)
            )
          }
        >
          +
        </button>

        <strong>{pixelsPerSecond}px/s</strong>
      </div>
    </div>

    <div
      className="pro-timeline-scroll"
      onScroll={(event) =>
        setTimelineScrollLeft(event.currentTarget.scrollLeft)
      }
    >
      <div
        className="pro-timeline-content"
        style={{
          width: `${timelineWidth()}px`,
        }}
      >
        <div className="timeline-ruler">
          {buildTimelineTicks().map((sec) => (
            <div
              key={sec}
              className="timeline-tick"
              style={{
                left: `${sec * pixelsPerSecond}px`,
              }}
            >
              <span>{formatTimelineLabel(sec)}</span>
            </div>
          ))}
        </div>

        <div
          className="timeline-tracks"
          onDoubleClick={(event) => {
            if (event.target.closest(".pro-segment")) {
              return;
            }

            const rect =
              event.currentTarget.getBoundingClientRect();

            const x =
              event.clientX -
              rect.left +
              timelineScrollLeft;

            addRowAtTime(x / pixelsPerSecond);
          }}
        >
          <div
            className="pro-playhead"
            style={{
              left: `${currentTime * pixelsPerSecond}px`,
            }}
          >
            <span />
          </div>

          {rows.map((row, index) => {
            const start = Number(row.start_sec || 0);
            const end = Number(row.end_sec || 0);
            const duration = Math.max(1, end - start);
            const lane = laneForSegment(row, index);
            const quality = getQualityStatus(row);

            return (
              <div
                key={`${row.index ?? index}-${start}-${end}`}
                className={`pro-segment ${colorClassForTitle(
  row.title
)} pro-segment-${quality.code} ${
  selectedIndex === index ? "selected" : ""
}`}
                style={{
                  left: `${start * pixelsPerSecond}px`,
                  width: `${Math.max(
                    12,
                    duration * pixelsPerSecond
                  )}px`,
                  top: `${lane * 46 + 12}px`,
                }}
                title={`${row.title} — ${row.time_in} → ${row.time_out}`}
                onClick={(event) => {
                  event.stopPropagation();
                  selectRow(index);
                }}
                onMouseDown={(event) =>
                  onMoveProSegment(event, index)
                }
              >
                <span
                  className="pro-resize-handle left"
                  onMouseDown={(event) =>
                    onResizeProLeft(event, index)
                  }
                />

                <div className="pro-segment-content">
                  <strong>{row.title}</strong>

                  <small>
                    {row.time_in} → {row.time_out}
                  </small>
                </div>

                <span
                  className="pro-resize-handle right"
                  onMouseDown={(event) =>
                    onResizeProRight(event, index)
                  }
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  </section>
)}

 
    
{selectedIndex !== null && rows[selectedIndex] && (
  <div className="properties-panel">
    <h3>Propriétés du segment</h3>

    <label>Titre</label>
    <input
      value={rows[selectedIndex].title}
      onChange={(e) => updateSelected("title", e.target.value)}
    />

    <label>TIME IN</label>
    <input
      value={rows[selectedIndex].time_in}
      onChange={(e) => updateSelected("time_in", e.target.value)}
    />

    <label>TIME OUT</label>
    <input
      value={rows[selectedIndex].time_out}
      onChange={(e) => updateSelected("time_out", e.target.value)}
    />
    <label>Compositeur</label>
<input
  value={rows[selectedIndex].compositeur || ""}
  onChange={(e) => updateSelected("compositeur", e.target.value)}
/>

<label>Éditeur</label>
<input
  value={rows[selectedIndex].editeur || ""}
  onChange={(e) => updateSelected("editeur", e.target.value)}
/>

<label>ISWC</label>
<input
  value={rows[selectedIndex].code_iswc || ""}
  onChange={(e) => updateSelected("code_iswc", e.target.value)}
/>

<label>ISRC</label>
<input
  value={rows[selectedIndex].code_isrc || ""}
  onChange={(e) => updateSelected("code_isrc", e.target.value)}
/>
<div className="validation-actions">
  <button
    className="validate-button"
    onClick={() => {
      if (selectedIndex === null) return;

      setRows((prev) =>
        prev.map((row, index) =>
          index === selectedIndex
            ? {
                ...row,
                statut_validation: "validated",
              }
            : row
        )
      );
    }}
  >
    ✓ Valider
  </button>

  <button
    className="review-button"
    onClick={() => {
      if (selectedIndex === null) return;

      setRows((prev) =>
        prev.map((row, index) =>
          index === selectedIndex
            ? {
                ...row,
                statut_validation: "review",
              }
            : row
        )
      );
    }}
  >
   
  </button>
</div>

<label>Répertoire SACEM</label>

{selectedRow?.url_sacem && (
  <a
    href={buildSacemSearchUrl(selectedRow)}
    target="_blank"
    rel="noopener noreferrer"
    className="sacem-link"
  >
    🔎 Ouvrir dans le répertoire SACEM
  </a>
)}
 

  {!selectedRow?.url_sacem &&
    selectedRow?.url_sacem_candidate && (
      <a
        href={selectedRow.url_sacem_candidate}
        target="_blank"
        rel="noopener noreferrer"
        className="sacem-link candidate"
      >
        ⚠️ Voir le candidat SACEM
      </a>
    )}

  {/* Absolument aucun résultat */}
  {!selectedRow?.url_sacem &&
    !selectedRow?.url_sacem_candidate && (
      <span className="sacem-no-link">
        Aucun lien SACEM disponible
      </span>
    )}

  


   {mode === "mdp" ? (
  <button onClick={() => applyShift(selectedIndex)}>
    Appliquer et décaler la suite
  </button>
) : (
  <button onClick={
    () => applyOnlyThisRow(selectedIndex)}>
    Appliquer uniquement ce titre
  </button>
)}

    <button onClick={() => addRowAfter(selectedIndex)}>
      Ajouter après
    </button>

    <button onClick={() => deleteRow(selectedIndex)}>
      Supprimer
    </button>
  </div>
)}
     {videoUrl && (
  <div className="waveform-card">
    <h3>Waveform audio</h3>
    <div ref={waveformRef} />
  </div>
)}

        {mode && (
          <>
            <h1>{mode === "mdp" ? "Timeline MDP" : "Timeline émission classique"}</h1>

            <div className="table">
              {rows.map((row, index) => {
               const quality = getQualityStatus(row);
              return (
                <div
                  className={`row row-${quality.code}`}
                  key={index}
                >
                  <button onClick={() => selectRow(index)}>▶</button>

                  <input
                    value={row.title}
                    onChange={(e) => updateRow(index, "title", e.target.value)}
                  />

                  <input
                    value={row.time_in}
                    onChange={(e) => updateRow(index, "time_in", e.target.value)}
                  />

                  <input
                    value={row.time_out}
                    onChange={(e) => updateRow(index, "time_out", e.target.value)}
                  />

                  <span>{row.duration}</span>
                  <span
  className={`quality-badge quality-${quality.code}`}
>
  {quality.label}
</span>
                  {(() => {
  const quality = getQualityStatus(row);

  return (
    <span
      className={`quality-badge ${quality.className}`}
    >
      {quality.label}
    </span>
  );
})()}

                  {mode === "mdp" ? (
  <button onClick={() => applyShift(index)}>Décaler suite</button>
) : (
  <button onClick={() => applyOnlyThisRow(index)}>Appliquer</button>
)}
                  <button onClick={() => addRowAfter(index)}>+</button>
                  <button onClick={() => deleteRow(index)}>Supprimer</button>
                    </div>
  );
})}
            </div>
            
           {mode === "mdp" && (
  <div className="summary-card">
    <h2>Somme des durées par titre</h2>

    {totalsByTitle().map((item) => (
      <div className="summary-row" key={item.title}>
        <span>{item.title}</span>
        <strong>{item.duration}</strong>
      </div>
    ))}
  </div>
)}

            {mode === "classic" && (
              <>
                <h2>Hits ACRCloud nettoyés</h2>

                <div className="acr-hits">
                  {acrHits.map((h, i) => (
                    <div key={i}>
                      {h.start_sec}s → {h.end_sec}s — {h.title} / score {h.score}
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
          </div>
)}
       </main>
    </div>
  );
}


export default App;
