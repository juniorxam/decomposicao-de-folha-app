# utils/data_processors.py
"""
Processamento de dados: cálculos, transformações e validações
"""

import datetime
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from typing import Optional, Tuple, List, Dict, Any
from config import (
    FAIXAS_ETARIAS, FORMATOS_DATA, SALARIO_MINIMO, TETO_ESTADUAL,
    VINCULOS_EFETIVO, VINCULOS_COMISSIONADO, VINCULOS_CONTRATADO,
    COLUNAS_MOEDA, COLUNAS_INTEIRO, COLUNAS_TEXTO,
    FAIXAS_SALARIAIS
)


class DataProcessor:
    """Classe para processamento de dados"""
    
    # Nome da coluna de moeda com regras de parsing especiais
    # (remove separadores de milhar e caracteres não numéricos).
    _COLUNA_MOEDA_ESPECIAL: str = 'VALOR_SIMBOLO'
    
    @staticmethod
    def calcular_idade_e_faixa(data_nascimento) -> Tuple[Optional[int], str]:
        """
        Calcula idade e faixa etária a partir da data de nascimento
        
        Args:
            data_nascimento: Data de nascimento em diversos formatos
            
        Returns:
            Tupla (idade, faixa_etaria)
        """
        if pd.isna(data_nascimento) or data_nascimento == '' or data_nascimento is None:
            return None, 'SEM INFORMACAO'
        
        try:
            data_convertida = DataProcessor._converter_data(data_nascimento)
            
            if data_convertida is None:
                return None, 'SEM INFORMACAO'
            
            hoje = datetime.datetime.now()
            idade = relativedelta(hoje, data_convertida).years
            
            faixa = DataProcessor._determinar_faixa_etaria(idade)
            return idade, faixa
            
        except Exception:
            return None, 'SEM INFORMACAO'
    
    @staticmethod
    def _converter_data(data) -> Optional[datetime.datetime]:
        """Converte data em diferentes formatos para datetime"""
        if isinstance(data, (pd.Timestamp, datetime.datetime)):
            return data.replace(tzinfo=None) if hasattr(data, 'tzinfo') else data
        
        if isinstance(data, str):
            for fmt in FORMATOS_DATA:
                try:
                    return datetime.datetime.strptime(data, fmt)
                except ValueError:
                    continue
            
            try:
                return pd.to_datetime(data, errors='coerce')
            except Exception:
                return None
        
        try:
            return pd.to_datetime(data, errors='coerce')
        except Exception:
            return None
    
    @staticmethod
    def _determinar_faixa_etaria(idade: int) -> str:
        """Determina a faixa etária com base na idade"""
        for nome, (min_idade, max_idade) in FAIXAS_ETARIAS.items():
            if min_idade <= idade <= max_idade:
                return nome.replace('_', ' ').replace('A', 'a')
        return 'SEM INFORMACAO'
    
    @staticmethod
    def calcular_faixa_salarial(valor: float) -> str:
        """
        Calcula faixa salarial com base no valor e salário mínimo.
        
        Os limites das faixas (em múltiplos do salário mínimo) e os
        respectivos rótulos são definidos em ``FAIXAS_SALARIAIS`` no
        módulo ``config``, garantindo um único ponto de configuração.
        
        Args:
            valor: Valor do salário
            
        Returns:
            String com a faixa salarial ou 'SEM INFORMACAO' quando o
            valor for nulo, vazio, zero ou não numérico.
        """
        if pd.isna(valor) or valor == '' or valor == 0 or valor is None:
            return 'SEM INFORMACAO'
        
        try:
            valor_float = float(valor)
            if valor_float <= 0:
                return 'SEM INFORMACAO'
            
            qtd_salarios = valor_float / SALARIO_MINIMO
            
            for limite_superior, rotulo in FAIXAS_SALARIAIS:
                if qtd_salarios <= limite_superior:
                    return rotulo
            
            # Em tese inalcançável: a última faixa tem limite = inf.
            return FAIXAS_SALARIAIS[-1][1]
            
        except Exception:
            return 'SEM INFORMACAO'
    
    @staticmethod
    def aplicar_teto_salarial(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica o teto salarial e cria colunas de situação
        
        Args:
            df: DataFrame com dados salariais
            
        Returns:
            DataFrame com colunas adicionais
        """
        if 'VALOR NIVEL/REF' not in df.columns or 'VALOR_SIMBOLO' not in df.columns:
            return df
        
        df = df.copy()
        
        # Criar base para cálculo
        df['VALOR_BASE_CALCULO'] = df['VALOR NIVEL/REF'].copy()
        
        # Usar VALOR_SIMBOLO quando VALOR NIVEL/REF for 0 ou nulo
        mask_zero = (df['VALOR NIVEL/REF'] == 0) | (df['VALOR NIVEL/REF'].isna())
        df.loc[mask_zero, 'VALOR_BASE_CALCULO'] = df.loc[mask_zero, 'VALOR_SIMBOLO']
        
        # Criar coluna com teto aplicado
        df['VALOR NIVEL/REF - com teto'] = df['VALOR_BASE_CALCULO'].copy()
        
        # Identificar valores sem informação
        mask_sem_info = (df['VALOR_BASE_CALCULO'] == 0) | (df['VALOR_BASE_CALCULO'].isna())
        df.loc[mask_sem_info, 'VALOR NIVEL/REF - com teto'] = None
        
        # Aplicar teto para valores válidos
        mask_validos = ~mask_sem_info
        df.loc[mask_validos & (df['VALOR NIVEL/REF - com teto'] < SALARIO_MINIMO), 
               'VALOR NIVEL/REF - com teto'] = SALARIO_MINIMO
        df.loc[mask_validos & (df['VALOR NIVEL/REF - com teto'] > TETO_ESTADUAL), 
               'VALOR NIVEL/REF - com teto'] = TETO_ESTADUAL
        
        # Criar situação salarial
        df['SITUACAO SALARIAL'] = 'DENTRO DO LIMITE'
        
        # Situação baseada em VALOR NIVEL/REF
        mask_usa_ref = ~mask_zero & mask_validos
        df.loc[mask_usa_ref & (df['VALOR NIVEL/REF'] < SALARIO_MINIMO), 
               'SITUACAO SALARIAL'] = 'ABAIXO DO MINIMO'
        df.loc[mask_usa_ref & (df['VALOR NIVEL/REF'] > TETO_ESTADUAL), 
               'SITUACAO SALARIAL'] = 'ACIMA DO TETO'
        
        # Situação baseada em VALOR_SIMBOLO
        mask_usa_simbolo = mask_zero & mask_validos
        df.loc[mask_usa_simbolo & (df['VALOR_SIMBOLO'] < SALARIO_MINIMO), 
               'SITUACAO SALARIAL'] = 'ABAIXO DO MINIMO'
        df.loc[mask_usa_simbolo & (df['VALOR_SIMBOLO'] > TETO_ESTADUAL), 
               'SITUACAO SALARIAL'] = 'ACIMA DO TETO'
        
        df.loc[mask_sem_info, 'SITUACAO SALARIAL'] = 'SEM INFORMACAO'
        
        # Criar faixa salarial
        df['FAIXA SALARIAL'] = df['VALOR NIVEL/REF - com teto'].apply(
            DataProcessor.calcular_faixa_salarial
        )
        
        df.drop('VALOR_BASE_CALCULO', axis=1, inplace=True)
        
        return df
    
    @staticmethod
    def mapear_vinculo(vinculo: str) -> str:
        """
        Mapeia o vínculo para categorias padronizadas
        
        Args:
            vinculo: String com o vínculo original
            
        Returns:
            Categoria padronizada
        """
        vinculo = str(vinculo).upper().strip()
        
        # Verificar efetivo
        for padrao in VINCULOS_EFETIVO:
            if padrao in vinculo:
                return 'EFETIVO'
        
        # Verificar comissionado
        for padrao in VINCULOS_COMISSIONADO:
            if padrao in vinculo:
                return 'COMISSIONADO'
        
        # Verificar contratado
        for padrao in VINCULOS_CONTRATADO:
            if padrao in vinculo:
                return 'CONTRATADO'
        
        # Palavras-chave
        if 'CONTRAT' in vinculo:
            return 'CONTRATADO'
        elif 'EFETIV' in vinculo:
            return 'EFETIVO'
        elif 'COMISSION' in vinculo:
            return 'COMISSIONADO'
        
        return 'OUTROS'

    @staticmethod
    def adicionar_cargo_ajustado(df: pd.DataFrame) -> pd.DataFrame:
        """Cria CARGO AJUSTADO pela primeira origem preenchida."""
        df = df.copy()

        def coluna_ou_vazia(nome: str) -> pd.Series:
            if nome in df.columns:
                return df[nome].fillna('').astype(str).str.strip()
            return pd.Series('', index=df.index, dtype='object')

        cargo = coluna_ou_vazia('CARGO')
        cargo_comissao = coluna_ou_vazia('CARGO_COMISSAO_OU_FUNCAO')
        tipo_vinculo = coluna_ou_vazia('TIPO_VINCULO')

        df['CARGO AJUSTADO'] = cargo.mask(cargo.eq(''), cargo_comissao)
        df['CARGO AJUSTADO'] = df['CARGO AJUSTADO'].mask(
            df['CARGO AJUSTADO'].eq(''), tipo_vinculo
        )
        return df
    
    @staticmethod
    def converter_colunas_moeda(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte colunas de moeda para float de forma vetorizada.
        
        Processa todas as colunas listadas em ``COLUNAS_MOEDA`` que
        existam no DataFrame, aplicando duas regras distintas:
        
        - **Regra padrão** (demais colunas): converte para string,
          remove espaços e troca vírgula decimal por ponto.
        
        - **Regra especial** (``VALOR_SIMBOLO``): além da regra
          padrão, remove separadores de milhar (pontos) e quaisquer
          caracteres não numéricos restantes (exceto dígito, ponto
          decimal e sinal de menos).
        
        Valores que não puderem ser convertidos tornam-se ``0``.
        O dtype resultante é sempre ``float64`` (mesmo comportamento
        da versão anterior).
        
        Args:
            df: DataFrame com colunas de moeda em formato string.
        
        Returns:
            Cópia do DataFrame com as colunas de moeda convertidas
            para ``float64``.
        """
        df = df.copy()
        
        # Pré-filtrar colunas presentes (evita verificar `in df.columns`
        # a cada iteração e permite processamento em lote).
        colunas_presentes: List[str] = [
            c for c in COLUNAS_MOEDA if c in df.columns
        ]
        if not colunas_presentes:
            return df
        
        coluna_especial = DataProcessor._COLUNA_MOEDA_ESPECIAL
        colunas_regulares = [
            c for c in colunas_presentes if c != coluna_especial
        ]
        
        # ===== Colunas regulares (regra única) em lote =====
        # Encadeia as transformações em poucas passadas sobre o
        # sub-DataFrame, reduzindo a quantidade de objetos
        # intermediários criados em relação ao loop original.
        if colunas_regulares:
            df[colunas_regulares] = (
                df[colunas_regulares]
                .astype(str)
                .apply(lambda s: s.str.strip().str.replace(',', '.', regex=False))
                .apply(lambda s: pd.to_numeric(s, errors='coerce'))
                .fillna(0)
            )
        
        # ===== Coluna especial (VALOR_SIMBOLO) =====
        # Regra adicional: remove separadores de milhar e caracteres
        # não numéricos antes da conversão.
        if coluna_especial in colunas_presentes:
            s = (
                df[coluna_especial]
                .astype(str)
                .str.strip()
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.replace(r'[^\d\.\-]', '', regex=True)
            )
            df[coluna_especial] = pd.to_numeric(s, errors='coerce').fillna(0)
        
        return df
    
    @staticmethod
    def converter_colunas_inteiro(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte colunas de inteiro de forma vetorizada.
        
        Processa todas as colunas listadas em ``COLUNAS_INTEIRO`` que
        existam no DataFrame, aplicando a mesma regra para todas:
        
        - Converte para numérico via ``pd.to_numeric`` com
          ``errors='coerce'`` (valores inválidos viram ``NaN``).
        - Substitui ``NaN`` por ``0``.
        - Converte o resultado para ``int`` (dtype ``int64`` do
          NumPy, mesmo comportamento da versão anterior).
        
        Args:
            df: DataFrame com colunas de inteiro em formato string
                ou numérico misto.
        
        Returns:
            Cópia do DataFrame com as colunas de inteiro convertidas
            para ``int64``.
        """
        df = df.copy()
        
        # Pré-filtrar colunas presentes (evita verificar `in df.columns`
        # a cada iteração e permite processamento em lote).
        colunas_presentes: List[str] = [
            c for c in COLUNAS_INTEIRO if c in df.columns
        ]
        if not colunas_presentes:
            return df
        
        # Processamento em lote: aplica pd.to_numeric coluna a coluna
        # via `apply` (cada coluna pode ter formato distinto), faz
        # fillna(0) global e astype(int) global — produzindo o mesmo
        # dtype int64 do loop original, com menos objetos
        # intermediários e sem dispatch Python-level entre colunas.
        df[colunas_presentes] = (
            df[colunas_presentes]
            .apply(lambda s: pd.to_numeric(s, errors='coerce'))
            .fillna(0)
            .astype(int)
        )
        
        return df
    
    @staticmethod
    def adicionar_coluna_ordem(df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona coluna ORDEM numerada"""
        df = df.copy()
        df['ORDEM'] = range(1, len(df) + 1)
        return df
