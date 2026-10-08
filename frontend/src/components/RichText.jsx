// Renders AI text safely (no innerHTML): paragraphs, bullets, **bold**, [Page N] tags, markdown tables.
function Inline({ text }) {
  return text.split(/(\[Page \d+\]|\*\*[^*]+\*\*)/).filter(Boolean).map((p, i) =>
    /^\[Page \d+\]$/.test(p) ? <span key={i} className="pg">{p.slice(1, -1)}</span>
    : /^\*\*.+\*\*$/.test(p) ? <strong key={i}>{p.slice(2, -2)}</strong>
    : p
  );
}

function Cell({ text }) {
  return text.split(/<br\s*\/?>/i).map((part, i) => {
    const t = part.trim();
    if (!t) return null;
    const bullet = /^[•\-*]\s/.test(t);
    return <div key={i} className={bullet ? "bl" : undefined}><Inline text={bullet ? t.slice(1).trim() : t} /></div>;
  });
}

function parse(text) {
  const lines = text.split("\n"), blocks = [];
  let i = 0, gap = false;
  while (i < lines.length) {
    const t = lines[i].trim();
    if (t.startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const r = lines[i].trim();
        if (!/^[\s|:-]+$/.test(r)) rows.push(r.replace(/^\||\|\s*$/g, "").split("|"));
        i++;
      }
      blocks.push({ type: "table", rows }); gap = false; continue;
    }
    i++;
    if (!t) { gap = true; continue; }
    const clean = t.replace(/<br\s*\/?>/gi, " ");
    const m = clean.match(/^([-*•]|\d+[.)])\s+(.*)/);
    const last = blocks[blocks.length - 1];
    if (m) {
      if (last && last.type === "ul" && !gap) last.items.push(m[2]);
      else blocks.push({ type: "ul", items: [m[2]] });
    } else blocks.push({ type: "p", text: clean.replace(/^#+\s*/, "") });
    gap = false;
  }
  return blocks;
}

export default function RichText({ text }) {
  return parse(text).map((b, i) => {
    if (b.type === "p") return <p key={i}><Inline text={b.text} /></p>;
    if (b.type === "ul") return <ul key={i}>{b.items.map((t, j) => <li key={j}><Inline text={t} /></li>)}</ul>;
    const [head, ...body] = b.rows;
    return (
      <div className="tw" key={i}>
        <table>
          <thead><tr>{head.map((c, j) => <th key={j}><Cell text={c.trim()} /></th>)}</tr></thead>
          <tbody>{body.map((r, j) => <tr key={j}>{r.map((c, k) => k === 0 ? <th key={k}><Cell text={c.trim()} /></th> : <td key={k}><Cell text={c.trim()} /></td>)}</tr>)}</tbody>
        </table>
      </div>
    );
  });
}
