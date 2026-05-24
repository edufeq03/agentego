import re
from datetime import datetime, date, timedelta
import pytz

# Timezone padrão do Brasil
TZ_SP = pytz.timezone('America/Sao_Paulo')

DIAS_SEMANA_MAP = {
    'segunda': 0, 'seg': 0, 'segunda-feira': 0,
    'terca': 1, 'terça': 1, 'ter': 1, 'terca-feira': 1, 'terça-feira': 1,
    'quarta': 2, 'qua': 2, 'quarta-feira': 2,
    'quinta': 3, 'qui': 3, 'quinta-feira': 3,
    'sexta': 4, 'sex': 4, 'sexta-feira': 4,
    'sabado': 5, 'sábado': 5, 'sab': 5,
    'domingo': 6, 'dom': 6
}

MESES_MAP = {
    'janeiro': 1, 'jan': 1,
    'fevereiro': 2, 'fev': 2,
    'marco': 3, 'março': 3, 'mar': 3,
    'abril': 4, 'abr': 4,
    'maio': 5, 'mai': 5,
    'junho': 6, 'jun': 6,
    'julho': 7, 'jul': 7,
    'agosto': 8, 'ago': 8,
    'setembro': 9, 'set': 9,
    'outubro': 10, 'out': 10,
    'novembro': 11, 'nov': 11,
    'dezembro': 12, 'dez': 12
}

def obter_hoje_local() -> date:
    """Retorna o dia atual no fuso de São Paulo."""
    return datetime.now(TZ_SP).date()

def normalizar_texto(texto: str) -> str:
    import unicodedata
    texto = texto.lower().strip()
    # Remove acentos
    texto = "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

def parse_data(texto: str) -> date | None:
    """
    Interpreta uma string de texto em PT-BR e tenta extrair uma data.
    Retorna um objeto date ou None se não conseguir identificar.
    """
    texto_norm = normalizar_texto(texto)
    hoje = obter_hoje_local()

    # 1. Datas Relativas Simples
    if 'hoje' in texto_norm:
        return hoje
    if 'amanha' in texto_norm:
        return hoje + timedelta(days=1)
    if 'depois de amanha' in texto_norm:
        return hoje + timedelta(days=2)

    # 2. Formato DD/MM ou DD/MM/AAAA
    # Ex: 25/11, 25/11/2026, 25-11-2026
    match_data_barra = re.search(r'\b(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?\b', texto_norm)
    if match_data_barra:
        dia = int(match_data_barra.group(1))
        mes = int(match_data_barra.group(2))
        ano_str = match_data_barra.group(3)
        
        if ano_str:
            ano = int(ano_str)
            if len(ano_str) == 2:
                ano += 2000
        else:
            ano = hoje.year
            
        try:
            parsed_date = date(ano, mes, dia)
            # Se for do ano atual e já passou (ex: 15/01 e hoje é 24/05), joga para o próximo ano
            if not ano_str and parsed_date < hoje:
                parsed_date = date(ano + 1, mes, dia)
            return parsed_date
        except ValueError:
            pass

    # 3. Formato "dia X de [Mês]" ou "dia X"
    # Ex: "dia 25 de novembro", "dia 10"
    match_dia_de = re.search(r'\bdia\s+(\d{1,2})(?:\s+de\s+([a-z]+))?\b', texto_norm)
    if match_dia_de:
        dia = int(match_dia_de.group(1))
        mes_nome = match_dia_de.group(2)
        
        if mes_nome and mes_nome in MESES_MAP:
            mes = MESES_MAP[mes_nome]
            ano = hoje.year
            try:
                parsed_date = date(ano, mes, dia)
                if parsed_date < hoje:
                    parsed_date = date(ano + 1, mes, dia)
                return parsed_date
            except ValueError:
                pass
        elif not mes_nome:
            # Apenas o dia fornecido. Assume o mês atual, se já passou assume o próximo mês.
            mes = hoje.month
            ano = hoje.year
            try:
                parsed_date = date(ano, mes, dia)
                if parsed_date < hoje:
                    # Vai para o próximo mês
                    if mes == 12:
                        parsed_date = date(ano + 1, 1, dia)
                    else:
                        parsed_date = date(ano, mes + 1, dia)
                return parsed_date
            except ValueError:
                pass

    # 4. Dias da Semana (ex: "proxima segunda", "quinta", "quarta que vem")
    # Identifica o dia da semana mencionado
    dia_semana_alvo = None
    for palavra, val in DIAS_SEMANA_MAP.items():
        # Busca a palavra com fronteira de caracteres
        if re.search(rf'\b{palavra}\b', texto_norm):
            dia_semana_alvo = val
            break

    if dia_semana_alvo is not None:
        proxima = 'proxima' in texto_norm or 'que vem' in texto_norm or 'semana que vem' in texto_norm
        dias_a_frente = dia_semana_alvo - hoje.weekday()
        if dias_a_frente < 0 or (dias_a_frente == 0 and proxima):
            dias_a_frente += 7
        if proxima and dias_a_frente < 7:
            dias_a_frente += 7
        return hoje + timedelta(days=dias_a_frente)

    return None

