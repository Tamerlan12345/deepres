import { useState, useEffect, memo } from 'react';
import mermaid from 'mermaid';
import DOMPurify from 'dompurify';

const MermaidChart = memo(({ chart }) => {
    const [svg, setSvg] = useState('');
    const [id] = useState(() => `mermaid-${Math.random().toString(36).substr(2, 9)}`);

    useEffect(() => {
      mermaid.render(id, chart).then((result) => {
          // SECURITY 🛡️: Sanitize generated SVG before rendering to prevent XSS
          const cleanSvg = DOMPurify.sanitize(result.svg);
          setSvg(cleanSvg);
      }).catch(err => {
          console.error("Mermaid error:", err);
          setSvg(`<div class="text-error">Error rendering diagram</div>`);
      });
    }, [chart, id]);

    return <div className="mermaid-container my-6 flex justify-center bg-brand-900/30 p-4 rounded-lg overflow-x-auto w-full max-w-full" dangerouslySetInnerHTML={{ __html: svg }} />;
});

export default MermaidChart;
