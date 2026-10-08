import { createContext, useCallback, useContext, useState } from "react";

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const show = useCallback((message) => {
    const id = Date.now() + Math.random();
    setItems((x) => [...x, { id, message }]);
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 4500);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      {items.map((i) => <div key={i.id} className="toast" role="alert">{i.message}</div>)}
    </ToastContext.Provider>
  );
}
