# services/ergon_service.py
"""
Serviço principal de processamento de dados Ergon
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.data_processors import DataProcessor
from utils.validators import DataValidator
from config import FORMATOS_DATA


@dataclass(frozen=True)
class ResultadoProcessamento:
    """
    Resultado imutável do processamento de dados Ergon.
    
    Encapsula o DataFrame processado e o dicionário de metadados
    gerados por ``ErgonService.processar_dados``. Substitui a tupla
    ``(df, info)`` anterior, oferecendo acesso nomeado e propriedades
    convenientes para os campos mais usados do dicionário ``info``.
    
    Attributes:
        df: DataFrame processado, com vínculos mapeados, idades
            calculadas (quando aplicável) e teto salarial aplicado.
        info: Dicionário com metadados do processamento, contendo
            as chaves 'eh_relatorio_ativos' (bool), 'total_registros'
            (int) e 'colunas' (List[str]).
    """
    df: pd.DataFrame
    info: Dict[str, Any]
    
    @property
    def eh_relatorio_ativos(self) -> bool:
        """Indica se o relatório processado é de servidores ativos."""
        return bool(self.info.get('eh_relatorio_ativos', False))
    
    @property
    def total_registros(self) -> int:
        """Total de registros no DataFrame processado."""
        return int(self.info.get('total_registros', 0))
    
    @property
    def colunas(self) -> List[str]:
        """Lista de nomes das colunas do DataFrame processado."""
        return list(self.info.get('colunas', []))


class ErgonService:
    """Serviço para processamento de dados do Ergon"""
    
    def __init__(self) -> None:
        self.processor: DataProcessor = DataProcessor()
        self.validator: DataValidator = DataValidator()
    
    def processar_dados(
        self, 
        df_ergon: pd.DataFrame, 
        df_apoio: pd.DataFrame
    ) -> Optional[ResultadoProcessamento]:
        """
        Processa os dados do Ergon com a planilha de apoio.
        
        Pipeline executado (na ordem):
          1. Identifica o tipo de relatório (FOLHA ou ATIVOS).
          2. Remove linhas totalmente vazias.
          3. Cria a coluna 'NUMERO FUNCIONAL' a partir de NUMFUNC-NUMVINC.
          4. Mapeia vínculos (CONTRATADO/CONCURSADO/REMAN/AGENTE POLITICO
             -> EFETIVO/COMISSIONADO).
          5. Realiza merge com a planilha de apoio via coluna de setor.
          6. Converte colunas de moeda e inteiro para tipos numéricos.
          7. Calcula idade e faixa etária (apenas para ativos).
          8. Aplica teto salarial e cria colunas de situação (apenas
             para ativos).
          9. Remove duplicatas (por 'NUMERO FUNCIONAL' quando presente).
         10. Adiciona coluna ORDEM numerada.
         11. Monta o dicionário ``info`` com metadados.
        
        Args:
            df_ergon: DataFrame com dados brutos do Ergon.
            df_apoio: DataFrame com a planilha de apoio (deve conter
                a coluna 'SETOR').
        
        Returns:
            ``ResultadoProcessamento`` com o DataFrame processado e
            os metadados, ou None quando o processamento não produzir
            resultado utilizável.
        
        Raises:
            ValueError: Se ocorrer qualquer erro durante o
                processamento (a mensagem inclui o erro original).
        """
        try:
            # 1. Identificar tipo de relatório
            coluna_setor, coluna_vinculo, eh_ativos = self.validator.identificar_tipo_relatorio(df_ergon)
            
            # 2. Limpeza inicial
            df_ergon = df_ergon.dropna(how='all')
            
            # 3. Criar número funcional
            if 'NUMFUNC' in df_ergon.columns and 'NUMVINC' in df_ergon.columns:
                df_ergon['NUMERO FUNCIONAL'] = (
                    df_ergon['NUMFUNC'].astype(str).str.strip() + '-' + 
                    df_ergon['NUMVINC'].astype(str).str.strip()
                )
            
            # 4. Mapear vínculos
            if coluna_vinculo in df_ergon.columns:
                df_ergon['VINCULO'] = df_ergon[coluna_vinculo].astype(str).str.strip().str.upper()
                df_ergon['VINCULO'] = df_ergon['VINCULO'].replace(
                    ['CONTRATADO', 'CONCURSADO', 'REMAN GOIAS - ESTABILIZADO', 'REMAN GOIAS - NAO ESTAVEL'], 
                    'EFETIVO'
                )
                df_ergon['VINCULO'] = df_ergon['VINCULO'].replace('AGENTE POLITICO', 'COMISSIONADO')
            
            # 5. Preparar para merge
            df_ergon[coluna_setor] = df_ergon[coluna_setor].astype(str).str.strip()
            df_apoio['SETOR'] = df_apoio['SETOR'].astype(str).str.strip()
            
            # Remover duplicatas da planilha de apoio
            df_apoio = df_apoio.drop_duplicates(subset=['SETOR'])
            
            # 6. Realizar merge
            df_merged = pd.merge(
                df_ergon,
                df_apoio,
                left_on=coluna_setor,
                right_on='SETOR',
                how='left'
            )

            # Coluna usada no relatório geral exportado pela aplicação.
            df_merged = self.processor.adicionar_cargo_ajustado(df_merged)
            
            # 7. Converter colunas
            df_merged = self.processor.converter_colunas_moeda(df_merged)
            df_merged = self.processor.converter_colunas_inteiro(df_merged)
            
            # 8. Calcular idade (apenas para ativos)
            if eh_ativos and 'DTNASC' in df_merged.columns:
                df_merged = self._calcular_idades(df_merged)
            
            # 9. Aplicar teto salarial (apenas para ativos)
            if eh_ativos:
                df_merged = self.processor.aplicar_teto_salarial(df_merged)
            
            # 10. Remover duplicatas
            if 'NUMERO FUNCIONAL' in df_merged.columns:
                df_merged = df_merged.drop_duplicates(subset=['NUMERO FUNCIONAL'], keep='first')
            else:
                df_merged = df_merged.drop_duplicates()
            
            # 11. Adicionar ordem
            df_merged = self.processor.adicionar_coluna_ordem(df_merged)
            
            # 12. Informações do processamento
            info = {
                'eh_relatorio_ativos': eh_ativos,
                'total_registros': len(df_merged),
                'colunas': list(df_merged.columns)
            }
            
            return ResultadoProcessamento(df=df_merged, info=info)
            
        except Exception as e:
            raise ValueError(f"Erro no processamento: {str(e)}")
    
    def _calcular_idades(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula idade, faixa etária e indicação de servidor idoso de forma
        vetorizada, substituindo o loop `iterrows` original para ganho
        expressivo de desempenho e redução de uso de memória.

        Comportamento preservado em relação à implementação anterior:
          - Valores vazios/NaN em 'DTNASC' geram idade ausente (pd.NA) e
            faixa 'SEM INFORMACAO'.
          - Os formatos de data são tentados na ordem definida em
            FORMATOS_DATA; valores não resolvidos passam por um fallback
            genérico com `dayfirst=True` (equivalente ao último recurso
            de `_converter_data`).
          - As faixas etárias seguem as constantes FAIXAS_ETARIAS do
            `config`, produzindo os mesmos rótulos da versão original.
          - 'SERVIDOR IDOSO' = 'SIM' apenas quando a idade é válida e
            maior ou igual a 60; caso contrário, 'NAO'.

        Args:
            df: DataFrame contendo a coluna 'DTNASC' com as datas de
                nascimento dos servidores.

        Returns:
            Novo DataFrame com as colunas 'IDADE', 'FAIXA ETARIA' e
            'SERVIDOR IDOSO' preenchidas.
        """
        df = df.copy()

        # Inicializa colunas com valores padrão (mesmo comportamento do
        # original para linhas que não receberão atualização).
        df['IDADE'] = pd.Series(pd.NA, index=df.index, dtype='Int64')
        df['FAIXA ETARIA'] = 'SEM INFORMACAO'
        df['SERVIDOR IDOSO'] = 'NAO'

        # Sem DTNASC, nada a calcular — mantém defaults.
        if 'DTNASC' not in df.columns:
            return df

        serie_dtnasc = df['DTNASC']

        # Máscara de valores reconhecidamente vazios (não tenta converter).
        mascara_vazia = serie_dtnasc.isna() | (
            serie_dtnasc.astype(str).str.strip() == ''
        )

        # Se todos os valores forem vazios, nada a fazer.
        if mascara_vazia.all():
            return df

        # ===== Conversão vetorizada de datas =====
        # Tenta cada formato específico em ordem; o que falhar fica para
        # o próximo formato ou para o fallback genérico ao final.
        datas: pd.Series = pd.Series(
            pd.NaT, index=df.index, dtype='datetime64[ns]'
        )

        for fmt in FORMATOS_DATA:
            pendentes = datas.isna() & ~mascara_vazia
            if not pendentes.any():
                break
            datas.loc[pendentes] = pd.to_datetime(
                serie_dtnasc[pendentes],
                format=fmt,
                errors='coerce'
            )

        # Fallback final: parsing genérico (dayfirst=True prioriza DD/MM).
        pendentes = datas.isna() & ~mascara_vazia
        if pendentes.any():
            datas.loc[pendentes] = pd.to_datetime(
                serie_dtnasc[pendentes],
                errors='coerce',
                dayfirst=True
            )

        mask_validas = datas.notna()
        if not mask_validas.any():
            return df

        # ===== Cálculo vetorizado da idade =====
        # Equivalente a relativedelta(hoje, data).years: anos completos
        # considerando se o aniversário já ocorreu no ano corrente.
        hoje = pd.Timestamp.now().normalize()
        anos_brutos = hoje.year - datas.dt.year
        aniversario_ocorreu = (datas.dt.month < hoje.month) | (
            (datas.dt.month == hoje.month) & (datas.dt.day <= hoje.day)
        )
        df['IDADE'] = (
            anos_brutos - (~aniversario_ocorreu).astype(int)
        ).astype('Int64')

        # ===== Faixa etária vetorizada via pd.cut =====
        # Bins e labels correspondem exatamente às constantes
        # FAIXAS_ETARIAS e ao método `_determinar_faixa_etaria` do
        # DataProcessor (após o replace '_' -> ' ' e 'A' -> 'a').
        bins: list = [-1, 17, 29, 39, 49, 54, 59, float('inf')]
        labels: list = [
            'MENOR DE 18',
            '18 a 29',
            '30 a 39',
            '40 a 49',
            '50 a 54',
            '55 a 59',
            '60 OU MAIS'
        ]
        faixas = pd.cut(
            df['IDADE'].astype('float'),
            bins=bins,
            labels=labels,
            right=True
        )
        # Atribui faixas apenas às linhas com data válida; idades
        # negativas (datas futuras por erro de cadastro) caem fora dos
        # bins e também viram 'SEM INFORMACAO'.
        df.loc[mask_validas, 'FAIXA ETARIA'] = (
            faixas[mask_validas].astype(object).fillna('SEM INFORMACAO')
        )

        # ===== Servidor idoso (vetorizado) =====
        # 'SIM' apenas quando idade é válida e >= 60.
        mask_idosos = mask_validas & (df['IDADE'].fillna(-1) >= 60)
        df.loc[mask_idosos, 'SERVIDOR IDOSO'] = 'SIM'

        return df