def parse_hora(texto: str) -> str | None:
    """
    Tenta extrair um horário de uma string.
    Retorna uma string no formato 'HH:MM' ou None.
    """
    texto_norm = normalizar_texto(texto)

    # 1. Regex padrão para HH:MM ou HHhMM
    # Ex: "14:30", "14h30", "08:15", "8h"
    match_hora = re.search(r'\b(\d{1,2})[:h](\d{2})?\b', texto_norm)
    if match_hora:
        h = int(match_hora.group(1))
        m = int(match_hora.group(2)) if match_hora.group(2) else 0
        
        # Ajusta para PM se contiver termos como "da tarde" ou "da noite" e for menor que 12
        if h < 12 and ('tarde' in texto_norm or 'noite' in texto_norm or 'pm' in texto_norm):
            h += 12
        # Trata 12pm ou 12am se necessário, mas de forma simplificada
        
        if 0 <= h < 24 and 0 <= m < 60:
            return f"{h:02d}:{m:02d}"

    # 2. Ex: "14 horas", "9 hora"
    match_horas_extenso = re.search(r'\b(\d{1,2})\s*horas?\b', texto_norm)
    if match_horas_extenso:
        h = int(match_horas_extenso.group(1))
        if h < 12 and ('tarde' in texto_norm or 'noite' in texto_norm or 'pm' in texto_norm):
            h += 12
        if 0 <= h < 24:
            return f"{h:02d}:00"

    # 2.5. Ex: "2 da tarde", "8 da noite"
    match_periodo = re.search(r'\b(\d{1,2})\s*(?:de|da)?\s*(tarde|noite|manha)\b', texto_norm)
    if match_periodo:
        h = int(match_periodo.group(1))
        periodo = match_periodo.group(2)
        if h < 12 and periodo in ('tarde', 'noite'):
            h += 12
        return f"{h:02d}:00"

    # 3. Ex: "uma e meia", "duas e meia", "duas e quinze" (números por extenso comuns)
    # Apenas se houver correspondência exata para simplificar
    horas_extenso_map = {
        'uma': 1, 'duas': 2, 'tres': 3, 'quatro': 4, 'cinco': 5, 'seis': 6,
        'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10, 'onze': 11, 'doze': 12,
        'meio dia': 12, 'meio-dia': 12, 'meia noite': 0, 'meia-noite': 0
    }
    
    for palavra, h in horas_extenso_map.items():
        if palavra in texto_norm:
            m = 0
            if 'meia' in texto_norm and palavra != 'meia noite' and palavra != 'meia-noite':
                m = 30
            elif 'quinze' in texto_norm:
                m = 15
                
            if h < 12 and ('tarde' in texto_norm or 'noite' in texto_norm):
                h += 12
            return f"{h:02d}:{m:02d}"

    return None
