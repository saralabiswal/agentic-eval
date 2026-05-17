import {
  BarChart3,
  Boxes,
  FileText,
  Gauge,
  GitCompare,
  Info,
  Play,
  Scale,
  Settings
} from "lucide-react";
import { NavLink, Route, Routes } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getConfig } from "./api/client";
import { BenchmarkRunner } from "./pages/BenchmarkRunner";
import { Dashboard } from "./pages/Dashboard";
import { ModelComparison } from "./pages/ModelComparison";
import { ResultDetail } from "./pages/ResultDetail";
import { TestCases } from "./pages/TestCases";
import { Architecture } from "./pages/Architecture";
import { SettingsPage } from "./pages/SettingsPage";
import { About } from "./pages/About";
import { modelDisplayName } from "./utils/modelLabels";

const navGroups = [
  {
    label: "Understand",
    items: [
      { to: "/", label: "About", icon: Info, end: true },
      { to: "/architecture", label: "Architecture", icon: Boxes },
      { to: "/cases", label: "Test Cases", icon: BarChart3 }
    ]
  },
  {
    label: "Evaluate",
    items: [
      { to: "/benchmark", label: "1. Run Benchmark", icon: Play },
      { to: "/results/latest", label: "2. Review Results", icon: FileText },
      { to: "/compare", label: "3. Compare Models", icon: GitCompare },
      { to: "/dashboard", label: "4. Monitor Dashboard", icon: Gauge }
    ]
  },
  {
    label: "Configure",
    items: [{ to: "/settings", label: "Settings", icon: Settings }]
  }
];

export default function App(): JSX.Element {
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: getConfig });

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-row">
            <div className="logo-icon">
              <Scale size={15} />
            </div>
            <div className="logo-name">agentic-eval</div>
          </div>
          <div className="logo-sub">Model Evaluation Framework</div>
        </div>
        <nav className="nav">
          {navGroups.map((group) => (
            <div className="nav-section" key={group.label}>
              <div className="nav-label">{group.label}</div>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    className="nav-item"
                    end={item.end}
                    key={item.to}
                    to={item.to}
                  >
                    <Icon size={14} />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="bar-right">
            <span className="pill">Judge: {modelDisplayName(config?.eval_judge_model)}</span>
            <span className="pill">System: {modelDisplayName(config?.sut_model)}</span>
            <NavLink className="button primary small" to="/benchmark">
              <Play size={13} />
              Run Benchmark
            </NavLink>
          </div>
        </header>
        <main className="page">
          <Routes>
            <Route path="/" element={<About />} />
            <Route path="/about" element={<About />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/benchmark" element={<BenchmarkRunner />} />
            <Route path="/results/:runId" element={<ResultDetail />} />
            <Route path="/compare" element={<ModelComparison />} />
            <Route path="/architecture" element={<Architecture />} />
            <Route path="/cases" element={<TestCases />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
