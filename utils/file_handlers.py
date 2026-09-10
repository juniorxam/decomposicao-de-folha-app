# utils/file_handlers.py
"""
Manipulação de arquivos: leitura, escrita e validação
"""

import os
import io
from typing import Any, List

import pandas as pd

from config import EXTENSOES_SUPORTADAS


class FileHandler:
    """Classe para manipulação de arquivos"""
    
    # Encodings tentados (em ordem) na leitura de CSV.
    _ENCONDINGS_CSV: List[str] = ['utf-8', 'latin-1', 'iso-8859-1']
    
    # Delimitadores tentados (em ordem) na leitura de CSV.
    _DELIMITADORES_CSV: List[str] = [';', ',']
    
    # Largura máxima aplicada às colunas ao salvar Excel.
    _LARGURA_MAXIMA_COLUNA: int = 50
    
    @staticmethod
    def ler_arquivo(uploaded_file: Any) -> pd.DataFrame:
        """
        Lê arquivo enviado pelo Streamlit diretamente do objeto
        ``UploadedFile``.
        
        Identifica a extensão do arquivo a partir do atributo ``.name``
        e delega para o leitor apropriado:
        
        - ``.csv``  → :meth:`_ler_csv` (fallback de encodings e
          delimitadores).
        - ``.xlsx`` → ``pd.read_excel`` com engine ``openpyxl``.
        - ``.xls``  → ``pd.read_excel`` com engine ``xlrd``.
        
        Args:
            uploaded_file: Objeto ``UploadedFile`` do Streamlit (ou
                qualquer objeto com atributo ``.name`` e bytes
                legíveis pelo pandas).
        
        Returns:
            DataFrame com os dados do arquivo.
        
        Raises:
            ValueError: Se a extensão não for suportada ou se ocorrer
                qualquer erro durante a leitura (a mensagem inclui o
                nome do arquivo e o erro original).
        """
        try:
            filename = uploaded_file.name
            extensao = os.path.splitext(filename)[1].lower()
            
            if extensao not in EXTENSOES_SUPORTADAS:
                raise ValueError(
                    f"Formato de arquivo não suportado: {extensao}. "
                    f"Use: {', '.join(EXTENSOES_SUPORTADAS)}"
                )
            
            if extensao == '.csv':
                return FileHandler._ler_csv(uploaded_file)
            elif extensao == '.xlsx':
                return pd.read_excel(uploaded_file, engine='openpyxl')
            elif extensao == '.xls':
                return pd.read_excel(uploaded_file, engine='xlrd')
        except Exception as e:
            raise ValueError(f"Erro ao ler o arquivo {filename}: {str(e)}")
    
    @staticmethod
    def _ler_csv(uploaded_file: Any) -> pd.DataFrame:
        """
        Tenta ler arquivo CSV com diferentes encodings e delimitadores.
        
        Estratégia de fallback: percorre todas as combinações de
        ``_ENCONDINGS_CSV`` × ``_DELIMITADORES_CSV`` (até 6 tentativas)
        até encontrar uma combinação que consiga ler o arquivo sem
        erros. A cada tentativa, reposiciona o ponteiro do arquivo
        para o início (``seek(0)``) antes de chamar ``pd.read_csv``.
        
        Args:
            uploaded_file: Objeto ``UploadedFile`` do Streamlit (ou
                objeto compatível com ``seek`` e leitura pelo pandas).
        
        Returns:
            DataFrame com os dados do CSV.
        
        Raises:
            ValueError: Se nenhuma combinação de encoding e
                delimitador conseguir ler o arquivo.
        """
        for encoding in FileHandler._ENCONDINGS_CSV:
            for delimiter in FileHandler._DELIMITADORES_CSV:
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(
                        uploaded_file, 
                        encoding=encoding, 
                        delimiter=delimiter
                    )
                except Exception:
                    continue
        
        raise ValueError("Não foi possível ler o arquivo CSV com os formatos testados")
    
    @staticmethod
    def salvar_excel(df: pd.DataFrame, nome_planilha: str = "Dados") -> bytes:
        """
        Salva DataFrame em Excel com formatação básica.
        
        Escreve o DataFrame em uma única aba (``nome_planilha``) sem
        índice e ajusta automaticamente a largura de cada coluna para
        o maior valor entre o cabeçalho e o conteúdo (limitado a
        :attr:`_LARGURA_MAXIMA_COLUNA` caracteres).
        
        Args:
            df: DataFrame a ser salvo.
            nome_planilha: Nome da aba (sheet) no arquivo Excel.
        
        Returns:
            Bytes do arquivo ``.xlsx`` pronto para download.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=nome_planilha, index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets[nome_planilha]
            for i, col in enumerate(df.columns):
                largura = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, min(largura, FileHandler._LARGURA_MAXIMA_COLUNA))
        
        return output.getvalue()