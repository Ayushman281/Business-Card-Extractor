import { fields } from "../types/leads";
import type { CardResult, LeadField } from "../types/leads";

export function ResultsTable({ results, disabled, onEdit }: {
  results: CardResult[]; disabled: boolean;
  onEdit: (index: number, field: LeadField, value: string) => void;
}) {
  const successful = results.filter(result => result.status === "success" && result.lead);
  if (!successful.length) return null;
  return <div className="table-scroll" role="region" aria-label="Editable lead results" tabIndex={0}>
    <table>
      <caption className="sr-only">Extracted business card leads. Review and edit before downloading.</caption>
      <thead><tr><th scope="col">Source card</th>{fields.map(([field, label]) => <th key={field} scope="col">{label}</th>)}</tr></thead>
      <tbody>{successful.map(result => <tr key={result.index}>
        <th scope="row" className="source-cell">
          <span title={result.source_filename}>{result.source_filename}</span>
          <small>{(result.processing_time_ms / 1000).toFixed(1)}s</small>
          {result.warnings.map(warning => <small className="field-warning" key={warning}>{warning}</small>)}
        </th>
        {fields.map(([field, label]) => <td key={field}>
          <input aria-label={label + " for " + result.source_filename} value={result.lead?.[field] ?? ""}
            disabled={disabled} maxLength={500} placeholder="—" autoComplete="off"
            onChange={event => onEdit(result.index, field, event.target.value)} />
        </td>)}
      </tr>)}</tbody>
    </table>
  </div>;
}
