import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
<<<<<<< HEAD
import { Activity, Gauge, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';
import StatCard from './components/StatCard';
import RealTimeChart from './components/RealTimeChart';

// 🔗 API URLs
const API_BASE = "http://127.0.0.1:8000";
const FRAME_API = `${API_BASE}/api/process-frame`;
const HISTORY_API = `${API_BASE}/api/history`;
=======
import { Gauge, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';
import StatCard from './components/StatCard';
import RealTimeChart from './components/RealTimeChart';

// Backend API
const API_URL = "https://speed-limit-system.onrender.com/api/process-frame";
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f

function App() {
  const [data, setData] = useState({
    current_speed: 0,
    speed_limit: 0,
    status: "Safe",
    fps: 0,
    violation_detected: false,
    timestamp: ""
  });

  const [speedHistory, setSpeedHistory] = useState(new Array(30).fill(0));
  const [fpsHistory, setFpsHistory] = useState(new Array(30).fill(0));
  const [violations, setViolations] = useState([]);
  const [currentMode, setCurrentMode] = useState("webcam");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const lastViolationRef = useRef(false);

  // ✅ NEW: prevent overlapping requests
  const isSendingRef = useRef(false);

  // 🎥 Start webcam
  useEffect(() => {
    let stream;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
          };
        }
      } catch (err) {
        console.error("Camera error:", err);
      }
    };

    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

<<<<<<< HEAD
  // 🚀 Frame loop (ONLY webcam mode)
=======
  // 🚀 Optimized frame sending loop
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f
  useEffect(() => {
    const interval = setInterval(async () => {

      if (currentMode !== "webcam") return;

      // ❗ prevent spamming server
      if (isSendingRef.current) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (!video || !canvas || !video.videoWidth) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0);

      canvas.toBlob(async (blob) => {
        if (!blob) return;

        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        isSendingRef.current = true;

        try {
<<<<<<< HEAD
          const res = await axios.post(FRAME_API, formData);
          const newData = res.data;
=======
          const response = await axios.post(API_URL, formData, {
            headers: {
              "Content-Type": "multipart/form-data"
            },
            timeout: 10000 // ✅ prevent hanging
          });
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f

          setData(newData);

          setSpeedHistory(prev => [...prev.slice(1), newData.current_speed || 0]);
          setFpsHistory(prev => [...prev.slice(1), newData.fps || 0]);

          if (newData.status === "Violation" && !lastViolationRef.current) {
            const newRecord = {
              id: Date.now(),
              time: new Date().toLocaleTimeString(),
              speed: newData.current_speed,
              limit: newData.speed_limit,
              status: "OVER-SPEED"
            };

            setViolations(prev => [newRecord, ...prev].slice(0, 10));
            lastViolationRef.current = true;
          }

          if (newData.status === "Safe") {
            lastViolationRef.current = false;
          }

        } catch (err) {
          console.error("Frame send error:", err.message);
        } finally {
          isSendingRef.current = false;
        }

      }, "image/jpeg");

<<<<<<< HEAD
    }, 300);
=======
    }, 1000); // ✅ FIXED: 1 request/sec (was 200ms)
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f

    return () => clearInterval(interval);
  }, [currentMode]);

<<<<<<< HEAD
  // 📦 Fetch DB history
  const fetchHistory = async () => {
    try {
      const res = await axios.get(HISTORY_API);
      setViolations(res.data || []);
    } catch (err) {
      console.error("History fetch failed", err);
    }
  };

  // Load history once
  useEffect(() => {
    fetchHistory();
  }, []);

  // 📤 Upload handler (FIXED)
=======
  // ============================
  // Upload Handlers
  // ============================
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f
  const handleFileUpload = async (event, type) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const endpoint = type === "image" ? "/upload/image" : "/upload/video";
<<<<<<< HEAD
      await axios.post(`${API_BASE}${endpoint}`, formData);

      setCurrentMode(type);

      // 🧠 Wait for backend processing, then fetch results
      setTimeout(async () => {
        const res = await axios.get(`${API_BASE}/api/data`);
        setData(res.data);
        fetchHistory();
      }, 1000);

      alert(`${type.toUpperCase()} processed successfully`);
=======

      await axios.post(
        `https://speed-limit-system.onrender.com${endpoint}`,
        formData,
        { timeout: 20000 }
      );

      setCurrentMode(type);
      alert(`${type.toUpperCase()} uploaded successfully`);
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f

    } catch (err) {
      console.error("Upload failed:", err.message);
    }
  };

  // 🎥 Switch back to webcam
  const switchToWebcam = async () => {
<<<<<<< HEAD
    await axios.post(`${API_BASE}/api/set-webcam`);
    setCurrentMode("webcam");
=======
    try {
      await axios.post(
        "https://speed-limit-system.onrender.com/api/set-webcam",
        {},
        { timeout: 10000 }
      );

      setCurrentMode("webcam");

    } catch (err) {
      console.error("Switch mode error:", err.message);
    }
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f
  };

  return (
    <div className="min-h-screen bg-cyber-dark text-white font-mono">

      {/* Header */}
      <header className="mb-8 flex flex-col items-center border-b border-cyber-cyan/20 pb-4">
        <h1 className="text-4xl font-black italic text-cyber-cyan">
          Speed Limit Detection System
        </h1>
      </header>

<<<<<<< HEAD
      {/* CONTROL PANEL */}
=======
      {/* Control Panel */}
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f
      <div className="mb-6 flex gap-4 justify-center">

        <button onClick={switchToWebcam}
          className="px-4 py-2 border border-cyber-cyan text-cyber-cyan">
          Webcam
        </button>

        <label className="cursor-pointer px-4 py-2 border border-white">
          Upload Image
          <input type="file" hidden accept="image/*"
            onChange={(e) => handleFileUpload(e, "image")} />
        </label>

        <label className="cursor-pointer px-4 py-2 border border-white">
          Upload Video
          <input type="file" hidden accept="video/*"
            onChange={(e) => handleFileUpload(e, "video")} />
        </label>

      </div>

<<<<<<< HEAD
      {/* CAMERA */}
=======
      {/* Camera */}
>>>>>>> 7649f753494aa861a6e333284bef4c1909ec3e6f
      <div className="flex justify-center mb-6">
        <video ref={videoRef} autoPlay muted playsInline
          className="w-80 h-60 border border-cyber-cyan bg-black" />
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      {/* STATS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard title="Speed" value={data.current_speed} unit="KM/H" icon={Gauge} />
        <StatCard title="Limit" value={data.speed_limit} unit="KM/H" icon={ShieldCheck} />
        <StatCard title="FPS" value={data.fps} icon={Cpu} />
        <StatCard title="Alerts" value={violations.length} icon={AlertTriangle} />
      </div>

      {/* CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <RealTimeChart dataArray={speedHistory} label="Speed" />
        <RealTimeChart dataArray={fpsHistory} label="FPS" />
      </div>

      {/* TABLE */}
      <div className="border p-4">
        <h3 className="mb-2">Violation History</h3>
        <table className="w-full text-left">
          <thead>
            <tr>
              <th>Time</th>
              <th>Speed</th>
              <th>Limit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {violations.map((v, i) => (
              <tr key={i}>
                <td>{v.time || v.timestamp}</td>
                <td>{v.speed}</td>
                <td>{v.limit}</td>
                <td style={{ color: "red" }}>{v.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}

export default App;
