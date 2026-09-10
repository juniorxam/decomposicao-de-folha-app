# utils/formatters.py
"""
Formatação de dados para Excel e outros formatos
"""

import io
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from config import COLUNAS_MOEDA, COLUNAS_INTEIRO, COLUNAS_TEXTO


class ExcelFormatter:
    """Classe para formatação de arquivos Excel"""
    
    @staticmethod
    def formatar_excel(
        df: pd.DataFrame, 
        nome_planilha: str = "Relatorio Tratado"
    ) -> bytes:
        """
        Salva DataFrame em Excel com formatação profissional
        
        Args:
            df: DataFrame a ser formatado
            nome_planilha: Nome da planilha
            
        Returns:
            bytes do arquivo Excel
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=nome_planilha, index=False)
            
            workbook = writer.book
            worksheet = writer.sheets[nome_planilha]
            
            # Definir formatos
            formatos = ExcelFormatter._criar_formatos(workbook)
            
            # Aplicar formatação
            ExcelFormatter._aplicar_formatacao(
                worksheet, df, formatos, workbook
            )
        
        return output.getvalue()
    
    @staticmethod
    def _criar_formatos(workbook):
        """Cria os formatos para o Excel"""
        return {
            'header': workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter',
                'align': 'center', 'fg_color': '#D7E4BC', 'border': 1
            }),
            'content': workbook.add_format({
                'align': 'center', 'valign': 'vcenter'
            }),
            'money': workbook.add_format({
                'num_format': 'R$ #,##0.00', 'align': 'center', 'valign': 'vcenter'
            }),
            'integer': workbook.add_format({
                'num_format': '0', 'align': 'center', 'valign': 'vcenter'
            }),
            'text': workbook.add_format({
                'align': 'center', 'valign': 'vcenter'
            }),
            'border': workbook.add_format({'border': 1}),
            'red': workbook.add_format({
                'font_color': '#FF0000', 'bold': True,
                'align': 'center', 'valign': 'vcenter'
            }),
            'orange': workbook.add_format({
                'font_color': '#FF6600', 'bold': True,
                'align': 'center', 'valign': 'vcenter'
            }),
            'gray': workbook.add_format({
                'font_color': '#999999', 'italic': True,
                'align': 'center', 'valign': 'vcenter'
            }),
            'idoso': workbook.add_format({
                'font_color': '#0066CC', 'bold': True,
                'align': 'center', 'valign': 'vcenter'
            })
        }
    
    @staticmethod
    def _aplicar_formatacao(worksheet, df, formatos, workbook):
        """Aplica formatação ao worksheet"""
        
        # Aplicar bordas
        num_linhas = len(df)
        num_colunas = len(df.columns)
        worksheet.conditional_format(0, 0, num_linhas, num_colunas - 1, {
            'type': 'no_errors', 'format': formatos['border']
        })
        
        # Formatando cada coluna
        for i, col in enumerate(df.columns):
            # Cabeçalho
            worksheet.write(0, i, col, formatos['header'])
            
            # Largura
            largura = max(df[col].astype(str).map(len).max() if len(df) > 0 else 0, len(col))
            worksheet.set_column(i, i, largura + 2, formatos['content'])
            
            # Formatação específica por tipo de coluna
            if col in COLUNAS_MOEDA:
                ExcelFormatter._formatar_coluna_moeda(worksheet, df, col, i, formatos)
            elif col in COLUNAS_INTEIRO:
                ExcelFormatter._formatar_coluna_inteiro(worksheet, df, col, i, formatos)
            elif col in COLUNAS_TEXTO:
                ExcelFormatter._formatar_coluna_texto(worksheet, df, col, i, formatos)
        
        # Freeze panes e autofiltro
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, num_linhas, num_colunas - 1)
        worksheet.set_row(0, 30)
        
        # Formatação condicional
        ExcelFormatter._aplicar_formatacao_condicional(worksheet, df, formatos)
    
    @staticmethod
    def _formatar_coluna_moeda(worksheet, df, col, idx, formatos):
        """Formata coluna como moeda"""
        for row_num in range(1, len(df) + 1):
            valor = df.iloc[row_num - 1][col]
            if pd.notna(valor) and valor != '' and valor is not None:
                try:
                    worksheet.write_number(row_num, idx, float(valor), formatos['money'])
                except (ValueError, TypeError):
                    worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
            else:
                worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
    
    @staticmethod
    def _formatar_coluna_inteiro(worksheet, df, col, idx, formatos):
        """Formata coluna como inteiro"""
        for row_num in range(1, len(df) + 1):
            valor = df.iloc[row_num - 1][col]
            if pd.isna(valor) or valor == '' or valor is None:
                worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
            else:
                try:
                    worksheet.write_number(row_num, idx, int(valor), formatos['integer'])
                except (ValueError, TypeError):
                    worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
    
    @staticmethod
    def _formatar_coluna_texto(worksheet, df, col, idx, formatos):
        """Formata coluna como texto"""
        for row_num in range(1, len(df) + 1):
            valor = df.iloc[row_num - 1][col]
            if pd.isna(valor) or valor == '' or valor is None:
                worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
            else:
                worksheet.write(row_num, idx, str(valor), formatos['text'])
    
    @staticmethod
    def _aplicar_formatacao_condicional(worksheet, df, formatos):
        """Aplica formatação condicional"""
        
        # Situação salarial
        if 'SITUACAO SALARIAL' in df.columns:
            col_idx = df.columns.get_loc('SITUACAO SALARIAL')
            
            worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                'type': 'text', 'criteria': 'containing',
                'value': 'ABAIXO DO MINIMO', 'format': formatos['red']
            })
            worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                'type': 'text', 'criteria': 'containing',
                'value': 'ACIMA DO TETO', 'format': formatos['orange']
            })
            worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                'type': 'text', 'criteria': 'containing',
                'value': 'SEM INFORMACAO', 'format': formatos['gray']
            })
        
        # Servidor idoso
        if 'SERVIDOR IDOSO' in df.columns:
            col_idx = df.columns.get_loc('SERVIDOR IDOSO')
            worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                'type': 'text', 'criteria': 'containing',
                'value': 'SIM', 'format': formatos['idoso']
            })