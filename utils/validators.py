# utils/validators.py
"""
Validações de dados
"""

from typing import List, Optional, Tuple

import pandas as pd


class DataValidator:
    """Classe para validação de dados"""
    
    # Coluna usada para distinguir relatório de FOLHA (mensal) de
    # relatório de ATIVOS (cadastro de servidores).
    _COLUNA_MES_ANO_FOLHA: str = 'MES_ANO_FOLHA'
    
    # Mapeamento (coluna_setor, coluna_vinculo, eh_ativos) para cada
    # tipo de relatório Ergon. Usado por ``identificar_tipo_relatorio``.
    _MAPEAMENTO_TIPO_RELATORIO: Tuple[Tuple[str, str, bool], Tuple[str, str, bool]] = (
        ('SETOR',    'TIPOVINC',     False),  # FOLHA mensal
        ('LOTACAO',  'TIPO_VINCULO', True ),  # ATIVOS (cadastro)
    )
    
    # Valor da coluna 'LOCAL' que identifica um hospital.
    _LOCAL_HOSPITAL: str = 'HOSPITAL'
    
    @staticmethod
    def validar_colunas_necessarias(
        df: pd.DataFrame, 
        colunas: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Verifica se todas as colunas necessárias estão presentes.
        
        Args:
            df: DataFrame cujas colunas serão verificadas.
            colunas: Lista de nomes de colunas obrigatórias.
        
        Returns:
            Tupla ``(válido, colunas_faltantes)`` onde ``válido`` é
            ``True`` quando nenhuma coluna está faltando, e
            ``colunas_faltantes`` é a lista (possivelmente vazia) das
            colunas de ``colunas`` ausentes em ``df``.
        """
        colunas_faltantes = [col for col in colunas if col not in df.columns]
        return len(colunas_faltantes) == 0, colunas_faltantes
    
    @staticmethod
    def identificar_tipo_relatorio(df: pd.DataFrame) -> Tuple[str, str, bool]:
        """
        Identifica o tipo de relatório (FOLHA ou ATIVOS).
        
        Heurística simples: se o DataFrame possui a coluna
        ``MES_ANO_FOLHA`` é tratado como relatório de **FOLHA mensal**;
        caso contrário, como relatório de **ATIVOS** (cadastro).
        
        O mapeamento de colunas é:
        
        - **FOLHA** → setor em ``SETOR``, vínculo em ``TIPOVINC``,
          ``eh_ativos = False``.
        - **ATIVOS** → setor em ``LOTACAO``, vínculo em
          ``TIPO_VINCULO``, ``eh_ativos = True``.
        
        Args:
            df: DataFrame bruto vindo do Ergon.
        
        Returns:
            Tupla ``(coluna_setor, coluna_vinculo, eh_ativos)``.
        """
        if DataValidator._COLUNA_MES_ANO_FOLHA in df.columns:
            # FOLHA mensal
            return DataValidator._MAPEAMENTO_TIPO_RELATORIO[0]
        # ATIVOS (cadastro de servidores)
        return DataValidator._MAPEAMENTO_TIPO_RELATORIO[1]
    
    @staticmethod
    def tem_hospitais(df: pd.DataFrame) -> bool:
        """
        Verifica se o DataFrame contém hospitais.
        
        Considera que há hospitais quando o DataFrame possui a coluna
        ``LOCAL`` e pelo menos uma linha com o valor ``HOSPITAL``.
        
        Args:
            df: DataFrame processado.
        
        Returns:
            ``True`` se houver ao menos um hospital; ``False`` caso
            contrário (incluindo quando a coluna ``LOCAL`` não existe).
        """
        return (
            'LOCAL' in df.columns
            and (df['LOCAL'] == DataValidator._LOCAL_HOSPITAL).any()
        )
    
    @staticmethod
    def contar_duplicatas(df: pd.DataFrame) -> int:
        """
        Conta o número de linhas duplicadas.
        
        Uma linha é considerada duplicada quando todos os valores de
        todas as colunas são idênticos aos de uma linha anterior
        (comportamento padrão do ``DataFrame.duplicated()``).
        
        Args:
            df: DataFrame a ser verificado.
        
        Returns:
            Quantidade de linhas duplicadas.
        """
        return int(df.duplicated().sum())
    
    @staticmethod
    def remover_duplicatas(
        df: pd.DataFrame, 
        subset: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Remove linhas duplicadas.
        
        Args:
            df: DataFrame a ser limpo.
            subset: Lista de colunas usadas como chave de
                duplicidade. Quando ``None`` (padrão), todas as
                colunas são consideradas.
        
        Returns:
            Novo DataFrame sem as duplicatas, mantendo a primeira
            ocorrência de cada grupo (``keep='first'``).
        """
        if subset:
            return df.drop_duplicates(subset=subset, keep='first')
        return df.drop_duplicates()