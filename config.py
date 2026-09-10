# config.py
"""
Configurações e constantes do sistema
"""

import pandas as pd

# Limites salariais
SALARIO_MINIMO = 1621.00
TETO_ESTADUAL = 41845.49

# Faixas etárias
FAIXAS_ETARIAS = {
    'MENOR_DE_18': (0, 17),
    '18_A_29': (18, 29),
    '30_A_39': (30, 39),
    '40_A_49': (40, 49),
    '50_A_54': (50, 54),
    '55_A_59': (55, 59),
    '60_OU_MAIS': (60, float('inf'))
}

# Faixas salariais (em múltiplos do salário mínimo)
# Cada tupla: (limite_superior_em_salarios, rótulo).
# A primeira faixa cujo limite superior seja >= qtd_salarios é a selecionada
# (mesma semântica das comparações <= no código original).
FAIXAS_SALARIAIS = [
    (3,             'Até 3 salários mínimos'),
    (6,             'De 3 a 6 salários mínimos'),
    (10,            'De 6 a 10 salários mínimos'),
    (15,            'De 10 a 15 salários mínimos'),
    (float('inf'),  'Mais de 15 salários mínimos'),
]

# Mapeamento de vínculos
VINCULOS_EFETIVO = [
    'CONTRATADO', 'CONCURSADO', 'REMAN GOIAS - ESTABILIZADO', 
    'REMAN GOIAS - NAO ESTAVEL', 'SERVIDOR EFETIVO', 'ESTAVEL'
]

VINCULOS_COMISSIONADO = [
    'AGENTE POLITICO', 'COMISSIONADO', 'CARGOS COMISSIONADOS',
    'COMISSIONADO - CARGO DE CONFIANCA'
]

VINCULOS_CONTRATADO = [
    'CONTRATADO', 'CONTRATO', 'CONTRATADO TEMPORARIO', 
    'CONTRATO TEMPORARIO', 'SERVIDOR CONTRATADO', 
    'CONTRATADO - TEMPORARIO', 'TEMPORARIO',
    'CONTRATADO TEMPORÁRIO', 'CONTRATO TEMPORÁRIO', 
    'CONTRATADO - TEMPORÁRIO'
]

# Colunas por tipo
COLUNAS_MOEDA = [
    'VALOR_TOTAL', 'VALOR_A_EMPENHAR', 'PATRONAL_FUNDO_PREVIDENCIA',
    'PATRONAL_FUNDO_PREV_13_SAL', 'PATRONAL_PLANSAUDE', 'PATRONAL_V_TRANSP_3%',
    'PATRONAL_V_TRANSP_6%', 'PATRONAL_INSS', 'PATRONAL_INSS_13_SAL',
    'PATRONAL_PREV_REQUISITADOS', 'VALOR NIVEL/REF', 'VALOR_SIMBOLO',
    'VALOR NIVEL/REF - com teto'
]

COLUNAS_INTEIRO = ['NUMFUNC', 'NUMVINC', 'IDADE', 'ORDEM']

COLUNAS_TEXTO = ['SITUACAO SALARIAL', 'FAIXA ETARIA', 'FAIXA SALARIAL', 'SERVIDOR IDOSO']

# Formatos de data aceitos
FORMATOS_DATA = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']

# Extensões de arquivo suportadas
EXTENSOES_SUPORTADAS = ['.csv', '.xlsx', '.xls']


# ==================== FUNÇÕES DE FORMATAÇÃO ====================

def formatar_numero_abreviado(valor: float, prefixo: str = "R$ ") -> str:
    """
    Formata um número com abreviação para valores grandes (padrão brasileiro).
    
    Regras de abreviação (todas com 2 casas decimais, para consistência):
      - **Milhões** (>= 1.000.000): abrevia com ``M``.
        Exemplos: ``5.430.000`` → ``5,43M``; ``5.000.000`` → ``5,00M``.
      - **Milhares** (>= 1.000): abrevia com ``K``.
        Exemplos: ``5.400`` → ``5,40K``; ``1.234`` → ``1,23K``.
      - **Menores que 1.000**: formata com 2 casas decimais e separador
        de milhar. Exemplo: ``540`` → ``540,00``.
    
    Args:
        valor: Valor numérico a ser formatado.
        prefixo: Prefixo a ser adicionado (padrão ``"R$ "``).
    
    Returns:
        String formatada no padrão brasileiro, ou ``"{prefixo}0,00"``
        quando o valor for nulo ou inválido.
    """
    if valor is None or pd.isna(valor):
        return f"{prefixo}0,00"
    
    try:
        valor_abs = abs(float(valor))
        
        # Milhões — 2 casas decimais
        if valor_abs >= 1_000_000:
            valor_formatado = valor / 1_000_000
            return f"{prefixo}{valor_formatado:.2f}M".replace('.', ',')
        
        # Milhares — 2 casas decimais
        elif valor_abs >= 1_000:
            valor_formatado = valor / 1_000
            return f"{prefixo}{valor_formatado:.2f}K".replace('.', ',')
        
        # Menos de 1.000 — formato completo
        else:
            return f"{prefixo}{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    except Exception:
        return f"{prefixo}0,00"


def formatar_numero_completo(valor: float, prefixo: str = "R$ ") -> str:
    """
    Formata um número completo sem abreviação (padrão brasileiro)
    """
    if valor is None or pd.isna(valor):
        return f"{prefixo}0,00"
    
    try:
        # Formata com separadores americanos
        temp = f"{valor:,.2f}"
        # Troca . por X (temporário)
        temp = temp.replace('.', 'X')
        # Troca , por .
        temp = temp.replace(',', '.')
        # Troca X por ,
        temp = temp.replace('X', ',')
        return f"{prefixo}{temp}"
    except Exception:
        return f"{prefixo}0,00"


def formatar_numero(valor: float, prefixo: str = "R$ ", abreviar: bool = True) -> str:
    """
    Formata um número com opção de abreviação (padrão brasileiro)
    """
    if abreviar:
        return formatar_numero_abreviado(valor, prefixo)
    else:
        return formatar_numero_completo(valor, prefixo)