type ConsistencyViewProps = {
  outputs: string[];
  matrix: number[][];
};

export function ConsistencyView({ outputs, matrix }: ConsistencyViewProps): JSX.Element {
  return (
    <div className="consistency-view">
      <div className="panel-title">Consistency Evidence</div>
      <p className="consistency-help">
        Run 1 to Run {outputs.length || matrix.length || 5} are repeated answers for the same
        customer case. The similarity matrix checks whether those answers stay stable across runs.
      </p>
      <table className="similarity-table" aria-label="Consistency similarity matrix">
        <tbody>
          {matrix.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {row.map((value, cellIndex) => (
                <td key={`cell-${rowIndex}-${cellIndex}`}>{value.toFixed(2)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="run-output-list">
        {outputs.length === 0 ? (
          <div className="empty-state">No consistency run outputs recorded.</div>
        ) : (
          outputs.map((output, index) => (
            <details className="run-output-card" key={`${output}-${index}`}>
              <summary>
                <span>Run {index + 1}</span>
                <span>{outputPreview(output)}</span>
              </summary>
              <pre className="run-output">{output}</pre>
            </details>
          ))
        )}
      </div>
    </div>
  );
}

function outputPreview(output: string): string {
  const riskLine = output.split("\n").find((line) => line.toLowerCase().includes("risk level"));
  if (riskLine) {
    return riskLine.replace(/\s+/g, " ").trim();
  }
  return output.slice(0, 90).replace(/\s+/g, " ").trim();
}
