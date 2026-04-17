import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Activity, Gauge, AlertTriangle, ShieldCheck, Cpu, History } from 'lucide-react';
import StatCard from './components/StatCard';
import RealTimeChart from './components/RealTimeChart';

//  Backend API
const API_URL = "http://127.0.0.1:8000/api/data";
// const API_URL = "https://speed-limit-system.onrender.com/api/process-frame";

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

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const lastViolationRef = useRef(false);

  // 🎥 Start webcam
  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;

          // force play (fixes stuck loading issue)
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

  // 🚀 Real-time frame sending loop
  useEffect(() => {
    const interval = setInterval(async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (!video || !canvas || !video.videoWidth) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0);

      canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
          const response = await axios.post(API_URL, formData, {
            headers: {
              "Content-Type": "multipart/form-data"
            }
          });

          const newData = response.data;
          setData(newData);

          // 📊 Update charts
          setSpeedHistory(prev => [...prev.slice(1), newData.current_speed || 0]);
          setFpsHistory(prev => [...prev.slice(1), newData.fps || 0]);

          // 🚨 Detect violation (only once per event)
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
        }
      }, "image/jpeg");

    }, 200); // 🔥 5 FPS (adjust 100–500ms)

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-cyber-dark text-white cyber-grid scanline-container font-mono">

      {/* Header */}
      <header className="mb-8 flex flex-col items-center border-b border-cyber-cyan/20 pb-4">
        <h1 className="text-4xl font-black italic neon-text-cyan text-cyber-cyan">
          Speed Limit Sign Detection System
        </h1>
      </header>

      {/* 🎥 LIVE CAMERA PREVIEW */}
      <div className="flex justify-center mb-6">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          onLoadedMetadata={() => {
            videoRef.current?.play();
          }}
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
          <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-tighter">
            Live Speed Analytics
          </h3>
          <RealTimeChart dataArray={speedHistory} label="Speed" color="#00f3ff" />
        </div>

        <div className="cyber-border p-4 rounded-lg h-64">
          <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-tighter">
            Engine Performance (FPS)
          </h3>
          <RealTimeChart dataArray={fpsHistory} label="FPS" color="#ff00ff" />
        </div>
      </div>

      {/* Violation Table */}
      <div className="cyber-border rounded-lg overflow-hidden">
        <div className="bg-cyber-cyan/10 p-4 border-b border-cyber-cyan/20 flex items-center gap-2">
          <History size={18} className="text-cyber-cyan" />
          <h3 className="font-bold uppercase tracking-widest text-sm">
            Violation History Log
          </h3>
        </div>

        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-gray-500 text-xs uppercase bg-black/40">
              <th className="p-4">Timestamp</th>
              <th className="p-4">Recorded Speed</th>
              <th className="p-4">Zone Limit</th>
              <th className="p-4 text-right">Severity</th>
            </tr>
          </thead>

          <tbody>
            {violations.length === 0 ? (
              <tr>
                <td colSpan="4" className="p-10 text-center text-gray-600 italic">
                  No violations recorded in this session.
                </td>
              </tr>
            ) : (
              violations.map(v => (
                <tr key={v.id} className="border-t border-white/5 hover:bg-white/5 transition-colors">
                  <td className="p-4 font-mono text-cyber-cyan">{v.time}</td>
                  <td className="p-4 font-bold">{v.speed} km/h</td>
                  <td className="p-4 text-gray-400">{v.limit} km/h</td>
                  <td className="p-4 text-right">
                    <span className="px-2 py-1 bg-cyber-red/20 text-cyber-red text-[10px] font-bold rounded border border-cyber-red/40">
                      {v.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}

export default App;