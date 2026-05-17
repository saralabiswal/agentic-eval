type ScoreGaugeProps = {
  label: string;
  value: number;
  detail?: string;
  color?: string;
};

export function ScoreGauge({
  label,
  value,
  detail = "",
  color = "var(--blue)"
}: ScoreGaugeProps): JSX.Element {
  const display = value > 1 ? String(value) : `${Math.round(value * 100)}%`;
  return (
    <div className="kpi" style={{ "--accent": color } as CSSProperties}>
      <div className="label">{label}</div>
      <div className="kpi-value">{display}</div>
      <div className="kpi-detail">{detail}</div>
    </div>
  );
}
import type { CSSProperties } from "react";
