import React from 'react';

const StatCard = ({ title, value, icon: Icon, colorClass, unit = "" }) => {
  return (
    <div className={`cyber-border p-6 rounded-lg transition-all duration-300 hover:border-cyber-cyan`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-400 text-sm font-bold uppercase tracking-widest">{title}</span>
        <Icon className={colorClass} size={24} />
      </div>
      <div className="flex items-baseline gap-2">
        <h2 className={`text-4xl font-black ${colorClass} tracking-tighter`}>
          {value}
        </h2>
        <span className="text-gray-500 font-bold">{unit}</span>
      </div>
    </div>
  );
};

export default StatCard;