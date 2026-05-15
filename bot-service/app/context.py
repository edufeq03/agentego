from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

import re

def parse_time_range(range_str: str):
    """
    Parses a string like '08-12', '08:00 as 18:00', '08:00 - 22:00'
    into a list of (start_minutes, end_minutes) tuples.
    """
    ranges = []
    if not range_str: return ranges
    
    # Divide por vírgula se houver múltiplos intervalos (ex: "08-12, 14-18")
    parts = range_str.split(',')
    
    for p in parts:
        # Normaliza o separador para '-'
        p = p.lower()
        # Substitui conectivos comuns por '-'
        p = re.sub(r'\s*(as|até|to|at|—|–|-)\s*', '-', p)
        p = p.replace(' ', '')
        
        try:
            if '-' in p:
                start_str, end_str = p.split('-', 1)
                
                def to_minutes(time_s):
                    time_s = time_s.strip()
                    # Remove qualquer coisa que não seja número ou dois pontos
                    time_s = re.sub(r'[^0-9:]', '', time_s)
                    if not time_s: return 0
                    
                    if ':' in time_s:
                        parts = time_s.split(':')
                        h = int(parts[0])
                        m = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                        return h * 60 + m
                    else:
                        return int(time_s) * 60
                
                ranges.append((to_minutes(start_str), to_minutes(end_str)))
        except Exception as e:
            logger.error(f"Erro ao parsear range de horário '{p}': {e}")
            
    return ranges

def esta_aberto(agora: datetime, horarios_config: dict) -> str:
    """
    Verifica se a empresa está aberta com base no dia da semana e horários.
    Retorna 'ABERTO', 'FECHADO' ou 'INTERVALO'.
    """
    dia_semana = agora.weekday() # 0 = Segunda, 6 = Domingo
    minutos_atuais = agora.hour * 60 + agora.minute
    
    # Mapeamento simples
    if dia_semana < 5: # Segunda a Sexta
        range_str = horarios_config.get('semana', '')
    elif dia_semana == 5: # Sábado
        range_str = horarios_config.get('sabado', '')
    else: # Domingo
        range_str = horarios_config.get('domingo', 'fechado')
    
    if not range_str or range_str.lower() == 'fechado':
        return "FECHADO"
    
    ranges = parse_time_range(range_str)
    if not ranges:
        return "FECHADO"

    for start_min, end_min in ranges:
        if start_min <= minutos_atuais < end_min:
            return "ABERTO"
    
    # Se houver mais de um range (ex: 08-12, 14-22) e a hora atual estiver no meio
    if len(ranges) > 1:
        ranges.sort()
        # Verifica se está no intervalo entre o fim do primeiro e início do segundo
        for i in range(len(ranges) - 1):
            if ranges[i][1] <= minutos_atuais < ranges[i+1][0]:
                return "INTERVALO"
            
    return "FECHADO"

def gerar_contexto_tempo(config: dict) -> str:
    """
    Gera o bloco de texto de contexto de tempo para o prompt.
    """
    tz_name = config.get('timezone', 'America/Sao_Paulo')
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone('America/Sao_Paulo')
        
    agora = datetime.now(tz)
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_str = dias_semana[agora.weekday()]
    hora_str = agora.strftime("%H:%M")
    
    horarios = config.get('horarios', {})
    status = esta_aberto(agora, horarios)
    
    contexto = f"Hoje é {dia_str}, e a hora atual é {hora_str}."
    contexto += f"\nStatus do estabelecimento agora: {status}."
    
    if status == "FECHADO" or status == "INTERVALO":
        contexto += "\n(IMPORTANTE: O estabelecimento está fechado ou em intervalo agora. Avise o cliente se necessário, mas continue o atendimento normalmente.)"
        
    return contexto
