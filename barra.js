// Barra do topo e rodapé do site (GitHub Pages).
// Cada página do site põe <site-barra atual="id-da-pagina"></site-barra> logo depois de <body>,
// <site-rodape></site-rodape> logo antes de </body>, e carrega este arquivo (barra.js).
// - A barra do topo tem as abas para trocar de página. Para incluir uma página nova, acrescente-a
//   em PAGINAS (curto é o nome usado em telas estreitas, como a do celular).
// - O rodapé mostra os colaboradores do projeto (lista COLABORADORES).
// Os atributos opcionais largura e margem alinham a barra e o rodapé com o conteúdo da página
// (ex.: <site-barra atual="painel" largura="1240" margem="16">).
// Os dois são desenhados dentro de um "shadow DOM", para que o estilo deles e o das páginas não se misturem.
(function () {
  const PAGINAS = [
    { id: 'poda', href: './', titulo: 'Onde podar agora', curto: 'Onde podar' },
    { id: 'painel', href: 'painel-1746.html', titulo: 'Painel 1746', curto: 'Painel 1746' },
    { id: 'picos', href: 'picos-de-chamados.html', titulo: 'Picos de chamados', curto: 'Picos' }
  ];
  const COLABORADORES = [
    { nome: 'Heitor Morais', github: 'heitor-oss' },
    { nome: 'José Salgado', github: 'jssppedra-png' }
  ];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const medidas = el => {
    const px = (nome, padrao) => {
      const v = el.getAttribute(nome);
      return (v !== null && v.trim() !== '' && !isNaN(+v) ? +v : padrao) + 'px';
    };
    return `:host{--w:${px('largura', 1080)};--p:${px('margem', 20)}}`;
  };

  // ---- barra do topo: abas entre as páginas
  const CSS_BARRA = `
    :host{display:block;--b:#18221d;--t:#e4ece7;--m:#9fb1a7;--a:#5cc28f;--l:#2d3a33}
    @media (prefers-color-scheme:dark){:host{--b:#0b110e;--l:#25312a}}
    nav{background:var(--b);color:var(--t);border-bottom:1px solid var(--l);
      font-family:"Source Sans 3","Segoe UI",system-ui,-apple-system,sans-serif;font-size:15px;line-height:1.3}
    .in{box-sizing:border-box;max-width:var(--w);margin:0 auto;padding:0 var(--p)}
    .tabs{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;margin:0 -8px}
    .tabs::-webkit-scrollbar{display:none}
    .tabs a{display:flex;align-items:center;padding:14px 8px 11px;color:var(--m);text-decoration:none;font-weight:600;
      white-space:nowrap;border-bottom:3px solid transparent}
    .tabs a:hover{color:var(--t)}
    .tabs a[aria-current="page"]{color:var(--t);border-bottom-color:var(--a)}
    a:focus-visible{outline:2px solid var(--a);outline-offset:2px;border-radius:3px}
    .sh{display:none}
    @media (max-width:480px){.lg{display:none}.sh{display:inline}}
  `;
  class SiteBarra extends HTMLElement {
    connectedCallback() {
      if (this.shadowRoot) return;
      const atual = this.getAttribute('atual');
      const abas = PAGINAS.map(p => `<a href="${esc(p.href)}"${p.id === atual ? ' aria-current="page"' : ''}>` +
        `<span class="lg">${esc(p.titulo)}</span><span class="sh">${esc(p.curto || p.titulo)}</span></a>`).join('');
      this.attachShadow({ mode: 'open' }).innerHTML =
        `<style>${medidas(this)}${CSS_BARRA}</style><nav aria-label="Páginas do projeto"><div class="in"><div class="tabs">${abas}</div></div></nav>`;
      // se as abas não couberem na largura, mostra a aba atual
      const tabs = this.shadowRoot.querySelector('.tabs'), cur = this.shadowRoot.querySelector('[aria-current]');
      if (cur && tabs.scrollWidth > tabs.clientWidth) tabs.scrollLeft = cur.offsetLeft - tabs.offsetLeft - 8;
    }
  }

  // ---- rodapé: colaboradores (usa a fonte e as cores da própria página)
  const CSS_RODAPE = `
    :host{display:block}
    .in{box-sizing:border-box;max-width:var(--w);margin:0 auto;padding:0 var(--p) 32px}
    .l{margin:0;border-top:1px solid currentColor;border-top-color:color-mix(in srgb,currentColor 20%,transparent);
      padding-top:14px;font-size:14px;line-height:1.5}
    a{color:inherit;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px}
    a:focus-visible{outline:2px solid currentColor;outline-offset:2px;border-radius:3px}
  `;
  class SiteRodape extends HTMLElement {
    connectedCallback() {
      if (this.shadowRoot) return;
      const nomes = COLABORADORES.map(c => `<a href="https://github.com/${esc(c.github)}" target="_blank" rel="noopener">${esc(c.nome)}</a>`);
      const lista = nomes.slice(0, -1).join(', ') + (nomes.length > 1 ? ' e ' : '') + nomes[nomes.length - 1];
      this.attachShadow({ mode: 'open' }).innerHTML =
        `<style>${medidas(this)}${CSS_RODAPE}</style><footer class="in"><p class="l">Colaboradores: ${lista}</p></footer>`;
    }
  }

  if (!customElements.get('site-barra')) customElements.define('site-barra', SiteBarra);
  if (!customElements.get('site-rodape')) customElements.define('site-rodape', SiteRodape);
})();
