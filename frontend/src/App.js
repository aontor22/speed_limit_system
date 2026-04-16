import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Gauge, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';
import StatCard from './components/StatCard';

const API_URL = "http://localhost:8000/api/data";

function App() {
  const [data, setData] = useState({
    current_speed: 0,
    speed_limit: 0,
    status: "Initializing...",
    fps: 0,
    violation_detected: false
  });
  const [violationCount, setViolationCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(API_URL);
        const newData = response.data;

        // Increment violation count if a new violation occurs
        if (newData.violation_detected && !data.violation_detected) {
          setViolationCount(prev => prev + 1);
        }

        setData(newData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    const interval = setInterval(fetchData, 500); // Poll every 500ms
    return () => clearInterval(interval);
  }, [data.violation_detected]);

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <header className="mb-10 flex flex-col items-center border-b border-cyber-cyan/20 pb-6">
        <h1 className="text-5xl font-black italic tracking-tighter neon-text-cyan text-cyber-cyan">
          TRAFFIC AI <span className="text-white">DASHBOARD</span>
        </h1>
        <p className="text-cyber-magenta font-mono tracking-widest mt-2 uppercase">
          Real-Time Speed Detection System v1.0
        </p>
      </header>

      {/* Main Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <StatCard 
          title="Current Speed" 
          value={data.current_speed} 
          unit="KM/H"
          icon={Gauge} 
          colorClass="text-cyber-cyan"
        />
        <StatCard 
          title="Speed Limit" 
          value={data.speed_limit > 0 ? data.speed_limit : "--"} 
          unit="KM/H"
          icon={ShieldCheck} 
          colorClass="text-cyber-green"
        />
        <StatCard 
          title="Total Violations" 
          value={violationCount} 
          icon={AlertTriangle} 
          colorClass={violationCount > 0 ? "text-cyber-red" : "text-gray-400"}
        />
        <StatCard 
          title="System FPS" 
          value={data.fps} 
          icon={Cpu} 
          colorClass="text-cyber-magenta"
        />
      </div>

      {/* Real-time Status Banner */}
      <div className={`p-4 rounded-md border-2 text-center font-black text-2xl transition-all duration-500 ${
        data.violation_detected 
        ? "bg-cyber-red/20 border-cyber-red text-cyber-red shadow-neon-red animate-pulse" 
        : "bg-cyber-green/20 border-cyber-green text-cyber-green"
      }`}>
        {data.violation_detected ? "VIOLATION DETECTED: PLEASE SLOW DOWN" : "SYSTEM STATUS: MONITORING SAFE"}
      </div>
    </div>
  );
}

export default App;