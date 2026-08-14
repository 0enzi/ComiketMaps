import { useEffect, useState } from "react";
import { clearDiagnostics, diagnosticReport, subscribeDiagnostics } from "../data/diagnostics";

export default function DiagnosticsPanel() {
  const [open, setOpen] = useState(false);
  const [report, setReport] = useState(() => diagnosticReport());
  const [copyStatus, setCopyStatus] = useState("");

  useEffect(() => subscribeDiagnostics(() => setReport(diagnosticReport())), []);

  const copyReport = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
      setCopyStatus("Copied");
    } catch {
      setCopyStatus("Long-press the log to copy");
    }
  };

  return <>
    <button className="diagnostics-toggle" type="button" onClick={() => setOpen((value) => !value)}>Debug {report.entries.length}</button>
    {open && <aside className="diagnostics-panel" aria-label="On-device diagnostics">
      <header>
        <strong>Device diagnostics</strong>
        <div>
          <button type="button" onClick={copyReport}>Copy</button>
          <button type="button" onClick={() => clearDiagnostics()}>Clear</button>
          <button type="button" onClick={() => setOpen(false)}>Close</button>
        </div>
      </header>
      {copyStatus && <small>{copyStatus}</small>}
      <textarea readOnly value={JSON.stringify(report, null, 2)} onFocus={(event) => event.currentTarget.select()} />
    </aside>}
  </>;
}
