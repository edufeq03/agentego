from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def parse_time_range(range_str: str):
    """
    Parses a string like '08-12,14-22' into a list of (start_hour, end_hour) tuples.
    """
    ranges = []
    try:
        parts = range_str.split(',')
        for p in parts:
            start, end = p.split('-')
            ranges.append((int(start), int(end)))
    except Exception as e:
        logger.error(f"Erro ao parsear range de horário '{range_str}': {e}")
    return ranges

def esta_aberto(agora: datetime, horarios_config: dict) -> str:
    """
    Verifica se a empresa está aberta com base no dia da semana e horários.
    Retorna 'ABERTO', 'FECHADO' ou 'INTERVALO'.
    """
    dia_semana = agora.weekday() # 0 = Segunda, 6 = Domingo
    hora_atual = agora.hour
    
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
    for start, end in ranges:
        if start <= hora_atual < end:
            return "ABERTO"
    
    # Se houver mais de um range (ex: 08-12, 14-22) e a hora atual estiver no meio
    if len(ranges) > 1:
        # Ordena ranges
        ranges.sort()
        if ranges[0][1] <= hora_atual < ranges[1][0]:
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
