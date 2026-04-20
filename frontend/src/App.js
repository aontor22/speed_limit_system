import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Gauge, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';
import StatCard from './components/StatCard';
import RealTimeChart from './components/RealTimeChart';

// Backend API
const API_URL = "https://speed-limit-system.onrender.com/api/process-frame";

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
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true
        });

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
  }, []);

  // 🚀 Optimized frame sending loop
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
          const response = await axios.post(API_URL, formData, {
            headers: {
              "Content-Type": "multipart/form-data"
            },
            timeout: 10000 // ✅ prevent hanging
          });

          const newData = response.data;
          setData(newData);

          // 📊 Charts
          setSpeedHistory(prev => [...prev.slice(1), newData.current_speed || 0]);
          setFpsHistory(prev => [...prev.slice(1), newData.fps || 0]);

          // 🚨 Violation tracking
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

    }, 1000); // ✅ FIXED: 1 request/sec (was 200ms)

    return () => clearInterval(interval);
  }, [currentMode]);

  // ============================
  // Upload Handlers
  // ============================
  const handleFileUpload = async (event, type) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const endpoint = type === "image" ? "/upload/image" : "/upload/video";

      await axios.post(
        `https://speed-limit-system.onrender.com${endpoint}`,
        formData,
        { timeout: 20000 }
      );

      setCurrentMode(type);
      alert(`${type.toUpperCase()} uploaded successfully`);

    } catch (err) {
      console.error("Upload failed:", err.message);
    }
  };

  const switchToWebcam = async () => {
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
  };

  return (
    <div className="min-h-screen bg-cyber-dark text-white cyber-grid scanline-container font-mono">

      {/* Header */}
      <header className="mb-8 flex flex-col items-center border-b border-cyber-cyan/20 pb-4">
        <h1 className="text-4xl font-black italic neon-text-cyan text-cyber-cyan">
          Speed Limit Sign Detection System
        </h1>
      </header>

      {/* Control Panel */}
      <div className="mb-6 flex gap-4 justify-center">

        <button
          onClick={switchToWebcam}
          className="px-4 py-2 border border-cyber-cyan text-cyber-cyan hover:bg-cyber-cyan/10"
        >
          Webcam
        </button>

        <label className="cursor-pointer px-4 py-2 border border-white hover:bg-white/10">
          Upload Image
          <input
            type="file"
            hidden
            accept="image/*"
            onChange={(e) => handleFileUpload(e, "image")}
          />
        </label>

        <label className="cursor-pointer px-4 py-2 border border-white hover:bg-white/10">
          Upload Video
          <input
            type="file"
            hidden
            accept="video/*"
            onChange={(e) => handleFileUpload(e, "video")}
          />
        </label>

      </div>

      {/* Camera */}
      <div className="flex justify-center mb-6">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-80 h-60 rounded-lg border border-cyber-cyan bg-black"
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard title="Speed" value={data.current_speed} unit="KM/H" icon={Gauge} colorClass="text-cyber-cyan" />
        <StatCard title="Limit" value={data.speed_limit} unit="KM/H" icon={ShieldCheck} colorClass="text-cyber-green" />
        <StatCard title="FPS" value={data.fps} icon={Cpu} colorClass="text-cyber-magenta" />
        <StatCard title="Alerts" value={violations.length} icon={AlertTriangle} colorClass="text-cyber-red" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="cyber-border p-4 rounded-lg h-64">
          <h3 className="text-xs text-gray-400 mb-4 uppercase">Live Speed</h3>
          <RealTimeChart dataArray={speedHistory} label="Speed" color="#00f3ff" />
        </div>

        <div className="cyber-border p-4 rounded-lg h-64">
          <h3 className="text-xs text-gray-400 mb-4 uppercase">FPS</h3>
          <RealTimeChart dataArray={fpsHistory} label="FPS" color="#ff00ff" />
        </div>
      </div>

      {/* Table */}
      <div className="cyber-border rounded-lg overflow-hidden">
        <div className="bg-cyber-cyan/10 p-4">
          <h3 className="font-bold text-sm">Violation History</h3>
        </div>

        <table className="w-full text-left">
          <thead>
            <tr className="text-gray-500 text-xs">
              <th className="p-4">Time</th>
              <th className="p-4">Speed</th>
              <th className="p-4">Limit</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>

          <tbody>
            {violations.map(v => (
              <tr key={v.id}>
                <td className="p-4">{v.time}</td>
                <td className="p-4">{v.speed}</td>
                <td className="p-4">{v.limit}</td>
                <td className="p-4 text-cyber-red">{v.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}

export default App;
