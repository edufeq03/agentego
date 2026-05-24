# Estratégia Comercial & Jurídica: Parcerias White-Label de IA

Este documento serve como guia estratégico para estruturar o modelo de negócios White-Label da plataforma, focado em parcerias com agências de marketing e redes de franquia, operando de forma enxuta como desenvolvedor solo (*solopreneur*).

---

## 1. Perfil da Agência Ideal (Onde Buscar?)

Nem toda agência de marketing serve para este modelo. Agências de *branding*, design ou mídias sociais tradicionais não têm foco em performance ou automação. O seu alvo deve ser:

* **Agências de Tráfego Pago / Performance**: Focadas em gerar *leads* (pelo Meta Ads/Google Ads) para negócios locais. Elas sofrem com a perda de leads que chegam no WhatsApp e não são atendidos rapidamente.
* **Agências de Automação & CRM**: Implementadoras de ferramentas como ManyChat, ActiveCampaign, RD Station, Kommo ou Blip. Eles já entendem a lógica de funis e fluxos de atendimento.
* **Agências Especializadas em Nichos**: Agências que atendem *exclusivamente* um setor (ex: "Agência especializada em captação para Academias" ou "Agência para Médicos/Clínicas de Estética"). Essas são as mais valiosas, pois uma única venda abre portas para dezenas de clientes idênticos.

### Como Encontrar:
* Pesquise no Instagram e Google por termos como: *"Tráfego Pago para Negócios Locais"*, *"Automação de WhatsApp Agência"*, *"Marketing para Academias"*.
* Participe de eventos de marketing digital, comunidades de tráfego pago (Comunidade Sobral, etc.) e grupos de WhatsApp/Telegram de donos de agência.

---

## 2. A Abordagem Comercial (O Pitch)

Donos de agência vivem o problema da **recorrência instável** e de **clientes que reclamam que os leads "estão ruins"** (quando na verdade o cliente final demora 3 horas para responder o lead no WhatsApp).

Seu pitch de vendas deve focar no seguinte:
1. **Acabar com o atraso no atendimento**: *"Nossa IA atende o lead em 10 segundos, qualifica e agenda a visita de forma automática, garantindo que o dinheiro que você gastou no anúncio não seja jogado fora."*
2. **Transformar serviço em recorrência (SaaS)**: *"Em vez de cobrar apenas pela gestão de tráfego (serviço que o cliente cancela fácil), você pode empacotar a IA com a sua marca e cobrar uma mensalidade do software. O cliente não cancela o sistema onde os leads dele estão salvos."*
3. **White-Label Real**: *"O painel terá o seu logotipo, suas cores e rodará no seu subdomínio (ex: `app.suaagencia.com.br`). O seu cliente nem saberá que a tecnologia é minha."*

### Proposta de Piloto:
* Ofereça um teste de **14 dias sem custo** para a agência aplicar no cliente "mais problemático" ou de "maior potencial" que eles têm. O sucesso desse piloto validará o sistema e fechará o contrato definitivo de parceria.

---

## 3. Precificação Sugerida (Quanto Cobrar?)

A agência assume o suporte nível 1 e a captação dos clientes. Você assume a hospedagem e a infraestrutura do código.

| Modelo de Cobrança | Valor Estimado (BRL) | O que Inclui |
| :--- | :--- | :--- |
| **Taxa de Setup (Configuração)** | R$ 1.500 a R$ 3.000 | Configuração única do portal White-Label da agência (logo, cores, domínio personalizado) e treinamento básico do time deles. |
| **Mensalidade por Subconta (Ativa)** | R$ 49 a R$ 99 por cliente/mês | A agência paga a você esse valor por cada cliente que ela cadastrar no painel. Ela costuma cobrar **R$ 297 a R$ 597/mês** do cliente final, obtendo uma excelente margem de lucro. |
| **Créditos Extras de API** | Custo de Token OpenAI + Margem | Se a agência ultrapassar o limite padrão de conversas, você cobra o excedente com uma margem de 30% a 50% sobre os custos de API da OpenAI. |

---

## 4. Acesso ao Código & Hospedagem (Segurança Intelectual)

> [!IMPORTANT]
> **A Agência NUNCA deve ter acesso ao código-fonte da sua plataforma.**

O modelo White-Label funciona sob o formato **SaaS (Software as a Service) Hospedado**, e não *On-Premise* (instalar no servidor deles).
* O código-fonte roda em **seus servidores** (na sua conta AWS, Google Cloud, DigitalOcean ou VPS).
* O acesso deles é feito por meio de um domínio apontado via CNAME (ex: o domínio da agência `sistema.agenciadigital.com` aponta para o seu servidor).
* Dessa forma, você mantém o controle total da propriedade intelectual. Se eles cancelarem a parceria, você simplesmente desativa o acesso deles no banco de dados e o sistema deles cai.

---

## 5. Proteção Jurídica e Direitos Autorais no Brasil

Sim, você pode (e deve) proteger o seu código no Brasil. 

### A. Registro de Software no INPI
O órgão responsável pelo registro de direitos autorais de programas de computador no Brasil é o **INPI (Instituto Nacional da Propriedade Industrial)**.
* O processo é 100% digital e rápido (costuma sair em menos de uma semana).
* Você gera um *hash* (uma assinatura digital criptográfica baseada no seu código-fonte) e preenche os dados do autor/titular.
* O registro no INPI serve como prova legal incontestável de que você escreveu aquele software naquela data. O custo da taxa federal (GRU) é baixo (menos de R$ 200).

### B. Contrato de Parceria Comercial e Licenciamento (O mais importante)
O que impede uma agência de usar o seu sistema por 3 meses e depois tentar copiar? Um bom **Contrato de Licenciamento de Uso de Software (SaaS)**. O contrato deve prever:
1. **Licenciamento Não-Exclusivo e Intransferível**: Eles estão comprando o direito de *usar* o sistema e revender subcontas, não a propriedade dele.
2. **Cláusula de Confidencialidade (NDA) e Não-Concorrência**: Impede legalmente que o dono da agência contrate outro desenvolvedor para copiar o design, a arquitetura ou as regras de negócio do seu produto pelo período da parceria + X anos após o término.
3. **Limitação de Responsabilidade**: Você não é responsável por eventuais bloqueios de números do WhatsApp dos clientes finais (já que o uso abusivo/spam é de responsabilidade deles) ou por instabilidades das APIs da OpenAI/Meta.
