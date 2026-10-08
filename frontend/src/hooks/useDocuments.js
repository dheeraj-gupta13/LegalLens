import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useToast } from "../components/Toast.jsx";

export function useDocuments() {
  const toast = useToast();
  const [docs, setDocs] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [uploading, setUploading] = useState(null); // filename while indexing

  const reload = useCallback(async (selectId) => {
    try {
      const { items } = await api.listDocuments();
      setDocs(items);
      setCurrentId((cur) => {
        const want = selectId ?? cur;
        return items.some((d) => d.id === want) ? want : items[0]?.id ?? null;
      });
    } catch (e) { toast(e.message); }
  }, [toast]);

  useEffect(() => { reload(); }, [reload]);

  const upload = async (file) => {
    if (!file) return;
    setUploading(file.name);
    try { const doc = await api.uploadDocument(file); await reload(doc.id); }
    catch (e) { toast(e.message); }
    finally { setUploading(null); }
  };

  const remove = async (doc) => {
    if (!window.confirm(`Delete ${doc.filename}?`)) return;
    try { await api.deleteDocument(doc.id); await reload(); } catch (e) { toast(e.message); }
  };

  return { docs, currentId, setCurrentId, current: docs.find((d) => d.id === currentId), uploading, upload, remove };
}
