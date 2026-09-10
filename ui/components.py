# ui/components.py - Início do arquivo

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional, Callable, Dict, Any
from config import (
    formatar_numero_abreviado, 
    formatar_numero_completo, 
    formatar_numero
)


class UIComponents:
    """Componentes reutilizáveis da UI"""

    # ==================== HELPERS INTERNOS ====================

    @staticmethod
    def _aplicar_tema_escuro(fig: go.Figure) -> go.Figure:
        """
        Aplica o tema escuro a uma figura Plotly caso o tema ativo seja 'escuro'.

        Args:
            fig: Figura Plotly a ser estilizada.

        Returns:
            A própria figura Plotly com o tema escuro aplicado quando relevante.
        """
        if st.session_state.get('tema', 'claro') == 'escuro':
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e0e0e0'
            )
        return fig

    @staticmethod
    def _aplicar_formatacao_brasileira(fig: go.Figure) -> go.Figure:
        """
        Aplica a formatação numérica brasileira a uma figura Plotly.

        Configura ``separators=',.'`` no layout, fazendo com que o
        Plotly use **vírgula como separador decimal** e **ponto como
        separador de milhar** em todos os valores formatados
        automaticamente (ticks dos eixos, hover labels e rótulos
        automáticos). Exemplo: ``1234.56`` passa a ser exibido como
        ``1.234,56``.

        Importante: para que o separador de milhar seja aplicado, o
        ``tickformat`` do eixo deve incluir a vírgula (ex: ``',.0f'``).
        A vírgula no ``tickformat`` instrui o Plotly a usar separador
        de milhar, e o ``separators`` define QUAL caractere usar
        (neste caso, ponto).

        Args:
            fig: Figura Plotly a ser configurada.

        Returns:
            A própria figura Plotly com a formatação brasileira aplicada.
        """
        fig.update_layout(separators=',.')
        return fig

    @staticmethod
    def kpi_card(
        valor: Any, 
        label: str, 
        icone: str = "", 
        cor: str = "blue",
        change: Optional[Dict] = None,
        abreviar: bool = True
    ) -> None:
        """
        Cria um card de KPI (Key Performance Indicator) com suporte a abreviação
        
        Args:
            valor: Valor do indicador
            label: Descrição do indicador
            icone: Emoji para o ícone
            cor: Cor do card (blue, green, red, orange, purple, teal)
            change: Dicionário com 'value' e 'direction' (up/down)
            abreviar: Se deve abreviar valores numéricos (M, K)
        """
        cores_validas = ['blue', 'green', 'red', 'orange', 'purple', 'teal']
        cor_classe = cor if cor in cores_validas else 'blue'
        
        # Abreviar valor se for numérico e estiver ativado
        valor_exibicao = valor
        if abreviar and isinstance(valor, (int, float)):
            valor_exibicao = formatar_numero_abreviado(valor, "")
        elif isinstance(valor, str) and valor.startswith('R$'):
            # Se já for string com R$, manter
            pass
        
        html = f'<div class="kpi-card kpi-{cor_classe}">'
        
        if icone:
            html += f'<span class="kpi-icon">{icone}</span>'
        
        html += f'<div class="kpi-value">{valor_exibicao}</div>'
        html += f'<div class="kpi-label">{label}</div>'
        
        if change:
            direcao = change.get('direction', 'neutral')
            valor_change = change.get('value', '')
            
            if direcao == 'up':
                classe_change = 'positive'
                simbolo = '▲'
            elif direcao == 'down':
                classe_change = 'negative'
                simbolo = '▼'
            else:
                classe_change = 'neutral'
                simbolo = '•'
            
            html += f'<div class="kpi-change {classe_change}">{simbolo} {valor_change}</div>'
        
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    @staticmethod
    def kpi_grid(metricas: List[Dict]) -> None:
        """Cria um grid de KPIs com suporte a abreviação"""
        html = '<div class="kpi-grid">'
        
        for metrica in metricas:
            cor = metrica.get('cor', 'blue')
            icone = metrica.get('icone', '')
            valor = metrica.get('valor', '—')
            label = metrica.get('label', '')
            change = metrica.get('change', None)
            abreviar = metrica.get('abreviar', True)
            
            cores_validas = ['blue', 'green', 'red', 'orange', 'purple', 'teal']
            cor_classe = cor if cor in cores_validas else 'blue'
            
            # Abreviar valor se for numérico
            valor_exibicao = valor
            if abreviar and isinstance(valor, (int, float)):
                valor_exibicao = formatar_numero_abreviado(valor, "")
            
            html += f'<div class="kpi-card kpi-{cor_classe}">'
            
            if icone:
                html += f'<span class="kpi-icon">{icone}</span>'
            
            html += f'<div class="kpi-value">{valor_exibicao}</div>'
            html += f'<div class="kpi-label">{label}</div>'
            
            if change:
                direcao = change.get('direction', 'neutral')
                valor_change = change.get('value', '')
                
                if direcao == 'up':
                    classe_change = 'positive'
                    simbolo = '▲'
                elif direcao == 'down':
                    classe_change = 'negative'
                    simbolo = '▼'
                else:
                    classe_change = 'neutral'
                    simbolo = '•'
                
                html += f'<div class="kpi-change {classe_change}">{simbolo} {valor_change}</div>'
            
            html += '</div>'
        
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    
    @staticmethod
    def grafico_barras(
        df: pd.DataFrame,
        x: str,
        y: str,
        titulo: str = "",
        cor: str = "#1E88E5",
        orientacao: str = "v",
        mostrar_rotulos: bool = True,
        abreviar_valores: bool = True
    ) -> None:
        """
        Cria gráfico de barras com Plotly e rótulos de dados com abreviação
        
        Args:
            df: DataFrame com os dados
            x: Nome da coluna para o eixo X
            y: Nome da coluna para o eixo Y
            titulo: Título do gráfico
            cor: Cor das barras
            orientacao: 'v' para vertical, 'h' para horizontal
            mostrar_rotulos: Se deve mostrar os rótulos de dados
            abreviar_valores: Se deve abreviar valores (M, K)
        """
        if df.empty:
            st.warning("Sem dados para exibir o gráfico")
            return
        
        df_exibicao = df.copy()
        
        # Criar coluna com valores abreviados para exibição
        if abreviar_valores:
            df_exibicao['valor_abreviado'] = df_exibicao[y].apply(
                lambda v: formatar_numero_abreviado(v, "") if isinstance(v, (int, float)) else str(v)
            )
        else:
            df_exibicao['valor_abreviado'] = df_exibicao[y].apply(
                lambda v: formatar_numero_completo(v, "") if isinstance(v, (int, float)) else str(v)
            )
        
        # NOTA: text_auto removido para evitar conflito com text='valor_abreviado'.
        # Quando ambos são especificados, o text_auto pode sobrescrever o text,
        # fazendo os rótulos personalizados não aparecerem.
        fig = px.bar(
            df_exibicao,
            x=x if orientacao == 'v' else y,
            y=y if orientacao == 'v' else x,
            title=titulo,
            color_discrete_sequence=[cor],
            orientation=orientacao,
            text='valor_abreviado'
        )
        
        if mostrar_rotulos:
            fig.update_traces(
                textposition='outside',
                textfont_size=10
            )
        
        fig.update_layout(
            template='plotly_white',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title_font_size=14,
            xaxis_title=None,
            yaxis_title=None,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        
        # Formatação brasileira (ponto para milhar, vírgula para decimal)
        UIComponents._aplicar_formatacao_brasileira(fig)
        # Tema escuro se necessário
        UIComponents._aplicar_tema_escuro(fig)
        st.plotly_chart(fig, use_container_width=True)
    
# ui/components.py - Método grafico_barras_horizontais_full corrigido

    @staticmethod
    def grafico_barras_horizontais_full(
        df: pd.DataFrame,
        x: str,
        y: str,
        titulo: str = "",
        cor: str = "#1E88E5",
        mostrar_rotulos: bool = True,
        altura: int = 500,
        margem_esquerda: int = 200,
        margem_direita: int = 150,
        abreviar_valores: bool = True
    ) -> None:
        """
        Cria gráfico de barras horizontais ocupando a largura total da página
        com formatação brasileira (ponto para milhar, vírgula para decimal)
        """
        if df.empty:
            st.warning("Sem dados para exibir o gráfico")
            return
        
        # Criar cópia com nomes truncados
        df_exibicao = df.copy()
        df_exibicao['nome_exibicao'] = df_exibicao[x].apply(
            lambda nome: str(nome)[:50] + '...' if len(str(nome)) > 50 else str(nome)
        )
        
        # Criar coluna com valores formatados para exibição
        if abreviar_valores:
            df_exibicao['valor_formatado'] = df_exibicao[y].apply(
                lambda v: formatar_numero_abreviado(v, "") if isinstance(v, (int, float)) else str(v)
            )
        else:
            df_exibicao['valor_formatado'] = df_exibicao[y].apply(
                lambda v: formatar_numero_completo(v, "") if isinstance(v, (int, float)) else str(v)
            )
        
        # Criar o gráfico.
        # NOTA: text_auto removido para evitar conflito com text='valor_formatado'.
        # Quando ambos são especificados, o text_auto sobrescreve o text,
        # fazendo os rótulos personalizados (K/M) não aparecerem.
        fig = px.bar(
            df_exibicao,
            x=y,
            y='nome_exibicao',
            title=titulo,
            color_discrete_sequence=[cor],
            orientation='h',
            text='valor_formatado',
            hover_data={x: True}
        )
        
        # Configurar texto dos rótulos
        if mostrar_rotulos:
            fig.update_traces(
                textposition='outside',
                textfont_size=11
            )
        
        # Ajustar layout
        # NOTA: tickformat=',.0f' (COM vírgula) — a vírgula instrui o
        # Plotly a usar separador de milhar. Combinado com
        # separators=',.' (aplicado por _aplicar_formatacao_brasileira),
        # o Plotly usa PONTO como milhar: R$ 1.234.567.
        # NÃO usar '.0f' (sem vírgula) — isso desativa o separador de
        # milhar completamente, produzindo R$ 1234567.
        fig.update_layout(
            template='plotly_white',
            height=altura,
            margin=dict(l=margem_esquerda, r=margem_direita, t=50, b=30),
            title_font_size=16,
            title_x=0.5,
            xaxis_title=None,
            yaxis_title=None,
            uniformtext_minsize=9,
            uniformtext_mode='hide',
            yaxis=dict(
                tickfont=dict(size=12),
                automargin=True
            ),
            xaxis=dict(
                tickformat=',.0f',
                automargin=True,
                tickprefix='R$ '
            )
        )
        
        # Formatação brasileira (ponto para milhar, vírgula para decimal)
        # Aplicado DEPOIS do update_layout para garantir que separators
        # não seja sobrescrito. Com tickformat=',.0f' + separators=',.',
        # o Plotly mostra R$ 1.234.567 (ponto como milhar).
        UIComponents._aplicar_formatacao_brasileira(fig)
        # Tema escuro se necessário
        UIComponents._aplicar_tema_escuro(fig)
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def grafico_barras_horizontais(
        df: pd.DataFrame,
        x: str,
        y: str,
        titulo: str = "",
        cor: str = "#1E88E5",
        mostrar_rotulos: bool = True,
        altura: int = 500,
        margem_esquerda: int = 200,
        margem_direita: int = 150,
        abreviar_valores: bool = True
    ) -> None:
        """
        Alias para :meth:`grafico_barras_horizontais_full`.
        
        Mantido por compatibilidade com chamadas existentes em
        ``pages.py`` que usam o nome sem o sufixo ``_full``. A
        implementação é idêntica — ambos produzem o mesmo gráfico de
        barras horizontais com formatação brasileira e rótulos
        abreviados (K/M).
        
        Args:
            df: DataFrame com os dados.
            x: Nome da coluna para os rótulos do eixo Y (categorias).
            y: Nome da coluna para o eixo X (valores numéricos).
            titulo: Título do gráfico.
            cor: Cor das barras (hex).
            mostrar_rotulos: Se deve mostrar os rótulos de dados ao
                lado de cada barra.
            altura: Altura do gráfico em pixels.
            margem_esquerda: Margem esquerda em pixels.
            margem_direita: Margem direita em pixels.
            abreviar_valores: Se deve abreviar valores (K, M) nos
                rótulos das barras.
        """
        UIComponents.grafico_barras_horizontais_full(
            df=df,
            x=x,
            y=y,
            titulo=titulo,
            cor=cor,
            mostrar_rotulos=mostrar_rotulos,
            altura=altura,
            margem_esquerda=margem_esquerda,
            margem_direita=margem_direita,
            abreviar_valores=abreviar_valores
        )

    
    @staticmethod
    def grafico_pizza(
        df: pd.DataFrame,
        names: str,
        values: str,
        titulo: str = "",
        colors: Optional[List[str]] = None,
        mostrar_rotulos: bool = True
    ) -> None:
        """
        Cria gráfico de pizza com Plotly e rótulos de dados
        """
        if df.empty:
            st.warning("Sem dados para exibir o gráfico")
            return
        
        if colors is None:
            colors = px.colors.qualitative.Set3
        
        fig = px.pie(
            df,
            names=names,
            values=values,
            title=titulo,
            color_discrete_sequence=colors,
            hole=0.0
        )
        
        if mostrar_rotulos:
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=11,
                insidetextorientation='radial'
            )
        else:
            fig.update_traces(
                textposition='inside',
                textinfo='percent'
            )
        
        fig.update_layout(
            template='plotly_white',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title_font_size=14,
            showlegend=True
        )
        
        # Formatação brasileira (ponto para milhar, vírgula para decimal)
        UIComponents._aplicar_formatacao_brasileira(fig)
        # Tema escuro se necessário
        UIComponents._aplicar_tema_escuro(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def grafico_donut(
        df: pd.DataFrame,
        names: str,
        values: str,
        titulo: str = "",
        colors: Optional[List[str]] = None,
        mostrar_rotulos: bool = True
    ) -> None:
        """
        Cria gráfico donut (pizza com furo) com Plotly e rótulos de dados
        """
        if df.empty:
            st.warning("Sem dados para exibir o gráfico")
            return
        
        if colors is None:
            colors = px.colors.qualitative.Set3
        
        fig = px.pie(
            df,
            names=names,
            values=values,
            title=titulo,
            color_discrete_sequence=colors,
            hole=0.4
        )
        
        if mostrar_rotulos:
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=11,
                insidetextorientation='radial'
            )
        else:
            fig.update_traces(
                textposition='inside',
                textinfo='percent'
            )
        
        fig.update_layout(
            template='plotly_white',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title_font_size=14
        )
        
        # Formatação brasileira (ponto para milhar, vírgula para decimal)
        UIComponents._aplicar_formatacao_brasileira(fig)
        # Tema escuro se necessário
        UIComponents._aplicar_tema_escuro(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def grafico_linhas(
        df: pd.DataFrame,
        x: str,
        y: List[str],
        titulo: str = "",
        cores: Optional[List[str]] = None,
        mostrar_rotulos: bool = True,
        abreviar_valores: bool = True
    ) -> None:
        """
        Cria gráfico de linhas com Plotly e rótulos de dados com abreviação
        """
        if df.empty:
            st.warning("Sem dados para exibir o gráfico")
            return
        
        if cores is None:
            cores = px.colors.qualitative.Set2
        
        fig = px.line(
            df,
            x=x,
            y=y,
            title=titulo,
            color_discrete_sequence=cores,
            markers=mostrar_rotulos
        )
        
        if mostrar_rotulos:
            fig.update_traces(
                texttemplate='%{y:,.2f}',
                textposition='top center',
                textfont_size=10
            )
        
        fig.update_layout(
            template='plotly_white',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title_font_size=14,
            xaxis_title=None,
            yaxis_title=None,
            legend_title=None
        )
        
        # Formatação brasileira (ponto para milhar, vírgula para decimal)
        UIComponents._aplicar_formatacao_brasileira(fig)
        # Tema escuro se necessário
        UIComponents._aplicar_tema_escuro(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def info_box(mensagem: str, tipo: str = "info") -> None:
        """Cria uma caixa de informação"""
        tipos = {
            "info": "info-box",
            "success": "success-box",
            "warning": "warning-box"
        }
        classe = tipos.get(tipo, "info-box")
        st.markdown(f'<div class="{classe}">{mensagem}</div>', unsafe_allow_html=True)
    
    @staticmethod
    def header(titulo: str, subtitulo: str = "", icone: str = "📊") -> None:
        """Cria cabeçalho da página melhorado"""
        st.markdown(f"""
        <div class="main-header">
            {icone} {titulo}
            {f'<small>{subtitulo}</small>' if subtitulo else ''}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def file_upload_section(
        titulo: str, 
        key: str,
        tipos: List[str] = ['csv', 'xlsx', 'xls'],
        icone: str = "📄"
    ) -> Optional[st.runtime.uploaded_file_manager.UploadedFile]:
        """Cria seção de upload de arquivo"""
        st.markdown(f"""
        <div class="upload-section">
            <span class="upload-icon">{icone}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"#### {titulo}")
        
        uploaded_file = st.file_uploader(
            f"Selecione o arquivo",
            type=tipos,
            key=key,
            help="Arraste o arquivo ou clique para selecionar"
        )
        
        if uploaded_file:
            st.success(f"✅ {uploaded_file.name} carregado com sucesso!")
        
        return uploaded_file
    
    @staticmethod
    def column_selector(
        colunas_disponiveis: List[str],
        colunas_selecionadas: List[str],
        colunas_por_linha: int = 3
    ) -> List[str]:
        """Cria seletor de colunas com checkboxes melhorado"""
        st.markdown('<div class="column-selector">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown("**📋 Selecione as colunas:**")
        with col3:
            if st.button("🔄 Limpar tudo", use_container_width=True):
                return []
        
        st.markdown('<div class="col-group">', unsafe_allow_html=True)
        
        selecionadas = colunas_selecionadas.copy() if colunas_selecionadas else []
        
        for idx, col in enumerate(colunas_disponiveis):
            col_idx = idx % colunas_por_linha
            if col_idx == 0:
                cols = st.columns(colunas_por_linha)
            
            with cols[col_idx]:
                checked = st.checkbox(
                    col, 
                    value=col in selecionadas, 
                    key=f"col_selector_{idx}"
                )
                if checked and col not in selecionadas:
                    selecionadas.append(col)
                elif not checked and col in selecionadas:
                    selecionadas.remove(col)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f"**{len(selecionadas)} colunas selecionadas**")
        st.markdown('</div>', unsafe_allow_html=True)
        
        return selecionadas
    
    @staticmethod
    def column_reorder(selecionadas: List[str]) -> List[str]:
        """Cria interface para reordenar colunas"""
        if not selecionadas:
            return selecionadas
        
        st.markdown("### 🔄 Ordem das Colunas")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown("**Use os botões para reordenar:**")
        with col2:
            if st.button("⬆️ Mover para cima", use_container_width=True):
                if len(selecionadas) > 1:
                    selecionadas.append(selecionadas.pop(0))
                    st.rerun()
        with col3:
            if st.button("⬇️ Mover para baixo", use_container_width=True):
                if len(selecionadas) > 1:
                    selecionadas.insert(0, selecionadas.pop())
                    st.rerun()
        with col4:
            if st.button("🔤 A-Z", use_container_width=True):
                selecionadas.sort()
                st.rerun()
        
        st.markdown("---")
        
        for i, col in enumerate(selecionadas):
            col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{i+1}. {col}**")
            
            with col2:
                if i > 0:
                    if st.button("⬆️", key=f"reorder_up_{i}"):
                        selecionadas[i], selecionadas[i-1] = selecionadas[i-1], selecionadas[i]
                        st.rerun()
            
            with col3:
                if i < len(selecionadas) - 1:
                    if st.button("⬇️", key=f"reorder_down_{i}"):
                        selecionadas[i], selecionadas[i+1] = selecionadas[i+1], selecionadas[i]
                        st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"reorder_remove_{i}"):
                    selecionadas.remove(col)
                    st.rerun()
        
        return selecionadas
    
    @staticmethod
    def filter_section(df: pd.DataFrame) -> pd.DataFrame:
        """Cria seção de filtros"""
        st.markdown("""
        <div class="filter-section">
            <div class="filter-title">🔍 Filtros</div>
        """, unsafe_allow_html=True)
        
        df_filtrado = df.copy()
        filtros_aplicados = {}
        
        colunas_filtro = {
            'SUPERINTENDENCIA': ('🏛️', 'SUPERINTENDÊNCIA'),
            'LOCAL': ('📍', 'LOCAL'),
            'SETOR_MUNICIPIO': ('🏙️', 'SETOR/MUNICÍPIO'),
            'FAIXA ETARIA': ('👤', 'FAIXA ETÁRIA'),
            'SERVIDOR IDOSO': ('👴', 'SERVIDOR IDOSO'),
            'FAIXA SALARIAL': ('💰', 'FAIXA SALARIAL'),
            'SITUACAO SALARIAL': ('📊', 'SITUAÇÃO SALARIAL'),
            'PORTE': ('📏', 'PORTE'),
            'SETOR_AREA': ('📂', 'SETOR/ÁREA'),
            'SEXO': ('🚻', 'SEXO'),
            'CARGO': ('💼', 'CARGO')
        }
        
        colunas_disponiveis = [col for col in colunas_filtro.keys() if col in df.columns]
        
        if colunas_disponiveis:
            linhas = (len(colunas_disponiveis) + 2) // 3
            
            for linha in range(linhas):
                cols = st.columns(3)
                for i in range(3):
                    idx = linha * 3 + i
                    if idx < len(colunas_disponiveis):
                        col_name = colunas_disponiveis[idx]
                        with cols[i]:
                            valores = sorted(df[col_name].dropna().unique())
                            if len(valores) > 0:
                                icone, label = colunas_filtro[col_name]
                                opcao = st.selectbox(
                                    f"{icone} {label}",
                                    options=['📋 TODOS'] + list(valores),
                                    key=f"filtro_{col_name}"
                                )
                                if opcao != '📋 TODOS':
                                    df_filtrado = df_filtrado[df_filtrado[col_name] == opcao]
                                    filtros_aplicados[col_name] = opcao
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if filtros_aplicados:
            badges = " ".join([
                f'<span class="badge badge-blue">{k}: {v}</span>' 
                for k, v in filtros_aplicados.items()
            ])
            st.markdown(f"**Filtros aplicados:** {badges}", unsafe_allow_html=True)
        
        total = len(df)
        atual = len(df_filtrado)
        percentual = (atual / total * 100) if total > 0 else 0
        
        st.markdown(f"""
        <div style="margin-top: 0.5rem;">
            <span style="font-size: 0.9rem; color: #6c757d;">
                <strong>{atual:,}</strong> de <strong>{total:,}</strong> registros 
                <span style="color: #1E88E5;">({percentual:.1f}%)</span>
            </span>
            <div class="progress-container">
                <div class="progress-bar" style="width: {percentual:.1f}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        return df_filtrado
    
    @staticmethod
    def status_badge(texto: str, tipo: str = "info") -> str:
        """Cria um badge de status"""
        tipos = {
            "info": "badge-blue",
            "success": "badge-green",
            "danger": "badge-red",
            "warning": "badge-yellow"
        }
        classe = tipos.get(tipo, "badge-blue")
        return f'<span class="badge {classe}">{texto}</span>'
    
    @staticmethod
    def section_title(titulo: str, icone: str = "", nivel: int = 2) -> None:
        """Cria um título de seção estilizado"""
        st.markdown(f"---")
        if nivel == 2:
            st.markdown(f"## {icone} {titulo}")
        elif nivel == 3:
            st.markdown(f"### {icone} {titulo}")
        else:
            st.markdown(f"#### {icone} {titulo}")