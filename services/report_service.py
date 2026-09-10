# services/report_service.py
"""
Serviço para geração de relatórios
"""

import pandas as pd
import io
from typing import Any, List, Optional
from utils.data_processors import DataProcessor
from utils.validators import DataValidator
from utils.formatters import ExcelFormatter


class ReportService:
    """Serviço para geração de relatórios"""
    
    # Vínculos considerados válidos para os relatórios detalhados e
    # resumidos. Usado em todos os métodos de geração de relatório.
    _VINCULOS_VALIDOS: List[str] = ['CONTRATADO', 'EFETIVO', 'COMISSIONADO']
    
    def __init__(self) -> None:
        self.processor: DataProcessor = DataProcessor()
        self.validator: DataValidator = DataValidator()
        self.formatter: ExcelFormatter = ExcelFormatter()
    
    # ==================== RELATÓRIO DETALHADO DE HOSPITAIS ====================
    
    def gerar_relatorio_hospitais(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Gera relatório de custo por hospital com quantidade e custo por vínculo.
        
        Para cada hospital, agrupa os registros por cargo e vínculo
        (CONTRATADO, EFETIVO, COMISSIONADO) e calcula a quantidade de
        servidores e o custo total. Inclui uma linha 'TOTAL' por hospital
        com os somatórios.
        
        Args:
            df: DataFrame processado contendo, no mínimo, as colunas
                'LOCAL', 'SETOR_AJUSTADO', 'CARGO', 'VINCULO' e
                'VALOR NIVEL/REF - com teto'.
        
        Returns:
            DataFrame com colunas [HOSPITAL, CARGO, CONTRATADO_QTD,
            CONTRATADO_CUSTO, EFETIVO_QTD, EFETIVO_CUSTO,
            COMISSIONADO_QTD, COMISSIONADO_CUSTO, TOTAL_QTD, TOTAL_CUSTO]
            ou None quando não houver hospitais, faltar alguma coluna
            necessária ou não houver vínculos válidos.
        """
        # Filtrar apenas hospitais
        df_hospitais = df[df['LOCAL'] == 'HOSPITAL'].copy()
        
        if df_hospitais.empty:
            return None
        
        # Verificar colunas necessárias
        colunas_necessarias = ['SETOR_AJUSTADO', 'CARGO', 'VINCULO', 'VALOR NIVEL/REF - com teto']
        for col in colunas_necessarias:
            if col not in df_hospitais.columns:
                return None
        
        # Mapear vínculos
        df_hospitais['VINCULO'] = df_hospitais['VINCULO'].astype(str).str.upper().str.strip()
        df_hospitais['VINCULO_MAPEADO'] = df_hospitais['VINCULO'].apply(
            self.processor.mapear_vinculo
        )
        
        # Filtrar vínculos válidos
        vinculos_validos = self._VINCULOS_VALIDOS
        df_hospitais = df_hospitais[df_hospitais['VINCULO_MAPEADO'].isin(vinculos_validos)]
        
        if df_hospitais.empty:
            return None
        
        df_hospitais['VINCULO'] = df_hospitais['VINCULO_MAPEADO']
        
        # Gerar relatório por hospital
        resultados = []
        hospitais = df_hospitais['SETOR_AJUSTADO'].unique()
        
        for hospital in hospitais:
            df_hospital = df_hospitais[df_hospitais['SETOR_AJUSTADO'] == hospital]
            
            # Agrupar por cargo e vínculo
            df_agrupado = df_hospital.groupby(['CARGO', 'VINCULO']).agg({
                'VALOR NIVEL/REF - com teto': ['count', 'sum']
            }).reset_index()
            
            df_agrupado.columns = ['CARGO', 'VINCULO', 'QTD', 'CUSTO']
            df_agrupado['CUSTO'] = df_agrupado['CUSTO'].fillna(0)
            
            # Criar pivô
            pivot_qtd = df_agrupado.pivot(index='CARGO', columns='VINCULO', values='QTD').fillna(0).astype(int)
            pivot_custo = df_agrupado.pivot(index='CARGO', columns='VINCULO', values='CUSTO').fillna(0)
            
            # Garantir colunas
            for vinculo in vinculos_validos:
                if vinculo not in pivot_qtd.columns:
                    pivot_qtd[vinculo] = 0
                    pivot_custo[vinculo] = 0
            
            pivot_qtd = pivot_qtd[vinculos_validos]
            pivot_custo = pivot_custo[vinculos_validos]
            
            # Criar DataFrame final
            df_final = pd.DataFrame(index=pivot_qtd.index)
            for vinculo in vinculos_validos:
                df_final[f'{vinculo}_QTD'] = pivot_qtd[vinculo]
                df_final[f'{vinculo}_CUSTO'] = pivot_custo[vinculo]
            
            df_final['TOTAL_QTD'] = df_final[[f'{v}_QTD' for v in vinculos_validos]].sum(axis=1)
            df_final['TOTAL_CUSTO'] = df_final[[f'{v}_CUSTO' for v in vinculos_validos]].sum(axis=1)
            
            # Remover cargos vazios
            mascara_zero = (df_final['CONTRATADO_QTD'] == 0) & (df_final['EFETIVO_QTD'] == 0) & (df_final['COMISSIONADO_QTD'] == 0)
            df_final = df_final[~mascara_zero]
            
            if df_final.empty:
                continue
            
            df_final = df_final.reset_index()
            df_final.rename(columns={'index': 'CARGO'}, inplace=True)
            
            # Adicionar total
            linha_total = pd.DataFrame({
                'CARGO': ['TOTAL'],
                **{f'{v}_QTD': [df_final[f'{v}_QTD'].sum()] for v in vinculos_validos},
                **{f'{v}_CUSTO': [df_final[f'{v}_CUSTO'].sum()] for v in vinculos_validos},
                'TOTAL_QTD': [df_final['TOTAL_QTD'].sum()],
                'TOTAL_CUSTO': [df_final['TOTAL_CUSTO'].sum()]
            })
            
            df_final = pd.concat([df_final, linha_total], ignore_index=True)
            df_final['HOSPITAL'] = hospital
            
            resultados.append(df_final)
        
        if not resultados:
            return None
        
        df_relatorio = pd.concat(resultados, ignore_index=True)
        
        # Reorganizar colunas
        colunas_ordem = [
            'HOSPITAL', 'CARGO',
            'CONTRATADO_QTD', 'CONTRATADO_CUSTO',
            'EFETIVO_QTD', 'EFETIVO_CUSTO',
            'COMISSIONADO_QTD', 'COMISSIONADO_CUSTO',
            'TOTAL_QTD', 'TOTAL_CUSTO'
        ]
        df_relatorio = df_relatorio[colunas_ordem]
        
        return df_relatorio
    
    def salvar_relatorio_hospitais(self, df_relatorio: pd.DataFrame) -> bytes:
        """
        Salva relatório de hospitais em Excel com formatação profissional.
        
        Cada hospital é escrito em uma aba própria (nome truncado para 31
        caracteres, limite do Excel), aplicando formatação de cabeçalho,
        moeda, inteiros e linha de total.
        
        Args:
            df_relatorio: DataFrame retornado por `gerar_relatorio_hospitais`.
        
        Returns:
            Bytes do arquivo .xlsx pronto para download.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            hospitais = df_relatorio['HOSPITAL'].unique()
            
            for hospital in hospitais:
                df_hospital = df_relatorio[df_relatorio['HOSPITAL'] == hospital].copy()
                df_hospital = df_hospital.drop('HOSPITAL', axis=1)
                
                sheet_name = str(hospital)[:31]
                
                # Escrever dados
                df_hospital.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
                
                worksheet = writer.sheets[sheet_name]
                
                # Formatação
                self._formatar_relatorio_geral(worksheet, workbook, df_hospital, str(hospital))
        
        return output.getvalue()
    
    # ==================== RELATÓRIO DETALHADO DE SUPERINTENDÊNCIAS ====================
    
    def gerar_relatorio_superintendencias(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Gera relatório de custo por superintendência com quantidade e
        custo por vínculo.
        
        Para cada superintendência, agrupa os registros por cargo e
        vínculo (CONTRATADO, EFETIVO, COMISSIONADO) e calcula a
        quantidade de servidores e o custo total. Inclui uma linha
        'TOTAL' por superintendência com os somatórios.
        
        Args:
            df: DataFrame processado contendo, no mínimo, as colunas
                'SUPERINTENDENCIA', 'CARGO', 'VINCULO' e
                'VALOR NIVEL/REF - com teto'.
        
        Returns:
            DataFrame com colunas [SUPERINTENDENCIA, CARGO,
            CONTRATADO_QTD, CONTRATADO_CUSTO, EFETIVO_QTD,
            EFETIVO_CUSTO, COMISSIONADO_QTD, COMISSIONADO_CUSTO,
            TOTAL_QTD, TOTAL_CUSTO] ou None quando não houver
            superintendências, faltar alguma coluna necessária ou
            não houver vínculos válidos.
        """
        # Filtrar apenas registros com SUPERINTENDENCIA preenchida
        df_super = df[df['SUPERINTENDENCIA'].notna() & (df['SUPERINTENDENCIA'] != '')].copy()
        
        if df_super.empty:
            return None
        
        # Verificar se as colunas necessárias existem
        colunas_necessarias = ['SUPERINTENDENCIA', 'CARGO', 'VINCULO', 'VALOR NIVEL/REF - com teto']
        for col in colunas_necessarias:
            if col not in df_super.columns:
                return None
        
        # Garantir que os vínculos estejam no formato correto
        df_super['VINCULO'] = df_super['VINCULO'].astype(str).str.upper().str.strip()
        
        # Mapear vínculos
        df_super['VINCULO_MAPEADO'] = df_super['VINCULO'].apply(
            self.processor.mapear_vinculo
        )
        
        # Filtrar apenas os vínculos que nos interessam
        vinculos_validos = self._VINCULOS_VALIDOS
        df_super = df_super[df_super['VINCULO_MAPEADO'].isin(vinculos_validos)]
        
        if df_super.empty:
            return None
        
        df_super['VINCULO'] = df_super['VINCULO_MAPEADO']
        
        # Lista para armazenar os resultados
        resultados = []
        superintendencias = df_super['SUPERINTENDENCIA'].unique()
        
        for superintendencia in superintendencias:
            df_super_item = df_super[df_super['SUPERINTENDENCIA'] == superintendencia]
            
            # Agrupar por cargo e vínculo
            df_agrupado = df_super_item.groupby(['CARGO', 'VINCULO']).agg({
                'VALOR NIVEL/REF - com teto': ['count', 'sum']
            }).reset_index()
            
            df_agrupado.columns = ['CARGO', 'VINCULO', 'QTD', 'CUSTO']
            df_agrupado['CUSTO'] = df_agrupado['CUSTO'].fillna(0)
            
            # Criar pivô
            pivot_qtd = df_agrupado.pivot(index='CARGO', columns='VINCULO', values='QTD').fillna(0).astype(int)
            pivot_custo = df_agrupado.pivot(index='CARGO', columns='VINCULO', values='CUSTO').fillna(0)
            
            # Garantir colunas
            for vinculo in vinculos_validos:
                if vinculo not in pivot_qtd.columns:
                    pivot_qtd[vinculo] = 0
                    pivot_custo[vinculo] = 0
            
            pivot_qtd = pivot_qtd[vinculos_validos]
            pivot_custo = pivot_custo[vinculos_validos]
            
            # Criar DataFrame final
            df_final = pd.DataFrame(index=pivot_qtd.index)
            for vinculo in vinculos_validos:
                df_final[f'{vinculo}_QTD'] = pivot_qtd[vinculo]
                df_final[f'{vinculo}_CUSTO'] = pivot_custo[vinculo]
            
            df_final['TOTAL_QTD'] = df_final[[f'{v}_QTD' for v in vinculos_validos]].sum(axis=1)
            df_final['TOTAL_CUSTO'] = df_final[[f'{v}_CUSTO' for v in vinculos_validos]].sum(axis=1)
            
            # Remover cargos vazios
            mascara_zero = (df_final['CONTRATADO_QTD'] == 0) & (df_final['EFETIVO_QTD'] == 0) & (df_final['COMISSIONADO_QTD'] == 0)
            df_final = df_final[~mascara_zero]
            
            if df_final.empty:
                continue
            
            df_final = df_final.reset_index()
            df_final.rename(columns={'index': 'CARGO'}, inplace=True)
            
            # Remover linhas com cargo vazio
            df_final = df_final[df_final['CARGO'].notna()]
            df_final = df_final[df_final['CARGO'] != '']
            df_final = df_final[df_final['CARGO'] != 'None']
            
            # Adicionar linha de total
            linha_total = pd.DataFrame({
                'CARGO': ['TOTAL'],
                'CONTRATADO_QTD': [df_final['CONTRATADO_QTD'].sum()],
                'CONTRATADO_CUSTO': [df_final['CONTRATADO_CUSTO'].sum()],
                'EFETIVO_QTD': [df_final['EFETIVO_QTD'].sum()],
                'EFETIVO_CUSTO': [df_final['EFETIVO_CUSTO'].sum()],
                'COMISSIONADO_QTD': [df_final['COMISSIONADO_QTD'].sum()],
                'COMISSIONADO_CUSTO': [df_final['COMISSIONADO_CUSTO'].sum()],
                'TOTAL_QTD': [df_final['TOTAL_QTD'].sum()],
                'TOTAL_CUSTO': [df_final['TOTAL_CUSTO'].sum()]
            })
            
            df_final = pd.concat([df_final, linha_total], ignore_index=True)
            df_final['SUPERINTENDENCIA'] = superintendencia
            
            resultados.append(df_final)
        
        if not resultados:
            return None
        
        df_relatorio = pd.concat(resultados, ignore_index=True)
        
        # Reorganizar colunas
        colunas_ordem = [
            'SUPERINTENDENCIA', 'CARGO',
            'CONTRATADO_QTD', 'CONTRATADO_CUSTO',
            'EFETIVO_QTD', 'EFETIVO_CUSTO',
            'COMISSIONADO_QTD', 'COMISSIONADO_CUSTO',
            'TOTAL_QTD', 'TOTAL_CUSTO'
        ]
        df_relatorio = df_relatorio[colunas_ordem]
        
        return df_relatorio
    
    def salvar_relatorio_superintendencias(self, df_relatorio: pd.DataFrame) -> bytes:
        """
        Salva relatório de superintendências em Excel com formatação
        profissional.
        
        Cada superintendência é escrita em uma aba própria (nome
        truncado para 31 caracteres, limite do Excel), aplicando
        formatação de cabeçalho, moeda, inteiros e linha de total.
        
        Args:
            df_relatorio: DataFrame retornado por
                `gerar_relatorio_superintendencias`.
        
        Returns:
            Bytes do arquivo .xlsx pronto para download.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            superintendencias = df_relatorio['SUPERINTENDENCIA'].unique()
            
            for superintendencia in superintendencias:
                df_super = df_relatorio[df_relatorio['SUPERINTENDENCIA'] == superintendencia].copy()
                df_super = df_super.drop('SUPERINTENDENCIA', axis=1)
                
                sheet_name = str(superintendencia)[:31]
                
                df_super.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
                
                worksheet = writer.sheets[sheet_name]
                
                # Formatação
                self._formatar_relatorio_geral(worksheet, workbook, df_super, str(superintendencia))
        
        return output.getvalue()
    
    # ==================== RELATÓRIO RESUMIDO DE HOSPITAIS ====================
    
    def gerar_relatorio_hospitais_resumido(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Gera relatório resumido de custo por hospital (sem detalhamento
        por cargo).
        
        Para cada hospital, calcula a quantidade de servidores e o custo
        total por vínculo (CONTRATADO, EFETIVO, COMISSIONADO) e o total
        geral. O resultado é ordenado pelo custo total (maior para menor)
        e finaliza com uma linha 'TOTAL GERAL'.
        
        Args:
            df: DataFrame processado contendo, no mínimo, as colunas
                'LOCAL', 'SETOR_AJUSTADO', 'VINCULO' e
                'VALOR NIVEL/REF - com teto'.
        
        Returns:
            DataFrame com colunas [HOSPITAL, CONTRATADO_QTD,
            CONTRATADO_CUSTO, EFETIVO_QTD, EFETIVO_CUSTO,
            COMISSIONADO_QTD, COMISSIONADO_CUSTO, TOTAL_QTD,
            TOTAL_CUSTO] ou None quando não houver hospitais, faltar
            alguma coluna necessária ou não houver vínculos válidos.
        """
        # Filtrar apenas hospitais
        df_hospitais = df[df['LOCAL'] == 'HOSPITAL'].copy()
        
        if df_hospitais.empty:
            return None
        
        # Verificar colunas necessárias
        colunas_necessarias = ['SETOR_AJUSTADO', 'VINCULO', 'VALOR NIVEL/REF - com teto']
        for col in colunas_necessarias:
            if col not in df_hospitais.columns:
                return None
        
        # Mapear vínculos
        df_hospitais['VINCULO'] = df_hospitais['VINCULO'].astype(str).str.upper().str.strip()
        df_hospitais['VINCULO_MAPEADO'] = df_hospitais['VINCULO'].apply(
            self.processor.mapear_vinculo
        )
        
        # Filtrar vínculos válidos
        vinculos_validos = self._VINCULOS_VALIDOS
        df_hospitais = df_hospitais[df_hospitais['VINCULO_MAPEADO'].isin(vinculos_validos)]
        
        if df_hospitais.empty:
            return None
        
        df_hospitais['VINCULO'] = df_hospitais['VINCULO_MAPEADO']
        
        # Lista para armazenar os resultados
        resultados = []
        hospitais = df_hospitais['SETOR_AJUSTADO'].unique()
        
        for hospital in hospitais:
            df_hospital = df_hospitais[df_hospitais['SETOR_AJUSTADO'] == hospital]
            
            # Agrupar apenas por vínculo (sem cargo)
            df_agrupado = df_hospital.groupby(['VINCULO']).agg({
                'VALOR NIVEL/REF - com teto': ['count', 'sum']
            }).reset_index()
            
            df_agrupado.columns = ['VINCULO', 'QTD', 'CUSTO']
            df_agrupado['CUSTO'] = df_agrupado['CUSTO'].fillna(0)
            
            # Criar linha para o hospital
            linha_hospital = {
                'HOSPITAL': hospital,
                'TOTAL_QTD': df_agrupado['QTD'].sum(),
                'TOTAL_CUSTO': df_agrupado['CUSTO'].sum()
            }
            
            # Adicionar colunas por vínculo
            for vinculo in vinculos_validos:
                vinculo_data = df_agrupado[df_agrupado['VINCULO'] == vinculo]
                if not vinculo_data.empty:
                    linha_hospital[f'{vinculo}_QTD'] = vinculo_data['QTD'].iloc[0]
                    linha_hospital[f'{vinculo}_CUSTO'] = vinculo_data['CUSTO'].iloc[0]
                else:
                    linha_hospital[f'{vinculo}_QTD'] = 0
                    linha_hospital[f'{vinculo}_CUSTO'] = 0
            
            resultados.append(linha_hospital)
        
        if not resultados:
            return None
        
        df_relatorio = pd.DataFrame(resultados)
        
        # Reorganizar colunas
        colunas_ordem = [
            'HOSPITAL',
            'CONTRATADO_QTD', 'CONTRATADO_CUSTO',
            'EFETIVO_QTD', 'EFETIVO_CUSTO',
            'COMISSIONADO_QTD', 'COMISSIONADO_CUSTO',
            'TOTAL_QTD', 'TOTAL_CUSTO'
        ]
        df_relatorio = df_relatorio[colunas_ordem]
        
        # Ordenar por total de custo (maior para menor)
        df_relatorio = df_relatorio.sort_values('TOTAL_CUSTO', ascending=False)
        
        # Adicionar linha de total geral
        linha_total = {
            'HOSPITAL': 'TOTAL GERAL',
            'CONTRATADO_QTD': df_relatorio['CONTRATADO_QTD'].sum(),
            'CONTRATADO_CUSTO': df_relatorio['CONTRATADO_CUSTO'].sum(),
            'EFETIVO_QTD': df_relatorio['EFETIVO_QTD'].sum(),
            'EFETIVO_CUSTO': df_relatorio['EFETIVO_CUSTO'].sum(),
            'COMISSIONADO_QTD': df_relatorio['COMISSIONADO_QTD'].sum(),
            'COMISSIONADO_CUSTO': df_relatorio['COMISSIONADO_CUSTO'].sum(),
            'TOTAL_QTD': df_relatorio['TOTAL_QTD'].sum(),
            'TOTAL_CUSTO': df_relatorio['TOTAL_CUSTO'].sum()
        }
        df_relatorio = pd.concat([df_relatorio, pd.DataFrame([linha_total])], ignore_index=True)
        
        return df_relatorio
    
    def salvar_relatorio_hospitais_resumido(self, df_relatorio: pd.DataFrame) -> bytes:
        """
        Salva relatório resumido de hospitais em Excel com formatação
        profissional.
        
        Cria uma única aba 'Resumo Hospitais' com cabeçalho de dois
        níveis (vínculos e QTD/CUSTO), linha de TOTAL GERAL destacada
        em amarelo, bordas, larguras de coluna, freeze panes e
        autofiltro.
        
        Args:
            df_relatorio: DataFrame retornado por
                `gerar_relatorio_hospitais_resumido`.
        
        Returns:
            Bytes do arquivo .xlsx pronto para download.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Resumo Hospitais')
            
            # Formatos
            title_format = workbook.add_format({
                'bold': True, 'font_size': 16, 'align': 'center',
                'valign': 'vcenter', 'fg_color': '#4472C4',
                'font_color': 'white', 'border': 1
            })
            
            header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter',
                'align': 'center', 'fg_color': '#D7E4BC', 'border': 1
            })
            
            sub_header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter',
                'align': 'center', 'fg_color': '#E8F0FE', 'border': 1
            })
            
            money_format = workbook.add_format({
                'num_format': 'R$ #,##0.00', 'align': 'right',
                'valign': 'vcenter', 'border': 1
            })
            
            integer_format = workbook.add_format({
                'num_format': '0', 'align': 'center',
                'valign': 'vcenter', 'border': 1
            })
            
            text_format = workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'border': 1
            })
            
            total_text_format = workbook.add_format({
                'bold': True, 'align': 'left', 'valign': 'vcenter',
                'border': 1, 'fg_color': '#FFE4B5'
            })
            
            total_qtd_format = workbook.add_format({
                'bold': True, 'num_format': '0', 'align': 'center',
                'valign': 'vcenter', 'border': 1, 'fg_color': '#FFE4B5'
            })
            
            total_money_format = workbook.add_format({
                'bold': True, 'num_format': 'R$ #,##0.00', 'align': 'right',
                'valign': 'vcenter', 'border': 1, 'fg_color': '#FFE4B5'
            })
            
            # Título
            worksheet.merge_range(0, 0, 0, 8, 'RESUMO DE CUSTO POR HOSPITAL', title_format)
            
            # Cabeçalho
            worksheet.write(1, 0, 'HOSPITAL', header_format)
            worksheet.merge_range(1, 1, 1, 2, 'CONTRATADO', header_format)
            worksheet.merge_range(1, 3, 1, 4, 'EFETIVO', header_format)
            worksheet.merge_range(1, 5, 1, 6, 'COMISSIONADO', header_format)
            worksheet.merge_range(1, 7, 1, 8, 'TOTAL', header_format)
            
            worksheet.write(2, 0, '', sub_header_format)
            worksheet.write(2, 1, 'QTD', sub_header_format)
            worksheet.write(2, 2, 'CUSTO', sub_header_format)
            worksheet.write(2, 3, 'QTD', sub_header_format)
            worksheet.write(2, 4, 'CUSTO', sub_header_format)
            worksheet.write(2, 5, 'QTD', sub_header_format)
            worksheet.write(2, 6, 'CUSTO', sub_header_format)
            worksheet.write(2, 7, 'QTD', sub_header_format)
            worksheet.write(2, 8, 'CUSTO', sub_header_format)
            
            # Dados
            for row_num, (idx, row) in enumerate(df_relatorio.iterrows(), start=3):
                is_total = row['HOSPITAL'] == 'TOTAL GERAL'
                
                if is_total:
                    worksheet.write(row_num, 0, row['HOSPITAL'], total_text_format)
                    worksheet.write(row_num, 1, row['CONTRATADO_QTD'], total_qtd_format)
                    worksheet.write(row_num, 2, row['CONTRATADO_CUSTO'], total_money_format)
                    worksheet.write(row_num, 3, row['EFETIVO_QTD'], total_qtd_format)
                    worksheet.write(row_num, 4, row['EFETIVO_CUSTO'], total_money_format)
                    worksheet.write(row_num, 5, row['COMISSIONADO_QTD'], total_qtd_format)
                    worksheet.write(row_num, 6, row['COMISSIONADO_CUSTO'], total_money_format)
                    worksheet.write(row_num, 7, row['TOTAL_QTD'], total_qtd_format)
                    worksheet.write(row_num, 8, row['TOTAL_CUSTO'], total_money_format)
                else:
                    worksheet.write(row_num, 0, row['HOSPITAL'], text_format)
                    worksheet.write(row_num, 1, row['CONTRATADO_QTD'], integer_format)
                    worksheet.write(row_num, 2, row['CONTRATADO_CUSTO'], money_format)
                    worksheet.write(row_num, 3, row['EFETIVO_QTD'], integer_format)
                    worksheet.write(row_num, 4, row['EFETIVO_CUSTO'], money_format)
                    worksheet.write(row_num, 5, row['COMISSIONADO_QTD'], integer_format)
                    worksheet.write(row_num, 6, row['COMISSIONADO_CUSTO'], money_format)
                    worksheet.write(row_num, 7, row['TOTAL_QTD'], integer_format)
                    worksheet.write(row_num, 8, row['TOTAL_CUSTO'], money_format)
            
            # Bordas
            border_format = workbook.add_format({'border': 1})
            ultima_linha = 3 + len(df_relatorio) - 1
            worksheet.conditional_format(1, 0, ultima_linha, 8, {
                'type': 'no_errors', 'format': border_format
            })
            
            # Larguras
            worksheet.set_column(0, 0, 45)
            for col in range(1, 9):
                worksheet.set_column(col, col, 18 if col % 2 == 0 else 10)
            
            worksheet.freeze_panes(3, 0)
            worksheet.autofilter(1, 0, ultima_linha, 8)
        
        return output.getvalue()
    
    # ==================== RELATÓRIO RESUMIDO DE SUPERINTENDÊNCIAS ====================
    
    def gerar_relatorio_superintendencias_resumido(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Gera relatório resumido de custo por superintendência (sem
        detalhamento por cargo).
        
        Para cada superintendência, calcula a quantidade de servidores e
        o custo total por vínculo (CONTRATADO, EFETIVO, COMISSIONADO) e
        o total geral. O resultado é ordenado pelo custo total (maior
        para menor) e finaliza com uma linha 'TOTAL GERAL'.
        
        Args:
            df: DataFrame processado contendo, no mínimo, as colunas
                'SUPERINTENDENCIA', 'VINCULO' e
                'VALOR NIVEL/REF - com teto'.
        
        Returns:
            DataFrame com colunas [SUPERINTENDENCIA, CONTRATADO_QTD,
            CONTRATADO_CUSTO, EFETIVO_QTD, EFETIVO_CUSTO,
            COMISSIONADO_QTD, COMISSIONADO_CUSTO, TOTAL_QTD,
            TOTAL_CUSTO] ou None quando não houver superintendências,
            faltar alguma coluna necessária ou não houver vínculos
            válidos.
        """
        # Filtrar apenas registros com SUPERINTENDENCIA preenchida
        df_super = df[df['SUPERINTENDENCIA'].notna() & (df['SUPERINTENDENCIA'] != '')].copy()
        
        if df_super.empty:
            return None
        
        # Verificar colunas necessárias
        colunas_necessarias = ['SUPERINTENDENCIA', 'VINCULO', 'VALOR NIVEL/REF - com teto']
        for col in colunas_necessarias:
            if col not in df_super.columns:
                return None
        
        # Mapear vínculos
        df_super['VINCULO'] = df_super['VINCULO'].astype(str).str.upper().str.strip()
        df_super['VINCULO_MAPEADO'] = df_super['VINCULO'].apply(
            self.processor.mapear_vinculo
        )
        
        # Filtrar vínculos válidos
        vinculos_validos = self._VINCULOS_VALIDOS
        df_super = df_super[df_super['VINCULO_MAPEADO'].isin(vinculos_validos)]
        
        if df_super.empty:
            return None
        
        df_super['VINCULO'] = df_super['VINCULO_MAPEADO']
        
        # Lista para armazenar os resultados
        resultados = []
        superintendencias = df_super['SUPERINTENDENCIA'].unique()
        
        for superintendencia in superintendencias:
            df_super_item = df_super[df_super['SUPERINTENDENCIA'] == superintendencia]
            
            # Agrupar apenas por vínculo (sem cargo)
            df_agrupado = df_super_item.groupby(['VINCULO']).agg({
                'VALOR NIVEL/REF - com teto': ['count', 'sum']
            }).reset_index()
            
            df_agrupado.columns = ['VINCULO', 'QTD', 'CUSTO']
            df_agrupado['CUSTO'] = df_agrupado['CUSTO'].fillna(0)
            
            # Criar linha para a superintendência
            linha_super = {
                'SUPERINTENDENCIA': superintendencia,
                'TOTAL_QTD': df_agrupado['QTD'].sum(),
                'TOTAL_CUSTO': df_agrupado['CUSTO'].sum()
            }
            
            # Adicionar colunas por vínculo
            for vinculo in vinculos_validos:
                vinculo_data = df_agrupado[df_agrupado['VINCULO'] == vinculo]
                if not vinculo_data.empty:
                    linha_super[f'{vinculo}_QTD'] = vinculo_data['QTD'].iloc[0]
                    linha_super[f'{vinculo}_CUSTO'] = vinculo_data['CUSTO'].iloc[0]
                else:
                    linha_super[f'{vinculo}_QTD'] = 0
                    linha_super[f'{vinculo}_CUSTO'] = 0
            
            resultados.append(linha_super)
        
        if not resultados:
            return None
        
        df_relatorio = pd.DataFrame(resultados)
        
        # Reorganizar colunas
        colunas_ordem = [
            'SUPERINTENDENCIA',
            'CONTRATADO_QTD', 'CONTRATADO_CUSTO',
            'EFETIVO_QTD', 'EFETIVO_CUSTO',
            'COMISSIONADO_QTD', 'COMISSIONADO_CUSTO',
            'TOTAL_QTD', 'TOTAL_CUSTO'
        ]
        df_relatorio = df_relatorio[colunas_ordem]
        
        # Ordenar por total de custo (maior para menor)
        df_relatorio = df_relatorio.sort_values('TOTAL_CUSTO', ascending=False)
        
        # Adicionar linha de total geral
        linha_total = {
            'SUPERINTENDENCIA': 'TOTAL GERAL',
            'CONTRATADO_QTD': df_relatorio['CONTRATADO_QTD'].sum(),
            'CONTRATADO_CUSTO': df_relatorio['CONTRATADO_CUSTO'].sum(),
            'EFETIVO_QTD': df_relatorio['EFETIVO_QTD'].sum(),
            'EFETIVO_CUSTO': df_relatorio['EFETIVO_CUSTO'].sum(),
            'COMISSIONADO_QTD': df_relatorio['COMISSIONADO_QTD'].sum(),
            'COMISSIONADO_CUSTO': df_relatorio['COMISSIONADO_CUSTO'].sum(),
            'TOTAL_QTD': df_relatorio['TOTAL_QTD'].sum(),
            'TOTAL_CUSTO': df_relatorio['TOTAL_CUSTO'].sum()
        }
        df_relatorio = pd.concat([df_relatorio, pd.DataFrame([linha_total])], ignore_index=True)
        
        return df_relatorio
    
    def salvar_relatorio_superintendencias_resumido(self, df_relatorio: pd.DataFrame) -> bytes:
        """
        Salva relatório resumido de superintendências em Excel com
        formatação profissional.
        
        Cria uma única aba 'Resumo Superintendencias' com cabeçalho de
        dois níveis (vínculos e QTD/CUSTO), linha de TOTAL GERAL
        destacada em amarelo, bordas, larguras de coluna, freeze panes
        e autofiltro.
        
        Args:
            df_relatorio: DataFrame retornado por
                `gerar_relatorio_superintendencias_resumido`.
        
        Returns:
            Bytes do arquivo .xlsx pronto para download.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Resumo Superintendencias')
            
            # Formatos
            title_format = workbook.add_format({
                'bold': True, 'font_size': 16, 'align': 'center',
                'valign': 'vcenter', 'fg_color': '#4472C4',
                'font_color': 'white', 'border': 1
            })
            
            header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter',
                'align': 'center', 'fg_color': '#D7E4BC', 'border': 1
            })
            
            sub_header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter',
                'align': 'center', 'fg_color': '#E8F0FE', 'border': 1
            })
            
            money_format = workbook.add_format({
                'num_format': 'R$ #,##0.00', 'align': 'right',
                'valign': 'vcenter', 'border': 1
            })
            
            integer_format = workbook.add_format({
                'num_format': '0', 'align': 'center',
                'valign': 'vcenter', 'border': 1
            })
            
            text_format = workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'border': 1
            })
            
            total_text_format = workbook.add_format({
                'bold': True, 'align': 'left', 'valign': 'vcenter',
                'border': 1, 'fg_color': '#FFE4B5'
            })
            
            total_qtd_format = workbook.add_format({
                'bold': True, 'num_format': '0', 'align': 'center',
                'valign': 'vcenter', 'border': 1, 'fg_color': '#FFE4B5'
            })
            
            total_money_format = workbook.add_format({
                'bold': True, 'num_format': 'R$ #,##0.00', 'align': 'right',
                'valign': 'vcenter', 'border': 1, 'fg_color': '#FFE4B5'
            })
            
            # Título
            worksheet.merge_range(0, 0, 0, 8, 'RESUMO DE CUSTO POR SUPERINTENDÊNCIA', title_format)
            
            # Cabeçalho
            worksheet.write(1, 0, 'SUPERINTENDÊNCIA', header_format)
            worksheet.merge_range(1, 1, 1, 2, 'CONTRATADO', header_format)
            worksheet.merge_range(1, 3, 1, 4, 'EFETIVO', header_format)
            worksheet.merge_range(1, 5, 1, 6, 'COMISSIONADO', header_format)
            worksheet.merge_range(1, 7, 1, 8, 'TOTAL', header_format)
            
            worksheet.write(2, 0, '', sub_header_format)
            worksheet.write(2, 1, 'QTD', sub_header_format)
            worksheet.write(2, 2, 'CUSTO', sub_header_format)
            worksheet.write(2, 3, 'QTD', sub_header_format)
            worksheet.write(2, 4, 'CUSTO', sub_header_format)
            worksheet.write(2, 5, 'QTD', sub_header_format)
            worksheet.write(2, 6, 'CUSTO', sub_header_format)
            worksheet.write(2, 7, 'QTD', sub_header_format)
            worksheet.write(2, 8, 'CUSTO', sub_header_format)
            
            # Dados
            for row_num, (idx, row) in enumerate(df_relatorio.iterrows(), start=3):
                is_total = row['SUPERINTENDENCIA'] == 'TOTAL GERAL'
                
                if is_total:
                    worksheet.write(row_num, 0, row['SUPERINTENDENCIA'], total_text_format)
                    worksheet.write(row_num, 1, row['CONTRATADO_QTD'], total_qtd_format)
                    worksheet.write(row_num, 2, row['CONTRATADO_CUSTO'], total_money_format)
                    worksheet.write(row_num, 3, row['EFETIVO_QTD'], total_qtd_format)
                    worksheet.write(row_num, 4, row['EFETIVO_CUSTO'], total_money_format)
                    worksheet.write(row_num, 5, row['COMISSIONADO_QTD'], total_qtd_format)
                    worksheet.write(row_num, 6, row['COMISSIONADO_CUSTO'], total_money_format)
                    worksheet.write(row_num, 7, row['TOTAL_QTD'], total_qtd_format)
                    worksheet.write(row_num, 8, row['TOTAL_CUSTO'], total_money_format)
                else:
                    worksheet.write(row_num, 0, row['SUPERINTENDENCIA'], text_format)
                    worksheet.write(row_num, 1, row['CONTRATADO_QTD'], integer_format)
                    worksheet.write(row_num, 2, row['CONTRATADO_CUSTO'], money_format)
                    worksheet.write(row_num, 3, row['EFETIVO_QTD'], integer_format)
                    worksheet.write(row_num, 4, row['EFETIVO_CUSTO'], money_format)
                    worksheet.write(row_num, 5, row['COMISSIONADO_QTD'], integer_format)
                    worksheet.write(row_num, 6, row['COMISSIONADO_CUSTO'], money_format)
                    worksheet.write(row_num, 7, row['TOTAL_QTD'], integer_format)
                    worksheet.write(row_num, 8, row['TOTAL_CUSTO'], money_format)
            
            # Bordas
            border_format = workbook.add_format({'border': 1})
            ultima_linha = 3 + len(df_relatorio) - 1
            worksheet.conditional_format(1, 0, ultima_linha, 8, {
                'type': 'no_errors', 'format': border_format
            })
            
            # Larguras
            worksheet.set_column(0, 0, 45)
            for col in range(1, 9):
                worksheet.set_column(col, col, 18 if col % 2 == 0 else 10)
            
            worksheet.freeze_panes(3, 0)
            worksheet.autofilter(1, 0, ultima_linha, 8)
        
        return output.getvalue()
    
    # ==================== MÉTODOS REUTILIZÁVEIS ====================
    
    def _formatar_relatorio_geral(
        self,
        worksheet: Any,
        workbook: Any,
        df: pd.DataFrame,
        titulo: str
    ) -> None:
        """
        Formata relatório geral (usado para hospitais, superintendências,
        etc.).
        
        Aplica título na linha 0, cabeçalho de dois níveis nas linhas
        1-2 (vínculos e QTD/CUSTO) e os dados a partir da linha 3.
        Linhas cuja coluna 'CARGO' seja 'TOTAL' recebem formatação em
        negrito. Aplica bordas, larguras de coluna, freeze panes e
        autofiltro.
        
        Args:
            worksheet: Objeto worksheet do xlsxwriter (já criado e com
                os dados escritos a partir da linha 2).
            workbook: Objeto workbook do xlsxwriter (para criação dos
                formatos).
            df: DataFrame cujas colunas e número de linhas definem as
                bordas e larguras aplicadas.
            titulo: Texto exibido na célula de título (linha 0).
        """
        # Formatos
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter', 'fg_color': '#4472C4',
            'font_color': 'white', 'border': 1
        })
        
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'align': 'center', 'fg_color': '#D7E4BC', 'border': 1
        })
        
        sub_header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'align': 'center', 'fg_color': '#E8F0FE', 'border': 1
        })
        
        money_format = workbook.add_format({
            'num_format': 'R$ #,##0.00', 'align': 'right',
            'valign': 'vcenter', 'border': 1
        })
        
        integer_format = workbook.add_format({
            'num_format': '0', 'align': 'center',
            'valign': 'vcenter', 'border': 1
        })
        
        text_format = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1
        })
        
        total_text_format = workbook.add_format({
            'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1
        })
        
        total_qtd_format = workbook.add_format({
            'bold': True, 'num_format': '0', 'align': 'center',
            'valign': 'vcenter', 'border': 1
        })
        
        total_money_format = workbook.add_format({
            'bold': True, 'num_format': 'R$ #,##0.00', 'align': 'right',
            'valign': 'vcenter', 'border': 1
        })
        
        # Título
        worksheet.merge_range(0, 0, 0, 8, titulo, title_format)
        
        # Cabeçalho
        worksheet.write(1, 0, 'CARGO', header_format)
        worksheet.merge_range(1, 1, 1, 2, 'CONTRATATO', header_format)
        worksheet.merge_range(1, 3, 1, 4, 'EFETIVO', header_format)
        worksheet.merge_range(1, 5, 1, 6, 'COMISSIONADO', header_format)
        worksheet.merge_range(1, 7, 1, 8, 'TOTAL', header_format)
        
        worksheet.write(2, 0, '', sub_header_format)
        worksheet.write(2, 1, 'QTD', sub_header_format)
        worksheet.write(2, 2, 'CUSTO', sub_header_format)
        worksheet.write(2, 3, 'QTD', sub_header_format)
        worksheet.write(2, 4, 'CUSTO', sub_header_format)
        worksheet.write(2, 5, 'QTD', sub_header_format)
        worksheet.write(2, 6, 'CUSTO', sub_header_format)
        worksheet.write(2, 7, 'QTD', sub_header_format)
        worksheet.write(2, 8, 'CUSTO', sub_header_format)
        
        # Dados
        for row_num, (idx, row) in enumerate(df.iterrows(), start=3):
            is_total = row['CARGO'] == 'TOTAL'
            
            if is_total:
                worksheet.write(row_num, 0, row['CARGO'], total_text_format)
                worksheet.write(row_num, 1, row['CONTRATADO_QTD'], total_qtd_format)
                worksheet.write(row_num, 2, row['CONTRATADO_CUSTO'], total_money_format)
                worksheet.write(row_num, 3, row['EFETIVO_QTD'], total_qtd_format)
                worksheet.write(row_num, 4, row['EFETIVO_CUSTO'], total_money_format)
                worksheet.write(row_num, 5, row['COMISSIONADO_QTD'], total_qtd_format)
                worksheet.write(row_num, 6, row['COMISSIONADO_CUSTO'], total_money_format)
                worksheet.write(row_num, 7, row['TOTAL_QTD'], total_qtd_format)
                worksheet.write(row_num, 8, row['TOTAL_CUSTO'], total_money_format)
            else:
                worksheet.write(row_num, 0, row['CARGO'], text_format)
                worksheet.write(row_num, 1, row['CONTRATADO_QTD'], integer_format)
                worksheet.write(row_num, 2, row['CONTRATADO_CUSTO'], money_format)
                worksheet.write(row_num, 3, row['EFETIVO_QTD'], integer_format)
                worksheet.write(row_num, 4, row['EFETIVO_CUSTO'], money_format)
                worksheet.write(row_num, 5, row['COMISSIONADO_QTD'], integer_format)
                worksheet.write(row_num, 6, row['COMISSIONADO_CUSTO'], money_format)
                worksheet.write(row_num, 7, row['TOTAL_QTD'], integer_format)
                worksheet.write(row_num, 8, row['TOTAL_CUSTO'], money_format)
        
        # Bordas
        border_format = workbook.add_format({'border': 1})
        ultima_linha = 3 + len(df) - 1
        worksheet.conditional_format(1, 0, ultima_linha, 8, {
            'type': 'no_errors', 'format': border_format
        })
        
        # Larguras
        worksheet.set_column(0, 0, 35)
        for col in range(1, 9):
            worksheet.set_column(col, col, 18 if col % 2 == 0 else 10)
        
        worksheet.freeze_panes(3, 0)
        worksheet.autofilter(1, 0, ultima_linha, 8)