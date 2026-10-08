import { useState } from "react";
import { useAuth } from "./context/AuthContext.jsx";
import { useDocuments } from "./hooks/useDocuments.js";
import AuthPage from "./components/AuthPage.jsx";
import Sidebar from "./components/Sidebar.jsx";
import ChatView from "./components/ChatView.jsx";
import SummaryView from "./components/SummaryView.jsx";
import CompareView from "./components/CompareView.jsx";

const TABS = [["chat", "Chat"], ["summary", "Summary and risks"], ["compare", "Compare"]];

function Workspace() {
  const d = useDocuments();
  const [tab, setTab] = useState("chat");

  let view;
  if (d.uploading) view = <section className="view"><div className="wrap"><p className="loadmsg">Reading and indexing {d.uploading}…</p><div className="sk" /><div className="sk" /></div></section>;
  else if (tab === "compare") view = <CompareView docs={d.docs} />;
  else if (!d.current) view = <section className="view"><div className="wrap"><div className="hello"><h3>Upload a contract to get started</h3><p>Try a lease, job offer, insurance policy or terms of service.</p></div></div></section>;
  else if (tab === "chat") view = <ChatView key={d.current.id} doc={d.current} />;
  else view = <SummaryView key={d.current.id} doc={d.current} />;

  return (
    <div className="app">
      <Sidebar docs={d.docs} currentId={d.currentId} onSelect={d.setCurrentId} onUpload={d.upload} onDelete={d.remove} uploading={d.uploading} />
      <main className="main">
        <div className="top">
          <h2>{d.current?.filename ?? "Your documents"}</h2>
          <div className="tabs">{TABS.map(([k, l]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>)}</div>
        </div>
        {view}
        <div className="note">AI-generated explanations of your document. Not legal advice.</div>
      </main>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <Workspace /> : <AuthPage />;
}
