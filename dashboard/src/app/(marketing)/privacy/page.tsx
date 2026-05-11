import Link from "next/link";
import "../agentego.css";

export default function PrivacyPage() {
  return (
    <div className="legal-container">
      <Link href="/" className="back-home">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Voltar para o início
      </Link>

      <header className="legal-header">
        <div className="logo legal-logo">
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
          </div>
          Zap<span>vai</span>
        </div>
        <h1 className="legal-title">Política de Privacidade</h1>
        <p className="last-update">Última atualização: 26 de abril de 2026</p>
      </header>

      <main>
        <div className="content-section">
          <h2 className="legal-subtitle">1. Introdução</h2>
          <p>A AgenteGo está comprometida em proteger sua privacidade. Esta Política de Privacidade explica como coletamos, usamos, divulgamos e protegemos suas informações quando você utiliza nossa plataforma de automação de vendas via WhatsApp.</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">2. Coleta de Dados</h2>
          <p>Coletamos informações que você nos fornece diretamente, bem como dados gerados durante o uso do serviço:</p>
          <ul>
            <li><strong>Informações de Registro:</strong> Nome, e-mail e dados de contato.</li>
            <li><strong>Integração com WhatsApp:</strong> Dados necessários para conectar sua conta ao nosso sistema.</li>
            <li><strong>Logs de Conversa:</strong> Armazenamos o histórico de mensagens para processamento pela nossa IA e melhoria contínua da assertividade das respostas.</li>
            <li><strong>Dados de Uso:</strong> Informações sobre como você interage com nossa plataforma.</li>
          </ul>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">3. Uso das Informações</h2>
          <p>Utilizamos os dados coletados para:</p>
          <ul>
            <li>Operar e manter a plataforma de IA vendedora.</li>
            <li>Treinar e aprimorar nossos modelos de linguagem para o seu nicho específico.</li>
            <li>Fornecer suporte técnico e responder a solicitações.</li>
            <li>Garantir a segurança e prevenir abusos na plataforma.</li>
          </ul>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">4. Segurança</h2>
          <p>Implementamos medidas de segurança técnicas e organizacionais para proteger seus dados, incluindo criptografia de ponta a ponta onde aplicável e armazenamento em servidores seguros (AWS/Google Cloud).</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">5. Seus Direitos (LGPD)</h2>
          <p>Em conformidade com a Lei Geral de Proteção de Dados (LGPD), você tem o direito de acessar, corrigir, excluir ou portar seus dados pessoais. Para exercer esses direitos, entre em contato através de nosso suporte.</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">6. Contato</h2>
          <p>Se você tiver dúvidas sobre esta política, entre em contato conosco pelo e-mail: <strong>contato@ignotec.com.br</strong></p>
        </div>
      </main>

      <footer>
        <p>&copy; 2026 AgenteGo. Todos os direitos reservados. Desenvolvido por Ignotec.</p>
      </footer>
    </div>
  );
}
