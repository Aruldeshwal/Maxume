import React from "react";

interface QuotaRingProps {
  label: string;
  current: number;
  total: number;
  unit?: string;
  size?: number;
  strokeWidth?: number;
}

export const QuotaRing: React.FC<QuotaRingProps> = ({
  label,
  current,
  total,
  unit = "req/day",
  size = 90,
  strokeWidth = 6,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percentage = Math.min(100, Math.max(0, Math.round((current / (total || 1)) * 100)));
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-3 rounded-lg bg-background-card border border-border-subtle hover:border-border-strong transition-all">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="var(--border-subtle)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress Ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="var(--accent-crimson)"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-sm font-bold font-mono text-white" data-testid="quota-percentage">
            {percentage}%
          </span>
        </div>
      </div>
      <div className="mt-2 text-center">
        <div className="text-xs font-semibold text-text-primary tracking-tight">{label}</div>
        <div className="text-[10px] font-mono text-text-secondary">
          {current.toLocaleString()} / {total.toLocaleString()} {unit}
        </div>
      </div>
    </div>
  );
};

export default QuotaRing;
