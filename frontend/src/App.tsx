import { Route, Routes } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { Overview } from "@/pages/Overview";
import { Queue } from "@/pages/Queue";
import { Investigation } from "@/pages/Investigation";
import { ModelMonitoring } from "@/pages/ModelMonitoring";
import { Audit } from "@/pages/Audit";

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/investigations" element={<Queue />} />
        <Route path="/investigations/:txId" element={<Investigation />} />
        <Route path="/model-monitoring" element={<ModelMonitoring />} />
        <Route path="/audit" element={<Audit />} />
      </Routes>
    </Shell>
  );
}
