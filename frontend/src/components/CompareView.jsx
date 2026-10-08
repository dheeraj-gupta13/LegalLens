import { useState } from "react";
import { api } from "../api/client.js";
import RichText from "./RichText.jsx";
import { useToast } from "./Toast.jsx";

export default function CompareView({ docs }) {
  const toast = useToast();
  const [a, setA] = useState(docs[0]?.id);
  const [b, setB] = useState(docs[1]?.id);
  const [state, setState] = useState({ busy: false, text: null });

  if (docs.length < 2) return (
    <section className="view"><div className="wrap"><div className="hello">
      <h3>Add a second document</h3><p>Upload two documents, such as two job offers, to see them side by side.</p>
    </div></div></section>
  );

  const run = async () => {
    setState({ busy: true, text: null });
    try { const d = await api.compare(Number(a), Number(b)); setState({ busy: false, text: d.comparison }); }
    catch (e) { toast(e.message); setState({ busy: false, text: null }); }
  };
  const Select = ({ value, onChange }) => (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {docs.map((d) => <option key={d.id} value={d.id}>{d.filename}</option>)}
    </select>
  );

  return (
    <section className="view"><div className="wrap">
      <div className="bar">
        <Select value={a} onChange={setA} /><span className="vs">vs</span><Select value={b} onChange={setB} />
        <button onClick={run} disabled={state.busy}>Compare</button>
      </div>
      {state.busy && <div className="card"><p className="loadmsg">Comparing. This can take a minute.</p><div className="sk" /><div className="sk" /></div>}
      {state.text && <div className="card cmp"><RichText text={state.text} /></div>}
    </div></section>
  );
}
