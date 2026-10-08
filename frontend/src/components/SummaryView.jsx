import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useToast } from "./Toast.jsx";

const SEV = { high: "var(--hi)", medium: "var(--med)", low: "var(--lo)" };

function ListCard({ title, items }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {items.length ? <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul> : <p className="empty">Nothing found.</p>}
    </div>
  );
}

export default function SummaryView({ doc }) {
  const toast = useToast();
  const [a, setA] = useState(null);

  useEffect(() => {
    let live = true;
    setA(null);
    api.getAnalysis(doc.id).then((d) => live && setA(d)).catch((e) => toast(e.message));
    return () => { live = false; };
  }, [doc.id, toast]);

  if (!a) return (
    <section className="view"><div className="wrap">
      <p className="loadmsg">Analysing the document. The first run can take a minute.</p>
      <div className="sk" /><div className="sk" /><div className="sk" />
    </div></section>
  );

  const count = (k) => a.risky_clauses.filter((r) => r.severity.toLowerCase() === k).length;
  return (
    <section className="view"><div className="wrap">
      <div className="tiles">
        {[["high", "High risk"], ["medium", "Medium risk"], ["low", "Low risk"]].map(([k, l]) => (
          <div className="tile" key={k} style={{ "--c": SEV[k] }}><b>{count(k)}</b><span>{l} {count(k) === 1 ? "clause" : "clauses"}</span></div>
        ))}
      </div>
      <div className="card"><h3>In short</h3><p>{a.summary}</p></div>
      <div className="card">
        <h3>Clauses worth a closer look</h3>
        {!a.risky_clauses.length && <p className="empty">No risky clauses detected.</p>}
        {a.risky_clauses.map((r, i) => (
          <div className="risk" key={i} style={{ "--c": SEV[r.severity.toLowerCase()] || SEV.medium }}>
            <div className="q"><span className="pill">{r.severity.toLowerCase()}</span>{r.clause} <span className="pg">Page {r.page}</span></div>
            <div className="why">{r.explanation}</div>
          </div>
        ))}
      </div>
      <div className="grid">
        <ListCard title="Who is involved" items={a.parties} />
        <ListCard title="Key dates" items={a.key_dates} />
        <ListCard title="Your obligations" items={a.obligations} />
        <ListCard title="Penalties" items={a.penalties} />
        <ListCard title="Ending the agreement" items={a.termination_terms} />
      </div>
    </div></section>
  );
}
