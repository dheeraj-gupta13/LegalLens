import { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Sidebar({ docs, currentId, onSelect, onUpload, onDelete, uploading }) {
  const { user, logout } = useAuth();
  const [over, setOver] = useState(false);

  return (
    <aside className="side">
      <div className="brand">Legal<span className="hl" style={{ color: "var(--ink)" }}>Lens</span></div>
      <label
        className={"drop" + (over ? " over" : "")}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); onUpload(e.dataTransfer.files[0]); }}
      >
        <strong>{uploading ? "Indexing…" : "Add a document"}</strong>
        <small>{uploading ?? "PDF, DOCX or TXT. Drop it here or click."}</small>
        <input type="file" accept=".pdf,.docx,.txt" hidden disabled={Boolean(uploading)}
               onChange={(e) => { onUpload(e.target.files[0]); e.target.value = ""; }} />
      </label>
      <div className="doclist">
        {!docs.length && <p className="nodocs">No documents yet. Add one to begin.</p>}
        {docs.map((d) => (
          <div key={d.id} className={"doc" + (d.id === currentId ? " on" : "")} onClick={() => onSelect(d.id)}>
            <div className="ico" />
            <div className="meta">
              <span className="name" title={d.filename}>{d.filename}</span>
              <small>{d.pages} {d.pages === 1 ? "page" : "pages"}</small>
            </div>
            <button className="x" title="Delete document" onClick={(e) => { e.stopPropagation(); onDelete(d); }}>Delete</button>
          </div>
        ))}
      </div>
      <div className="me"><span>{user.email}</span><button onClick={logout}>Log out</button></div>
    </aside>
  );
}
