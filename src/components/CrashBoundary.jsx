import React from "react";
import { diagnosticReport, recordDiagnostic } from "../data/diagnostics";

export default class CrashBoundary extends React.Component {
  state = { error: null, report: "" };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    recordDiagnostic("react-crash", {
      name: error?.name,
      message: error?.message,
      stack: error?.stack,
      componentStack: info.componentStack,
    });
    this.setState({ report: JSON.stringify(diagnosticReport(), null, 2) });
  }

  render() {
    if (!this.state.error) return this.props.children;
    const report = this.state.report || JSON.stringify(diagnosticReport(), null, 2);
    return <main className="crash-screen">
      <h1>Comiket Maps crashed</h1>
      <p>{this.state.error.message || String(this.state.error)}</p>
      <p>Screenshot this screen—the diagnostic log below contains the actual error.</p>
      <textarea aria-label="Crash diagnostics" readOnly value={report} onFocus={(event) => event.currentTarget.select()} />
      <button type="button" onClick={() => window.location.reload()}>Reload</button>
    </main>;
  }
}
