import { useEffect, useState } from "react";

export function FilePreview({ file, onRemove, disabled }: { file: File; onRemove: () => void; disabled: boolean }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    const created = URL.createObjectURL(file);
    setUrl(created);
    return () => URL.revokeObjectURL(created);
  }, [file]);
  return <div className="file-card">
    <img src={url} alt={"Preview of " + file.name} />
    <div className="file-description"><strong title={file.name}>{file.name}</strong>
      <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span></div>
    <button className="remove-button" type="button" disabled={disabled} onClick={onRemove} aria-label={"Remove " + file.name}>×</button>
  </div>;
}
