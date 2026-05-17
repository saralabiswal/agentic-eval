type DimensionBadgeProps = {
  label: string;
  score: number;
  passed: boolean;
};

export function DimensionBadge({ label, score, passed }: DimensionBadgeProps): JSX.Element {
  const color = passed ? "var(--pass)" : score >= 0.75 ? "var(--warn)" : "var(--fail)";
  return (
    <span
      className="dim-chip"
      style={{
        color,
        borderColor: color,
        background: passed
          ? "rgba(16,185,129,.08)"
          : score >= 0.75
            ? "rgba(245,158,11,.08)"
            : "rgba(255,71,87,.08)"
      }}
    >
      {label} {score.toFixed(2)}
    </span>
  );
}
