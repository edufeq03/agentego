import Link from "next/link";
import "../zapvai.css";

export default function TermsPage() {
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
        <h1 className="legal-title">Termos de Serviço</h1>
        <p className="last-update">Última atualização: 26 de abril de 2026</p>
      </header>

      <main>
        <div className="content-section">
          <h2 className="legal-subtitle">1. Aceitação dos Termos</h2>
          <p>Ao acessar e utilizar a plataforma Zapvai, você concorda em cumprir e estar vinculado a estes Termos de Serviço. Se você não concordar com qualquer parte destes termos, não deverá utilizar nossos serviços.</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">2. Descrição do Serviço</h2>
          <p>A Zapvai fornece uma solução de Inteligência Artificial para automação de atendimento e vendas via WhatsApp. Nosso serviço inclui o treinamento de uma IA personalizada com base nos dados do seu negócio.</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">3. Responsabilidades do Usuário</h2>
          <p>O usuário é responsável por:</p>
          <ul>
            <li>Garantir que o uso do WhatsApp esteja em conformidade com as políticas comerciais da Meta/WhatsApp.</li>
            <li>Não utilizar a plataforma para o envio de spam ou conteúdo ilegal.</li>
            <li>Manter a segurança de suas credenciais de acesso.</li>
            <li>Obter o consentimento dos seus clientes para o tratamento de dados.</li>
          </ul>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">4. Planos e Pagamentos</h2>
          <p>O acesso aos serviços da Zapvai é baseado em planos de assinatura. Os valores e limites de cada plano estão descritos em nossa página principal. O atraso no pagamento pode resultar na suspensão temporária dos serviços.</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">5. Limitação de Responsabilidade</h2>
          <p>A Zapvai não se responsabiliza por eventuais bloqueios de números de WhatsApp realizados pela Meta, uma vez que o uso da ferramenta é de inteira responsabilidade do usuário final. Também não garantimos resultados financeiros específicos, pois o sucesso das vendas depende de múltiplos fatores externos à ferramenta.</p>
        </div>

        <div className="content-section">
          <h2 className="legal-subtitle">6. Rescisão</h2>
          <p>Você pode cancelar sua assinatura a qualquer momento através do nosso painel ou suporte. O cancelamento interrompe cobranças futuras, mas não confere direito a reembolso de períodos já utilizados, salvo disposição em contrário.</p>
        </div>
      </main>

      <footer>
        <p>&copy; 2026 Zapvai. Todos os direitos reservados. Desenvolvido por Ignotec.</p>
      </footer>
    </div>
  );
}
