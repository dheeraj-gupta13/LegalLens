import { useEffect, useRef, useState } from "react";
import { api } from "../api/client.js";
import RichText from "./RichText.jsx";
import { useToast } from "./Toast.jsx";

const STARTERS = ["When can this agreement be ended?", "What are my main obligations?", "Are there any fees or penalties?", "What are the important dates?"];

function Message({ m }) {
  const [open, setOpen] = useState(null);
  return (
    <div className={"msg " + m.role}>
      <RichText text={m.content} />
      {m.sources?.length > 0 && (
        <div className="srcs">Found on
          {m.sources.map((s) => (
            <span key={s.page} style={{ display: "contents" }}>
              <button className="chip" onClick={() => setOpen(open === s.page ? null : s.page)}>Page {s.page}</button>
              {open === s.page && <div className="quote" style={{ display: "block" }}>“{s.snippet.trim()}…”</div>}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ChatView({ doc }) {
  const toast = useToast();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [text, setText] = useState("");
  const viewRef = useRef(null);

  useEffect(() => {
    let live = true;
    setLoading(true); setMessages([]);
    api.listMessages(doc.id).then((d) => live && setMessages(d.items)).catch((e) => toast(e.message)).finally(() => live && setLoading(false));
    return () => { live = false; };
  }, [doc.id, toast]);

  useEffect(() => { viewRef.current?.scrollTo({ top: viewRef.current.scrollHeight }); }, [messages, pending]);

  const ask = async (q) => {
    q = q.trim();
    if (!q || pending) return;
    setText(""); setPending(true);
    setMessages((m) => [...m, { id: "tmp" + Date.now(), role: "user", content: q }]);
    try { const answer = await api.ask(doc.id, q); setMessages((m) => [...m, answer]); }
    catch (e) { toast(e.message); }
    finally { setPending(false); }
  };

  return (
    <>
      <section className="view" ref={viewRef}>
        <div className="wrap">
          {!loading && !messages.length && !pending && (
            <div className="hello">
              <h3>What do you want to know?</h3>
              <p>Answers come only from this document, with the page they were found on.</p>
              <div className="starters">{STARTERS.map((s) => <button key={s} onClick={() => ask(s)}>{s}</button>)}</div>
            </div>
          )}
          {messages.map((m) => <Message key={m.id} m={m} />)}
          {pending && <div className="msg assistant"><div className="dots"><i /><i /><i /></div></div>}
        </div>
      </section>
      <div className="composer">
        <form onSubmit={(e) => { e.preventDefault(); ask(text); }}>
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask about this document" autoComplete="off" />
          <button disabled={pending}>Ask</button>
        </form>
      </div>
    </>
  );
}
