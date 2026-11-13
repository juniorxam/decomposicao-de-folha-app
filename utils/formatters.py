# utils/formatters.py
"""
Formatação de dados para Excel e outros formatos
"""

import io
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from config import COLUNAS_MOEDA, COLUNAS_INTEIRO, COLUNAS_TEXTO, COLUNAS_PERCENTUAL


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
            # Reserva a primeira linha para um título visível da planilha.
            df.to_excel(writer, sheet_name=nome_planilha, index=False, startrow=1)
            
            workbook = writer.book
            worksheet = writer.sheets[nome_planilha]
            
            # Definir formatos
            formatos = ExcelFormatter._criar_formatos(workbook)
            
            # Aplicar formatação
            ExcelFormatter._aplicar_formatacao(
                worksheet, df, formatos, workbook, nome_planilha
            )
        
        return output.getvalue()
    
    @staticmethod
    def _criar_formatos(workbook):
        """Cria os formatos para o Excel"""
        return {
            'header': workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter',
                'align': 'center', 'fg_color': '#1F4E78',
                'font_color': 'white', 'border': 1
            }),
            'title': workbook.add_format({
                'bold': True, 'font_size': 15, 'align': 'center',
                'valign': 'vcenter', 'fg_color': '#17365D',
                'font_color': 'white', 'border': 1
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
            'percentage': workbook.add_format({
                'num_format': '0.00%', 'align': 'center', 'valign': 'vcenter'
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
            }),
            'total': workbook.add_format({
                'bold': True, 'fg_color': '#FFF2CC', 'border': 1
            })
        }
    
    @staticmethod
    def _aplicar_formatacao(worksheet, df, formatos, workbook, nome_planilha):
        """Aplica formatação ao worksheet"""
        
        # Aplicar bordas
        num_linhas = len(df)
        num_colunas = len(df.columns)
        worksheet.merge_range(0, 0, 0, num_colunas - 1,
                              str(nome_planilha).upper(), formatos['title'])
        worksheet.set_row(0, 28)
        worksheet.conditional_format(1, 0, num_linhas + 1, num_colunas - 1, {
            'type': 'no_errors', 'format': formatos['border']
        })
        
        # Formatando cada coluna
        for i, col in enumerate(df.columns):
            # Cabeçalho
            worksheet.write(1, i, col, formatos['header'])
            
            # Largura
            largura = max(df[col].astype(str).map(len).max() if len(df) > 0 else 0, len(col))
            worksheet.set_column(i, i, min(max(largura + 2, 12), 42), formatos['content'])
            
            # Formatação específica por tipo de coluna
            if col in COLUNAS_MOEDA:
                ExcelFormatter._formatar_coluna_moeda(worksheet, df, col, i, formatos)
            elif col in COLUNAS_INTEIRO:
                ExcelFormatter._formatar_coluna_inteiro(worksheet, df, col, i, formatos)
            elif col in COLUNAS_PERCENTUAL:
                ExcelFormatter._formatar_coluna_percentual(worksheet, df, col, i, formatos)
            elif col in COLUNAS_TEXTO:
                ExcelFormatter._formatar_coluna_texto(worksheet, df, col, i, formatos)
        
        # Freeze panes e autofiltro
        worksheet.freeze_panes(2, 0)
        worksheet.autofilter(1, 0, num_linhas + 1, num_colunas - 1)
        if num_linhas:
            worksheet.conditional_format(2, 0, num_linhas + 1, num_colunas - 1, {
                'type': 'formula',
                'criteria': '=OR($A3="TOTAL",$A3="TOTAL GERAL")',
                'format': formatos['total']
            })
        
        # Formatação condicional
        ExcelFormatter._aplicar_formatacao_condicional(worksheet, df, formatos)
    
    @staticmethod
    def _formatar_coluna_moeda(worksheet, df, col, idx, formatos):
        """Formata coluna como moeda"""
        for data_idx, row_num in enumerate(range(2, len(df) + 2)):
            valor = df.iloc[data_idx][col]
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
        for data_idx, row_num in enumerate(range(2, len(df) + 2)):
            valor = df.iloc[data_idx][col]
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
        for data_idx, row_num in enumerate(range(2, len(df) + 2)):
            valor = df.iloc[data_idx][col]
            if pd.isna(valor) or valor == '' or valor is None:
                worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
            else:
                worksheet.write(row_num, idx, str(valor), formatos['text'])

    @staticmethod
    def _formatar_coluna_percentual(worksheet, df, col, idx, formatos):
        """Formata percentuais armazenados como valores de 0 a 100."""
        for data_idx, row_num in enumerate(range(2, len(df) + 2)):
            valor = df.iloc[data_idx][col]
            if pd.isna(valor) or valor == '' or valor is None:
                worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
            else:
                try:
                    worksheet.write_number(
                        row_num, idx, float(valor) / 100,
                        formatos['percentage']
                    )
                except (ValueError, TypeError):
                    worksheet.write(row_num, idx, 'SEM INFORMACAO', formatos['text'])
    
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
