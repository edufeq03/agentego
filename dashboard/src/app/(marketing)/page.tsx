"use client";

import Link from "next/link";
import { useEffect } from "react";
import "./zapvai.css";

export default function ZapvaiLanding() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            observer.unobserve(e.target);
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

    const hamburger = document.getElementById("hamburger");
    const nav = document.getElementById("main-nav");
    if (hamburger && nav) {
      hamburger.addEventListener("click", () => {
        nav.classList.toggle("open");
      });
    }
  }, []);

  return (
    <>
      <header>
        <div className="container">
          <div className="header-inner">
            <div className="logo">
              <div className="logo-icon">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              Zap<span>vai</span>
            </div>

            <nav id="main-nav">
              <a href="#benefits">Benefícios</a>
              <a href="#how">Como funciona</a>
              <a href="#faq">Dúvidas</a>
              <Link href="/login" className="nav-cta">
                Entrar no Painel
              </Link>
            </nav>

            <button className="hamburger" id="hamburger" aria-label="Menu">
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>
        </div>
      </header>

      <section className="hero" id="hero">
        <div className="hero-blob blob-1"></div>
        <div className="hero-blob blob-2"></div>
        <div className="hero-blob blob-3"></div>

        <div className="container">
          <div className="hero-inner">
            <div className="hero-copy reveal">
              <div className="badge">
                <span className="badge-dot"></span>
                IA para WhatsApp · Vendas 24h
              </div>

              <h1 className="hero-title">
                Seu WhatsApp como um<br />
                <em>vendedor automático</em><br />
                que nunca descansa
              </h1>

              <p className="hero-sub">
                Responda todos os clientes em segundos, filtre curiosos e foque apenas em quem está pronto para comprar — sem aumentar equipe.
              </p>

              <div className="hero-pills">
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  Atendimento 24h
                </div>
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                  </svg>
                  Filtra curiosos vs compradores
                </div>
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                    <polyline points="17 6 23 6 23 12" />
                  </svg>
                  Mais conversões
                </div>
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14" />
                  </svg>
                  Configurado para o seu negócio
                </div>
              </div>

              <div className="hero-actions">
                <a href="https://wa.me/5519996737713?text=Olá! Quero transformar meu WhatsApp em um vendedor." className="btn-primary">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z" />
                  </svg>
                  Quero meu vendedor automático
                </a>
              </div>
            </div>

            <div className="hero-visual reveal reveal-delay-2">
              <div className="phone-wrap">
                <div className="float-badge f1">
                  <div className="fb-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: "16px", height: "16px" }}>
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                  <div className="fb-text">
                    <div className="fb-val">+38 vendas</div>
                    <div className="fb-label">neste mês</div>
                  </div>
                </div>

                <div className="float-badge f3">
                  <div className="fb-icon cyan">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: "16px", height: "16px" }}>
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                  </div>
                  <div className="fb-text">
                    <div className="fb-val">&lt; 3s</div>
                    <div className="fb-label">tempo de resposta</div>
                  </div>
                </div>

                <div className="phone-frame">
                  <div className="phone-notch"></div>
                  <div className="chat-screen">
                    <div className="chat-header">
                      <div className="chat-avatar">ZV</div>
                      <div className="chat-contact">
                        <div className="chat-name">Zapvai Bot ⚡</div>
                        <div className="chat-status">● Online agora</div>
                      </div>
                    </div>

                    <div className="msg incoming">
                      <div className="msg-bubble">Oi, vi o anúncio. Quanto custa?</div>
                      <div className="msg-time">14:22</div>
                    </div>
                    <div className="msg outgoing">
                      <div className="msg-bubble">Olá! 😊 Que ótimo que entrou em contato. Temos planos a partir de R$97/mês. Posso te explicar o que está incluso?</div>
                      <div className="msg-time">14:22 ✓✓</div>
                    </div>
                    <div className="msg incoming">
                      <div className="msg-bubble">Sim! Quero saber mais.</div>
                      <div className="msg-time">14:23</div>
                    </div>
                    <div className="msg outgoing">
                      <div className="msg-bubble">Perfeito! Com o plano básico você tem atendimento automatizado 24h, filtragem de leads e relatórios semanais. Quer começar hoje?</div>
                      <div className="msg-time">14:23 ✓✓</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* PAIN */}
      <section className="pain-section" id="pain">
        <div className="container">
          <div className="pain-grid">
            <div className="reveal">
              <div className="section-label">O problema real</div>
              <h2 className="section-title">Você não está<br />sem clientes.<br />Está <em>perdendo</em> eles.</h2>
              <p style={{ fontSize: "1rem", color: "var(--text-muted)", lineHeight: 1.7, marginTop: "16px", marginBottom: "8px" }}>
                A maioria dos negócios acredita que precisa de mais clientes, mas ignora o que acontece dentro do próprio WhatsApp.
              </p>

              <ul className="pain-list">
                <li>
                  <div className="pain-icon-x">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </div>
                  Mensagens não respondidas a tempo
                </li>
                <li>
                  <div className="pain-icon-x">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </div>
                  Conversas que morrem no meio
                </li>
              </ul>
            </div>
            
            {/* New Added Feature Element from user instructions */}
            <div className="reveal reveal-delay-2">
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-num">80%</div>
                  <div className="stat-label">são curiosos ou comparam opções</div>
                </div>
                <div className="stat-card">
                  <div className="stat-num">24/7</div>
                  <div className="stat-label">Atendimento integrado ao seu Dashboard SaaS</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div className="container">
          <div className="footer-inner">
            <div className="logo">
              Zap<span>vai</span>
            </div>
            <div className="footer-tagline">Transformando WhatsApp em máquinas de vendas inteligentes</div>
          </div>
          <div className="footer-copy">
            <p>&copy; 2026 Zapvai. Todos os direitos reservados. Desenvolvido por Ignotec</p>
          </div>
        </div>
      </footer>
    </>
  );
}
