"use client";

import Link from "next/link";
import { useEffect } from "react";
import "./agentego.css";

export default function AgenteGoLanding() {
  useEffect(() => {
    // Scroll reveal
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          observer.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

    // Hamburger menu
    const hamburger = document.getElementById('hamburger');
    const nav = document.getElementById('main-nav');
    if (hamburger && nav) {
      hamburger.addEventListener('click', () => {
        nav.classList.toggle('open');
      });
    }

    // Smooth scroll for all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = anchor.getAttribute('href')?.substring(1);
        if (targetId) {
          const targetElement = document.getElementById(targetId);
          if (targetElement) {
            targetElement.scrollIntoView({
              behavior: 'smooth'
            });
            // Close mobile nav if open
            nav?.classList.remove('open');
          }
        }
      });
    });
  }, []);

  return (
    <>
      {/* ═══════════════════ HEADER ═══════════════════ */}
      <header>
        <div className="container">
          <div className="header-inner">
            <div className="logo">
              <div className="logo-icon">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              Agente<span>Go</span>
            </div>

            <nav id="main-nav">
              <a href="#benefits">Benefícios</a>
              <a href="#how">Como funciona</a>
              <a href="#pricing">Preços</a>
              <a href="#faq">Dúvidas</a>
              <Link href="/login" className="nav-cta" style={{ marginLeft: '8px' }}>Painel do Cliente</Link>
            </nav>

            <button className="hamburger" id="hamburger" aria-label="Menu">
              <span></span><span></span><span></span>
            </button>
          </div>
        </div>
      </header>

      {/* ═══════════════════ HERO ═══════════════════ */}
      <section className="hero" id="hero">
        <div className="hero-blob blob-1"></div>
        <div className="hero-blob blob-2"></div>
        <div className="hero-blob blob-3"></div>

        <div className="container">
          <div className="hero-inner">

            {/* LEFT: copy */}
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
                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                  </svg>
                  Atendimento 24h
                </div>
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                  </svg>
                  Filtra curiosos vs compradores
                </div>
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
                  </svg>
                  Mais conversões
                </div>
                <div className="pill">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
                  </svg>
                  Configurado para o seu negócio
                </div>
              </div>

              <div className="hero-actions">
                <a href="https://wa.me/5519996737713?text=Olá! Vi o AgenteGo e quero transformar meu WhatsApp com um Agente de Vendas." className="btn-primary">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/>
                  </svg>
                  Quero meu vendedor automático
                </a>
                <button className="btn-secondary" onClick={() => document.getElementById('how')?.scrollIntoView({behavior:'smooth'})}>
                  Ver como funciona
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{width:'16px',height:'16px'}}>
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>
            </div>

            {/* RIGHT: phone mockup */}
            <div className="hero-visual reveal reveal-delay-2">
              <div className="phone-wrap">
                <div className="float-badge f1">
                  <div className="fb-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{width:'16px',height:'16px'}}>
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <div className="fb-text">
                    <div className="fb-val">+38 vendas</div>
                    <div className="fb-label">neste mês</div>
                  </div>
                </div>

                <div className="float-badge f3">
                  <div className="fb-icon cyan">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{width:'16px',height:'16px'}}>
                      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                  </div>
                  <div className="fb-text">
                    <div className="fb-val">&lt; 3s</div>
                    <div className="fb-label">tempo de resposta</div>
                  </div>
                </div>

                <div className="float-badge f2">
                  <div className="fb-icon red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{width:'16px',height:'16px'}}>
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                    </svg>
                  </div>
                  <div className="fb-text">
                    <div className="fb-val">0 perdidos</div>
                    <div className="fb-label">sem resposta</div>
                  </div>
                </div>

                <div className="phone-frame">
                  <div className="phone-notch"></div>
                  <div className="chat-screen">
                    <div className="chat-header">
                      <div className="chat-avatar">ZV</div>
                      <div className="chat-contact">
                        <div className="chat-name">AgenteGo Bot ⚡</div>
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
                    <div className="msg incoming">
                      <div className="msg-bubble">Sim, quero fechar!</div>
                      <div className="msg-time">14:24</div>
                    </div>

                    <div className="typing-indicator">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* ═══════════════════ PAIN ═══════════════════ */}
      <section className="pain-section" id="pain">
        <div className="container">
          <div className="pain-grid">
            {/* Left: copy */}
            <div className="reveal">
              <div className="section-label">O problema real</div>
              <h2 className="section-title">Você não está<br />sem clientes.<br />Está <em>perdendo</em> eles.</h2>
              <p style={{fontSize:'1rem',color:'var(--text-muted)',lineHeight:1.7,marginTop:'16px',marginBottom:'8px'}}>
                A maioria dos negócios acredita que precisa de mais clientes, mas ignora o que acontece dentro do próprio WhatsApp.
              </p>

              <ul className="pain-list">
                <li>
                  <div className="pain-icon-x">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </div>
                  Mensagens não respondidas a tempo
                </li>
                <li>
                  <div className="pain-icon-x">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </div>
                  Conversas que morrem no meio
                </li>
                <li>
                  <div className="pain-icon-x">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </div>
                  Clientes que somem sem explicação
                </li>
              </ul>

              <p className="pain-punchline">
                O curioso não evolui. O comprador desiste.<br />
                E o <em>concorrente agradece.</em>
              </p>
            </div>

            {/* Right: stats */}
            <div className="reveal reveal-delay-2">
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-num">80%</div>
                  <div className="stat-label">são curiosos ou estão comparando opções antes de decidir</div>
                </div>
                <div className="stat-card">
                  <div className="stat-num">20%</div>
                  <div className="stat-label">já estão prontos para comprar agora mesmo</div>
                </div>
              </div>

              <div className="pain-quote">
                \"Sem um atendimento rápido e estruturado, você perde os dois grupos. O curioso não avança. O comprador vai para o concorrente.\"
              </div>

              <div style={{marginTop:'20px',padding:'20px',background:'var(--bg-card)',border:'1px solid var(--border)',borderRadius:'var(--radius-md)'}}>
                <div style={{fontSize:'0.75rem',fontWeight:700,textTransform:'uppercase',letterSpacing:'1px',color:'var(--text-faint)',marginBottom:'12px'}}>Impacto de demorar para responder</div>
                <div style={{display:'flex',flexDirection:'column',gap:'10px'}}>
                  <div>
                    <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.78rem',color:'var(--text-muted)',marginBottom:'5px'}}>
                      <span>Chance de fechar em &lt;5min</span><span style={{color:'var(--cyan)'}}>78%</span>
                    </div>
                    <div style={{height:'5px',background:'var(--border)',borderRadius:'3px'}}>
                      <div style={{height:'100%',width:'78%',background:'var(--cyan)',borderRadius:'3px'}}></div>
                    </div>
                  </div>
                  <div>
                    <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.78rem',color:'var(--text-muted)',marginBottom:'5px'}}>
                      <span>Chance de fechar em &gt;1h</span><span style={{color:'var(--red)'}}>12%</span>
                    </div>
                    <div style={{height:'5px',background:'var(--border)',borderRadius:'3px'}}>
                      <div style={{height:'100%',width:'12%',background:'var(--red)',borderRadius:'3px'}}></div>
                    </div>
                  </div>
                  <div>
                    <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.78rem',color:'var(--text-muted)',marginBottom:'5px'}}>
                      <span>Chance de fechar em &gt;24h</span><span style={{color:'var(--text-faint)'}}>3%</span>
                    </div>
                    <div style={{height:'5px',background:'var(--border)',borderRadius:'3px'}}>
                      <div style={{height:'100%',width:'3%',background:'var(--text-faint)',borderRadius:'3px'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* ═══════════════════ SOLUTION ═══════════════════ */}
      <section className="solution-section" id="solution">
        <div className="container">
          <div className="section-head reveal">
            <div className="section-label">A solução</div>
            <h2 className="section-title">Um vendedor automático trabalhando<br /><em>24h por dia</em> para você</h2>
            <p className="section-sub">Nosso agente transforma seu WhatsApp em um processo de vendas inteligente, configurado com base no seu produto e jeito de vender.</p>
          </div>

          <div className="solution-grid">
            <div className="sol-card reveal reveal-delay-1">
              <div className="sol-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              <h3>Resposta Imediata</h3>
              <p>Responde qualquer cliente em menos de 3 segundos, dia ou noite. Nenhuma mensagem fica sem resposta.</p>
            </div>

            <div className="sol-card reveal reveal-delay-2">
              <div className="sol-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <h3>Contexto Inteligente</h3>
              <p>Entende o contexto da conversa e guia o cliente naturalmente até a decisão de compra.</p>
            </div>

            <div className="sol-card reveal reveal-delay-3">
              <div className="sol-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                </svg>
              </div>
              <h3>Filtro de Qualidade</h3>
              <p>Filtra automaticamente quem realmente vale sua atenção, para você focar nos compradores potenciais.</p>
            </div>
          </div>

          <div className="reveal" style={{marginTop:'40px'}}>
            <div className="highlight-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <p>Não são respostas genéricas. O conteúdo é <strong>configurado com base no seu produto</strong>, serviço e forma de vender — para parecer natural e humano.</p>
            </div>
          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* ═══════════════════ BENEFITS ═══════════════════ */}
      <section className="benefits-section" id="benefits">
        <div className="container">
          <div className="benefits-grid">
            {/* Left: impact card */}
            <div className="impact-card reveal">
              <div className="big-text">
                Seu WhatsApp deixa de ser um gargalo…<br />
                e vira uma <em>máquina de vendas.</em>
              </div>
              <p style={{fontSize:'0.9rem',color:'var(--text-muted)',marginBottom:'28px'}}>Resultados reais que nossos clientes reportam após os primeiros 30 dias.</p>

              <div className="impact-icon-row">
                <div className="impact-icon-item">
                  <div className="ic" style={{background:'var(--cyan-dim)'}}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{width:'20px',height:'20px'}}>
                      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
                    </svg>
                  </div>
                  <span>+40% conversão</span>
                </div>
                <div className="impact-icon-item">
                  <div className="ic" style={{background:'var(--green-dim)'}}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{width:'20px',height:'20px'}}>
                      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                  </div>
                  <span>3s de resposta</span>
                </div>
                <div className="impact-icon-item">
                  <div className="ic" style={{background:'var(--red-dim)'}}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{width:'20px',height:'20px'}}>
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <span>0 não respondidos</span>
                </div>
              </div>
            </div>

            {/* Right: list */}
            <div className="reveal reveal-delay-2">
              <div className="section-label">Benefícios</div>
              <h2 className="section-title">Mais vendas.<br />Menos esforço.</h2>
              <p className="section-sub" style={{marginBottom:'32px'}}>Zero cliente sem resposta.</p>

              <div className="benefit-item">
                <div className="benefit-num">01</div>
                <div className="benefit-content">
                  <h4>Nunca mais deixe um cliente esperando</h4>
                  <p>Atendimento instantâneo 24 horas por dia, 7 dias por semana, sem interrupções.</p>
                </div>
              </div>
              <div className="benefit-item">
                <div className="benefit-num">02</div>
                <div className="benefit-content">
                  <h4>Aumente sua taxa de conversão no WhatsApp</h4>
                  <p>Respostas rápidas e estruturadas transformam mais curiosos em compradores.</p>
                </div>
              </div>
              <div className="benefit-item">
                <div className="benefit-num">03</div>
                <div className="benefit-content">
                  <h4>Foque apenas em clientes prontos para fechar</h4>
                  <p>A IA qualifica os leads para você, entregando só quem realmente tem intenção de compra.</p>
                </div>
              </div>
              <div className="benefit-item">
                <div className="benefit-num">04</div>
                <div className="benefit-content">
                  <h4>Mantenha seu atendimento ativo mesmo ocupado</h4>
                  <p>Mesmo quando você está em reunião, dormindo ou de folga — o WhatsApp segue vendendo.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* ═══════════════════ HOW IT WORKS ═══════════════════ */}
      <section className="how-section" id="how">
        <div className="container">
          <div className="section-head reveal" style={{textAlign:'center'}}>
            <div className="section-label" style={{justifyContent:'center'}}>Como funciona</div>
            <h2 className="section-title">Simples de usar.<br /><em>Rápido de ativar.</em></h2>
            <p className="section-sub" style={{margin:'0 auto'}}>Em poucos minutos, seu atendimento automático já está online e funcionando.</p>
          </div>

          <div className="steps-container">
            <div className="step-item reveal reveal-delay-1">
              <div className="step-circle">1</div>
              <h3>Conecte seu WhatsApp</h3>
              <p>Integre seu número à nossa plataforma de forma rápida e segura. Sem complicação técnica.</p>
            </div>
            <div className="step-item reveal reveal-delay-2">
              <div className="step-circle">2</div>
              <h3>Defina sua Estratégia</h3>
              <p>Configure como seu negócio responde, vende e qualifica clientes. Personalizamos tudo para você.</p>
            </div>
            <div className="step-item reveal reveal-delay-3">
              <div className="step-circle">3</div>
              <h3>Ative e Venda</h3>
              <p>Seu agente começa a atender, qualificar e preparar clientes automaticamente. 24h por dia.</p>
            </div>
          </div>

          <div className="how-note-wrap reveal">
            <div className="how-note">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Em poucos minutos, seu atendimento já está ativo e funcionando — sem precisar de equipe de TI.
            </div>
          </div>
        </div>
      </section>

      <div className="divider"></div>
      
      {/* ═══════════════════ PRICING ═══════════════════ */}
      <section className="pricing-section" id="pricing">
        <div className="container">
          <div className="section-head reveal" style={{textAlign:'center'}}>
            <div className="section-label" style={{justifyContent:'center'}}>Planos e Preços</div>
            <h2 className="section-title">Escolha o plano ideal para<br /><em>o seu momento</em></h2>
            <p className="section-sub" style={{margin:'0 auto'}}>Sem taxas de adesão. Cancele quando quiser.</p>
          </div>

          <div className="pricing-grid">
            {/* Plan 1 */}
            <div className="price-card reveal reveal-delay-1">
              <div className="pc-tag">Individual</div>
              <h3 className="pc-title">Plano Starter</h3>
              <div className="pc-price">
                <span className="currency">R$</span>
                <span className="amount">97</span>
                <span className="period">/mês</span>
              </div>
              <p className="pc-desc">Ideal para pequenos negócios que estão começando a automatizar.</p>
              
              <ul className="pc-features">
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> 1 Vendedor Automático</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> 1 Número de WhatsApp</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Atendimento 24h/7</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Filtro de Leads básico</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Suporte por e-mail</li>
              </ul>

              <a href="https://wa.me/5519996737713?text=Olá! Quero assinar o Plano Starter e ativar meu Agente." className="btn-secondary" style={{width:'100%',justifyContent:'center'}}>Começar agora</a>
            </div>

            {/* Plan 2 - Featured */}
            <div className="price-card featured reveal reveal-delay-2">
              <div className="pc-badge">Mais Popular</div>
              <div className="pc-tag" style={{color:'var(--cyan)'}}>Escalabilidade</div>
              <h3 className="pc-title">Plano Pro</h3>
              <div className="pc-price">
                <span className="currency">R$</span>
                <span className="amount">197</span>
                <span className="period">/mês</span>
              </div>
              <p className="pc-desc">Perfeito para quem quer separar vendas de suporte ou escalar volume.</p>
              
              <ul className="pc-features">
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> <strong>2 Vendedores Automáticos</strong></li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> <strong>2 Números de WhatsApp</strong></li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Estratégias Diferentes</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Dashboard de Métricas</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Suporte Prioritário</li>
              </ul>

              <a href="https://wa.me/5519996737713?text=Olá! Quero assinar o Plano Pro e escalar meus Agentes." className="btn-primary" style={{width:'100%',justifyContent:'center'}}>Assinar Plano Pro</a>
            </div>

            {/* Plan 3 */}
            <div className="price-card reveal reveal-delay-3">
              <div className="pc-tag">Corporativo</div>
              <h3 className="pc-title">Plano Business</h3>
              <div className="pc-price">
                <span className="currency">R$</span>
                <span className="amount">397</span>
                <span className="period">/mês</span>
              </div>
              <p className="pc-desc">Para empresas que precisam de inteligência sob medida e alto volume.</p>
              
              <ul className="pc-features">
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Vendedores Ilimitados</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Números Ilimitados</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> <strong>IA Treinada sob medida</strong></li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Integração via API / CRM</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg> Gerente de Conta Dedicado</li>
              </ul>

              <a href="https://wa.me/5519996737713?text=Olá! Quero saber mais sobre o Plano Business e Agentes sob medida." className="btn-secondary" style={{width:'100%',justifyContent:'center'}}>Falar com consultor</a>
            </div>
          </div>

          <div className="pricing-bottom reveal" style={{marginTop:'40px', textAlign:'center'}}>
            <p style={{fontSize:'0.85rem', color:'var(--text-faint)'}}>
              * Planos Business podem exigir taxa de setup única para treinamento personalizado da IA.
            </p>
          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* ═══════════════════ FAQ ═══════════════════ */}
      <section className="faq-section" id="faq">
        <div className="container">
          <div className="section-head reveal" style={{textAlign:'center'}}>
            <div className="section-label" style={{justifyContent:'center'}}>Dúvidas frequentes</div>
            <h2 className="section-title">Funciona mesmo<br />no meu caso?</h2>
          </div>

          <div className="faq-grid">
            <div className="faq-item reveal reveal-delay-1">
              <div className="faq-q">
                <div className="faq-q-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <h3>\"Vai parecer robótico?\"</h3>
              </div>
              <p>Não. As respostas são naturais e adaptadas ao seu negócio, configuradas para refletir sua voz e marca. Clientes raramente percebem que é automático.</p>
            </div>

            <div className="faq-item reveal reveal-delay-2">
              <div className="faq-q">
                <div className="faq-q-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <h3>\"E se o cliente fizer perguntas diferentes?\"</h3>
              </div>
              <p>O agente interpreta e responde dentro do contexto — ou encaminha para você quando necessário. Nenhuma pergunta fica sem resposta.</p>
            </div>

            <div className="faq-item reveal reveal-delay-3">
              <div className="faq-q">
                <div className="faq-q-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <h3>\"Vou perder o controle?\"</h3>
              </div>
              <p>Não. Você pode assumir qualquer conversa a qualquer momento. O agente complementa seu trabalho, não substitui seu controle.</p>
            </div>

            <div className="faq-item reveal reveal-delay-4">
              <div className="faq-q">
                <div className="faq-q-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#00e5d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <h3>\"Funciona para qualquer segmento?\"</h3>
              </div>
              <p>Sim. Configuramos o agente especificamente para o seu nicho — seja produto físico, serviço, consultoria ou loja virtual.</p>
            </div>
          </div>
        </div>
      </section>

      <div className="divider"></div>

      {/* ═══════════════════ FINAL CTA ═══════════════════ */}
      <section className="final-cta" id="cta">
        <div className="cta-blob cta-blob-1"></div>
        <div className="container">
          <div className="reveal">
            <div className="cta-eyebrow">
              <span className="badge-dot"></span>
              Comece hoje
            </div>
            <h2 className="section-title">Quantos clientes você já<br />perdeu hoje <em>sem perceber?</em></h2>
            <p className="final-cta-sub">Cada minuto sem resposta é uma oportunidade indo embora. Seu concorrente responde. Você demora. Quem você acha que vende?</p>

            <a href="https://wa.me/5519996737713?text=Olá! Quero começar agora com um Agente de IA e parar de perder vendas." className="btn-primary" style={{fontSize:'1.1rem',padding:'18px 36px',marginBottom:'8px'}}>
              <svg viewBox="0 0 24 24" fill="currentColor" style={{width:'22px',height:'22px'}}>
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/>
              </svg>
              Começar agora e parar de perder vendas
            </a>

            <div className="cta-trust">
              <div className="cta-trust-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                Sem contrato de fidelidade
              </div>
              <div className="cta-trust-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                Ativo em minutos
              </div>
              <div className="cta-trust-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                Suporte incluído
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ FOOTER ═══════════════════ */}
      <footer>
        <div className="container">
          <div className="footer-inner">
            <div className="logo">
              <div className="logo-icon">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#070d1a">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              Agente<span>Go</span>
            </div>
            <div className="footer-tagline">Transformando WhatsApp em máquinas de vendas inteligentes</div>
          </div>
          <div className="footer-copy">
            <p>&copy; 2026 AgenteGo. Todos os direitos reservados. Desenvolvido com <span>♥</span> por Ignotec</p>
            <div style={{marginTop: '12px', display: 'flex', justifyContent: 'center', gap: '20px'}}>
              <Link href="/privacy" style={{color: 'var(--text-faint)', fontSize: '0.75rem'}}>Privacidade</Link>
              <Link href="/terms" style={{color: 'var(--text-faint)', fontSize: '0.75rem'}}>Termos de Uso</Link>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
