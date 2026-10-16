// Barra do topo do site (GitHub Pages): abas para trocar de página e os colaboradores do projeto.
// Cada página do site põe <site-barra atual="id-da-pagina"></site-barra> logo depois de <body>
// e carrega este arquivo (barra.js). Para incluir uma página nova, acrescente-a em PAGINAS.
// Os atributos opcionais largura e margem alinham a barra com o conteúdo da página
// (ex.: <site-barra atual="painel" largura="1240" margem="16">).
// A barra é desenhada dentro de um "shadow DOM", para que o estilo dela e o das páginas não se misturem.
(function () {
  const PAGINAS = [
    { id: 'poda', href: './', titulo: 'Onde podar agora' },
    { id: 'painel', href: 'painel-1746.html', titulo: 'Painel 1746' }
  ];
  const EQUIPE = [
    { nome: 'Heitor Morais', github: 'heitor-oss' },
    { nome: 'José Salgado', github: 'jssppedra-png' }
  ];
  const CSS = `
    :host{display:block;--b:#18221d;--t:#e4ece7;--m:#9fb1a7;--a:#5cc28f;--l:#2d3a33}
    @media (prefers-color-scheme:dark){:host{--b:#0b110e;--l:#25312a}}
    nav{background:var(--b);color:var(--t);border-bottom:1px solid var(--l);
      font-family:"Source Sans 3","Segoe UI",system-ui,-apple-system,sans-serif;font-size:15px;line-height:1.3}
    .in{box-sizing:border-box;max-width:var(--w);margin:0 auto;padding:0 var(--p);display:flex;align-items:stretch;justify-content:space-between;gap:4px 24px;flex-wrap:wrap}
    .tabs{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;margin:0 -8px}
    .tabs::-webkit-scrollbar{display:none}
    .tabs a{display:flex;align-items:center;padding:14px 8px 11px;color:var(--m);text-decoration:none;font-weight:600;
      white-space:nowrap;border-bottom:3px solid transparent}
    .tabs a:hover{color:var(--t)}
    .tabs a[aria-current="page"]{color:var(--t);border-bottom-color:var(--a)}
    .eq{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:13px;color:var(--m);padding:8px 0}
    .eq a{color:var(--t);text-decoration:underline;text-decoration-color:var(--l);text-underline-offset:3px}
    .eq a:hover{text-decoration-color:var(--a)}
    a:focus-visible{outline:2px solid var(--a);outline-offset:2px;border-radius:3px}
    @media (max-width:640px){.eq{padding:0 0 10px}}
  `;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  class SiteBarra extends HTMLElement {
    connectedCallback() {
      if (this.shadowRoot) return;
      const atual = this.getAttribute('atual');
      const px = (nome, padrao) => (+this.getAttribute(nome) || padrao) + 'px';
      const abas = PAGINAS.map(p => `<a href="${esc(p.href)}"${p.id === atual ? ' aria-current="page"' : ''}>${esc(p.titulo)}</a>`).join('');
      const nomes = EQUIPE.map(e => `<a href="https://github.com/${esc(e.github)}" target="_blank" rel="noopener">${esc(e.nome)}</a>`);
      const equipe = nomes.slice(0, -1).join(', ') + (nomes.length > 1 ? ' e ' : '') + nomes[nomes.length - 1];
      this.attachShadow({ mode: 'open' }).innerHTML =
        `<style>:host{--w:${px('largura', 1080)};--p:${px('margem', 20)}}${CSS}</style><nav aria-label="Páginas do projeto"><div class="in"><div class="tabs">${abas}</div>` +
        `<div class="eq"><span>Colaboradores: ${equipe}</span></div></div></nav>`;
    }
  }
  if (!customElements.get('site-barra')) customElements.define('site-barra', SiteBarra);
})();
