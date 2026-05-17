import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type LatencyChartProps = {
  data: Array<{ backend: string; latency: number }>;
};

export function LatencyChart({ data }: LatencyChartProps): JSX.Element {
  return (
    <div style={{ width: "100%", height: 220 }}>
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="backend" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="latency" fill="#2f6fdd" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
