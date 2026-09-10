# ui/pages.py - Início do arquivo

import streamlit as st
import datetime
import pandas as pd
from typing import Optional

from services.ergon_service import ErgonService
from services.report_service import ReportService
from utils.file_handlers import FileHandler
from utils.validators import DataValidator
from utils.formatters import ExcelFormatter
from config import (
    SALARIO_MINIMO, 
    TETO_ESTADUAL,
    formatar_numero_abreviado,
    formatar_numero_completo,
    formatar_numero
)

from .components import UIComponents
from .styles import aplicar_estilos, toggle_tema


class MainPage:
    """Página principal da aplicação"""
    
    def __init__(self):
        self.ergon_service = ErgonService()
        self.report_service = ReportService()
        self.ui = UIComponents()
        self.validator = DataValidator()
        self.formatter = ExcelFormatter()
        self.file_handler = FileHandler()
        
        # Inicializar session_state
        self._init_session_state()

    @staticmethod
    def _contagem_ordenada(serie: pd.Series, ordem: list) -> pd.DataFrame:
        """Retorna contagens na ordem informada, não na ordem de frequência."""
        contagens = serie.value_counts().rename_axis('categoria').reset_index(name='Quantidade')
        if contagens.empty:
            return contagens.rename(columns={'categoria': 'Categoria'})

        presentes = set(contagens['categoria'])
        ordem_final = [categoria for categoria in ordem if categoria in presentes]
        extras = sorted(presentes.difference(ordem_final), key=lambda valor: str(valor))
        ordem_final.extend(extras)

        contagens['categoria'] = pd.Categorical(
            contagens['categoria'], categories=ordem_final, ordered=True
        )
        return contagens.sort_values('categoria').rename(
            columns={'categoria': 'Categoria'}
        ).reset_index(drop=True)
    
    def _init_session_state(self):
        """Inicializa variáveis de sessão"""
        defaults = {
            'df_completo': None,
            'df_filtrado': None,
            'df_resultado': None,
            'df_relatorio_hospitais': None,
            'df_relatorio_superintendencias': None,
            'df_relatorio_hospitais_resumido': None,
            'df_relatorio_superintendencias_resumido': None,
            'colunas_selecionadas': [],
            'info': None,
            'processado': False,
            'active_tab': "📊 Dashboard",
            'tema': 'claro',
            'dashboard_filtro_local': 'TODOS',
            'dashboard_filtro_vinculo': 'TODOS',
            'dashboard_filtro_situacao': 'TODAS',
            'dashboard_filtro_sexo': 'TODOS',
            'dashboard_filtro_cargo': 'TODOS'
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def render(self):
        """Renderiza a página principal"""
        aplicar_estilos()
        
        # Cabeçalho
        self.ui.header(
            "Sistema de Tratamento de Dados",
            "Consolide, filtre e gere relatórios a partir dos dados do Ergon",
            "📊"
        )
        
        # Sidebar
        self._render_sidebar()
        
        # Conteúdo principal
        self._render_main_content()
        
        # Rodapé
        self._render_footer()
    
    def _render_sidebar(self):
        """Renderiza a barra lateral"""
        with st.sidebar:
            st.markdown("## 📋 Painel de Controle")
            
            # Alternar Tema
            st.markdown("### 🎨 Aparência")
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.session_state.get('tema', 'claro') == 'claro':
                    st.markdown("☀️")
                else:
                    st.markdown("🌙")
            with col2:
                if st.button(
                    "Alternar Tema",
                    use_container_width=True,
                    key="toggle_tema"
                ):
                    toggle_tema()
            
            st.markdown("---")
            
            # Status
            st.markdown("""
            <div class="sidebar-info">
                <h4>🚀 Status</h4>
            """, unsafe_allow_html=True)
            
            if st.session_state.processado:
                st.markdown(f"""
                <div class="stat-item">
                    <span class="stat-label">Status</span>
                    <span class="stat-value"><span class="status-dot green"></span>Processado</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="stat-item">
                    <span class="stat-label">Status</span>
                    <span class="stat-value"><span class="status-dot yellow"></span>Aguardando</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Limites
            st.markdown("""
            <div class="sidebar-info">
                <h4>💰 Limites</h4>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="stat-item">
                <span class="stat-label">Salário Mínimo</span>
                <span class="stat-value">R$ {SALARIO_MINIMO:,.2f}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Teto Estadual</span>
                <span class="stat-value">R$ {TETO_ESTADUAL:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Estatísticas
            if st.session_state.df_completo is not None:
                df = st.session_state.df_completo
                st.markdown("""
                <div class="sidebar-info">
                    <h4>📊 Estatísticas</h4>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="stat-item">
                    <span class="stat-label">Total Registros</span>
                    <span class="stat-value">{len(df):,}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if 'SERVIDOR IDOSO' in df.columns:
                    idosos = len(df[df['SERVIDOR IDOSO'] == 'SIM'])
                    st.markdown(f"""
                    <div class="stat-item">
                        <span class="stat-label">👴 Servidores Idosos</span>
                        <span class="stat-value">{idosos:,}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                if 'SITUACAO SALARIAL' in df.columns:
                    abaixo = len(df[df['SITUACAO SALARIAL'] == 'ABAIXO DO MINIMO'])
                    acima = len(df[df['SITUACAO SALARIAL'] == 'ACIMA DO TETO'])
                    st.markdown(f"""
                    <div class="stat-item">
                        <span class="stat-label">⬇️ Abaixo do Mínimo</span>
                        <span class="stat-value" style="color: #dc3545;">{abaixo:,}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">⬆️ Acima do Teto</span>
                        <span class="stat-value" style="color: #ffc107;">{acima:,}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Ações Rápidas
            st.markdown("### ⚡ Ações Rápidas")
            if st.session_state.processado:
                if st.button("🔄 Resetar Dados", use_container_width=True):
                    for key in ['df_completo', 'df_filtrado', 'df_resultado', 'processado']:
                        if key in st.session_state:
                            st.session_state[key] = None
                    st.rerun()
    
    def _render_main_content(self):
        """Renderiza o conteúdo principal com abas"""
        
        if not st.session_state.processado:
            self._render_upload_section()
            return
        
        # Abas reorganizadas
        tabs = st.tabs([
            "📊 Dashboard",
            "👥 Análise Pessoal",
            "💰 Análise Financeira",
            "🏥 Hospitais",
            "🏛️ Superintendências",
            "🔍 Filtros & Colunas",
            "📥 Exportar"
        ])
        
        with tabs[0]:
            self._render_dashboard_tab()
        
        with tabs[1]:
            self._render_analise_pessoal_tab()
        
        with tabs[2]:
            self._render_analise_financeira_tab()
        
        with tabs[3]:
            self._render_hospital_tab()
        
        with tabs[4]:
            self._render_superintendencia_tab()
        
        with tabs[5]:
            self._render_filters_tab()
        
        with tabs[6]:
            self._render_export_tab()
    
    # ==================== FILTROS DO DASHBOARD (REUTILIZÁVEL) ====================
    
    def _render_filtros_dashboard(
        self,
        df: pd.DataFrame,
        expanded: bool = False,
        sufixo_key: str = ""
    ) -> pd.DataFrame:
        """
        Renderiza o expander de filtros do dashboard e retorna o DataFrame filtrado.
        
        Os filtros compartilham o mesmo ``session_state`` entre todas as abas,
        de modo que mudar um filtro em uma aba reflete automaticamente nas
        outras. O parâmetro ``sufixo_key`` diferencia as ``key`` dos widgets
        entre abas (exigência do Streamlit: cada widget precisa de uma key
        única), mas o estado é persistido nos mesmos campos de
        ``session_state`` (``dashboard_filtro_local``, etc.).
        
        Args:
            df: DataFrame completo a ser filtrado.
            expanded: Se o expander deve iniciar expandido.
            sufixo_key: Sufixo único por aba para evitar colisão de
                ``key`` entre widgets (ex: ``"_pessoal"``, ``"_hosp"``).
        
        Returns:
            DataFrame filtrado pelos critérios selecionados.
        """
        with st.expander("🔍 Filtros do Dashboard", expanded=expanded):
            # Linha 1: 4 filtros
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'LOCAL' in df.columns:
                    locais = ['TODOS'] + sorted(df['LOCAL'].dropna().unique().tolist())
                    # index inicial alinhado ao session_state (sincroniza entre abas)
                    try:
                        idx_local = locais.index(st.session_state.get('dashboard_filtro_local', 'TODOS'))
                    except ValueError:
                        idx_local = 0
                    st.session_state.dashboard_filtro_local = st.selectbox(
                        "📍 Local",
                        options=locais,
                        index=idx_local,
                        key=f"dash_filtro_local{sufixo_key}"
                    )
                else:
                    st.session_state.dashboard_filtro_local = 'TODOS'
            
            with col2:
                if 'VINCULO' in df.columns:
                    vinculos = ['TODOS'] + sorted(df['VINCULO'].dropna().unique().tolist())
                    try:
                        idx_vinc = vinculos.index(st.session_state.get('dashboard_filtro_vinculo', 'TODOS'))
                    except ValueError:
                        idx_vinc = 0
                    st.session_state.dashboard_filtro_vinculo = st.selectbox(
                        "👤 Vínculo",
                        options=vinculos,
                        index=idx_vinc,
                        key=f"dash_filtro_vinculo{sufixo_key}"
                    )
                else:
                    st.session_state.dashboard_filtro_vinculo = 'TODOS'
            
            with col3:
                if 'SITUACAO SALARIAL' in df.columns:
                    situacoes = ['TODAS'] + sorted(df['SITUACAO SALARIAL'].dropna().unique().tolist())
                    try:
                        idx_sit = situacoes.index(st.session_state.get('dashboard_filtro_situacao', 'TODAS'))
                    except ValueError:
                        idx_sit = 0
                    st.session_state.dashboard_filtro_situacao = st.selectbox(
                        "📊 Situação Salarial",
                        options=situacoes,
                        index=idx_sit,
                        key=f"dash_filtro_situacao{sufixo_key}"
                    )
                else:
                    st.session_state.dashboard_filtro_situacao = 'TODAS'
            
            with col4:
                if 'SEXO' in df.columns:
                    sexos = ['TODOS'] + sorted(df['SEXO'].dropna().unique().tolist())
                    try:
                        idx_sexo = sexos.index(st.session_state.get('dashboard_filtro_sexo', 'TODOS'))
                    except ValueError:
                        idx_sexo = 0
                    st.session_state.dashboard_filtro_sexo = st.selectbox(
                        "🚻 Sexo",
                        options=sexos,
                        index=idx_sexo,
                        key=f"dash_filtro_sexo{sufixo_key}"
                    )
                else:
                    st.session_state.dashboard_filtro_sexo = 'TODOS'
            
            # Linha 2: Filtro de Cargo (ocupando toda a largura)
            if 'CARGO' in df.columns:
                st.markdown("---")
                cargos = ['TODOS'] + sorted(df['CARGO'].dropna().unique().tolist())
                try:
                    idx_cargo = cargos.index(st.session_state.get('dashboard_filtro_cargo', 'TODOS'))
                except ValueError:
                    idx_cargo = 0
                st.session_state.dashboard_filtro_cargo = st.selectbox(
                    "💼 Cargo",
                    options=cargos,
                    index=idx_cargo,
                    key=f"dash_filtro_cargo{sufixo_key}",
                    help="Selecione um cargo específico ou TODOS"
                )
            else:
                st.session_state.dashboard_filtro_cargo = 'TODOS'
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if st.session_state.get('dashboard_filtro_local', 'TODOS') != 'TODOS':
            df_filtrado = df_filtrado[df_filtrado['LOCAL'] == st.session_state.dashboard_filtro_local]
        
        if st.session_state.get('dashboard_filtro_vinculo', 'TODOS') != 'TODOS':
            df_filtrado = df_filtrado[df_filtrado['VINCULO'] == st.session_state.dashboard_filtro_vinculo]
        
        if st.session_state.get('dashboard_filtro_situacao', 'TODAS') != 'TODAS':
            df_filtrado = df_filtrado[df_filtrado['SITUACAO SALARIAL'] == st.session_state.dashboard_filtro_situacao]
        
        if st.session_state.get('dashboard_filtro_sexo', 'TODOS') != 'TODOS':
            df_filtrado = df_filtrado[df_filtrado['SEXO'] == st.session_state.dashboard_filtro_sexo]
        
        if st.session_state.get('dashboard_filtro_cargo', 'TODOS') != 'TODOS':
            df_filtrado = df_filtrado[df_filtrado['CARGO'] == st.session_state.dashboard_filtro_cargo]
        
        # Mostrar resumo dos filtros aplicados
        filtros_ativos = []
        if st.session_state.get('dashboard_filtro_local', 'TODOS') != 'TODOS':
            filtros_ativos.append(f"Local: {st.session_state.dashboard_filtro_local}")
        if st.session_state.get('dashboard_filtro_vinculo', 'TODOS') != 'TODOS':
            filtros_ativos.append(f"Vínculo: {st.session_state.dashboard_filtro_vinculo}")
        if st.session_state.get('dashboard_filtro_situacao', 'TODAS') != 'TODAS':
            filtros_ativos.append(f"Situação: {st.session_state.dashboard_filtro_situacao}")
        if st.session_state.get('dashboard_filtro_sexo', 'TODOS') != 'TODOS':
            filtros_ativos.append(f"Sexo: {st.session_state.dashboard_filtro_sexo}")
        if st.session_state.get('dashboard_filtro_cargo', 'TODOS') != 'TODOS':
            filtros_ativos.append(f"Cargo: {st.session_state.dashboard_filtro_cargo}")
        
        if filtros_ativos:
            st.caption(f"🔍 Filtros ativos: {', '.join(filtros_ativos)} | Registros: {len(df_filtrado):,}")
        else:
            st.caption(f"📊 Registros: {len(df_filtrado):,}")
        
        return df_filtrado
    
    # ==================== DASHBOARD ====================
    
    def _render_dashboard_tab(self):
        """Renderiza o Dashboard reformulado com filtros de Sexo e Cargo"""
        st.markdown("## 📊 Dashboard Geral")
        
        df = st.session_state.df_completo
        
        # ===== FILTROS DO DASHBOARD =====
        df_filtrado = self._render_filtros_dashboard(df, sufixo_key="_dash")
        
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados.")
            return
        
        # ===== KPIs PRINCIPAIS =====
        self._render_kpis_principais(df_filtrado)
        
        # ===== GRÁFICOS PRINCIPAIS (2 colunas) =====
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_grafico_hospitais_vs_super(df_filtrado)
        
        with col2:
            self._render_grafico_distribuicao_vinculo(df_filtrado)
        
        st.markdown("---")
        
        # ===== TODOS OS HOSPITAIS (LARGURA TOTAL) =====
        self._render_todos_hospitais(df_filtrado)
        
        st.markdown("---")
        
        # ===== TODAS AS SUPERINTENDÊNCIAS (LARGURA TOTAL) =====
        self._render_todas_superintendencias(df_filtrado)
        
        st.markdown("---")
        
        # ===== ANÁLISE TEMPORAL (PREPARADA) =====
        self._render_analise_temporal(df_filtrado)
 
    
    def _render_kpis_principais(self, df):
        """Renderiza os 4 KPIs principais"""
        
        # Calcular métricas
        total_trabalhadores = len(df)
        
        # Custo total (sem encargos)
        if 'VALOR NIVEL/REF - com teto' in df.columns:
            custo_total = df['VALOR NIVEL/REF - com teto'].sum()
        else:
            custo_total = 0
        
        # Hospitais
        if 'LOCAL' in df.columns and 'SETOR_AJUSTADO' in df.columns:
            df_hosp = df[df['LOCAL'] == 'HOSPITAL']
            qtd_hospitais = len(df_hosp['SETOR_AJUSTADO'].unique())
            trabalhadores_hosp = len(df_hosp)
            perc_hosp = (trabalhadores_hosp / total_trabalhadores * 100) if total_trabalhadores > 0 else 0
        else:
            qtd_hospitais = 0
            trabalhadores_hosp = 0
            perc_hosp = 0
        
        # Superintendências
        if 'SUPERINTENDENCIA' in df.columns:
            df_super = df[df['SUPERINTENDENCIA'].notna() & (df['SUPERINTENDENCIA'] != '')]
            qtd_super = len(df_super['SUPERINTENDENCIA'].unique())
            trabalhadores_super = len(df_super)
            perc_super = (trabalhadores_super / total_trabalhadores * 100) if total_trabalhadores > 0 else 0
        else:
            qtd_super = 0
            trabalhadores_super = 0
            perc_super = 0
        
        # Renderizar KPIs
        st.markdown("### 🎯 Indicadores Principais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.ui.kpi_card(
                valor=f"{total_trabalhadores:,}",
                label="Total de Trabalhadores",
                icone="👥",
                cor="blue"
            )
        
        with col2:
            self.ui.kpi_card(
                valor=f"R$ {custo_total:,.2f}",
                label="Custo Total (sem encargos)",
                icone="💰",
                cor="teal"
            )
        
        with col3:
            self.ui.kpi_card(
                valor=f"{qtd_hospitais}",
                label=f"🏥 Hospitais ({trabalhadores_hosp:,} trabalhadores - {perc_hosp:.1f}%)",
                icone="🏥",
                cor="orange"
            )
        
        with col4:
            self.ui.kpi_card(
                valor=f"{qtd_super}",
                label=f"🏛️ Superintendências ({trabalhadores_super:,} trabalhadores - {perc_super:.1f}%)",
                icone="🏛️",
                cor="purple"
            )
    
    def _render_todos_hospitais(self, df):
        """Renderiza todos os Hospitais por Custo com formatação brasileira"""
        st.markdown("### 🏥 Todos os Hospitais por Custo")
        
        if 'LOCAL' in df.columns and 'SETOR_AJUSTADO' in df.columns and 'VALOR NIVEL/REF - com teto' in df.columns:
            df_hosp = df[df['LOCAL'] == 'HOSPITAL'].copy()
            
            if not df_hosp.empty:
                hosp_custo = df_hosp.groupby('SETOR_AJUSTADO')['VALOR NIVEL/REF - com teto'].sum().reset_index()
                hosp_custo.columns = ['Hospital', 'Custo Total']
                hosp_custo = hosp_custo.sort_values('Custo Total', ascending=False)
                
                if not hosp_custo.empty:
                    # Formatar com padrão brasileiro
                    df_exibicao = hosp_custo.copy()
                    df_exibicao['Custo Total'] = df_exibicao['Custo Total'].apply(
                        lambda x: formatar_numero_completo(x, "R$ ")
                    )
                    
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Hospitais", len(df_exibicao))
                    with col2:
                        st.metric("Custo Total", formatar_numero_completo(hosp_custo['Custo Total'].sum(), "R$ "))
                    with col3:
                        st.metric("Média por Hospital", formatar_numero_completo(hosp_custo['Custo Total'].mean(), "R$ "))
                    
                    # Tabela com scroll
                    st.dataframe(
                        df_exibicao, 
                        use_container_width=True, 
                        hide_index=True,
                        height=min(500, max(300, len(df_exibicao) * 35 + 50))
                    )
                    
                    # Gráfico
                    altura = max(400, min(900, len(hosp_custo) * 32))
                    
                    self.ui.grafico_barras_horizontais_full(
                        hosp_custo,
                        x='Hospital',
                        y='Custo Total',
                        titulo='Distribuição de Custos por Hospital',
                        cor='#ff8f00',
                        mostrar_rotulos=True,
                        altura=altura,
                        margem_esquerda=200,
                        margem_direita=150,
                        abreviar_valores=True
                    )
                else:
                    st.info("Nenhum hospital encontrado")
            else:
                st.info("Nenhum hospital encontrado")
        else:
            st.info("Dados de hospitais não disponíveis")

    
    def _render_todas_superintendencias(self, df):
        """Renderiza todas as Superintendências por Custo com formatação brasileira"""
        st.markdown("### 🏛️ Todas as Superintendências por Custo")
        
        if 'SUPERINTENDENCIA' in df.columns and 'VALOR NIVEL/REF - com teto' in df.columns:
            df_super = df[df['SUPERINTENDENCIA'].notna() & (df['SUPERINTENDENCIA'] != '')].copy()
            
            if not df_super.empty:
                super_custo = df_super.groupby('SUPERINTENDENCIA')['VALOR NIVEL/REF - com teto'].sum().reset_index()
                super_custo.columns = ['Superintendência', 'Custo Total']
                super_custo = super_custo.sort_values('Custo Total', ascending=False)
                
                if not super_custo.empty:
                    # Formatar com padrão brasileiro
                    df_exibicao = super_custo.copy()
                    df_exibicao['Custo Total'] = df_exibicao['Custo Total'].apply(
                        lambda x: formatar_numero_completo(x, "R$ ")
                    )
                    
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Superintendências", len(super_custo))
                    with col2:
                        st.metric("Custo Total", formatar_numero_completo(super_custo['Custo Total'].sum(), "R$ "))
                    with col3:
                        st.metric("Média por Superintendência", formatar_numero_completo(super_custo['Custo Total'].mean(), "R$ "))
                    
                    # Tabela com scroll
                    st.dataframe(
                        df_exibicao, 
                        use_container_width=True, 
                        hide_index=True,
                        height=min(500, max(300, len(df_exibicao) * 35 + 50))
                    )
                    
                    # Gráfico
                    altura = max(400, min(900, len(super_custo) * 32))
                    
                    self.ui.grafico_barras_horizontais_full(
                        super_custo,
                        x='Superintendência',
                        y='Custo Total',
                        titulo='Distribuição de Custos por Superintendência',
                        cor='#7b1fa2',
                        mostrar_rotulos=True,
                        altura=altura,
                        margem_esquerda=220,
                        margem_direita=150,
                        abreviar_valores=True
                    )
                else:
                    st.info("Nenhuma superintendência encontrada")
            else:
                st.info("Nenhuma superintendência encontrada")
        else:
            st.info("Dados de superintendências não disponíveis")


    def _render_grafico_hospitais_vs_super(self, df):
        """Renderiza gráfico de Hospitais vs Superintendências com rótulos"""
        st.markdown("#### 🏥 Distribuição: Hospitais vs Superintendências")
        
        # Calcular dados
        if 'LOCAL' in df.columns:
            df_hosp = df[df['LOCAL'] == 'HOSPITAL']
            trabalhadores_hosp = len(df_hosp)
        else:
            trabalhadores_hosp = 0
        
        if 'SUPERINTENDENCIA' in df.columns:
            df_super = df[df['SUPERINTENDENCIA'].notna() & (df['SUPERINTENDENCIA'] != '')]
            trabalhadores_super = len(df_super)
        else:
            trabalhadores_super = 0
        
        outros = len(df) - trabalhadores_hosp - trabalhadores_super
        
        dados = []
        if trabalhadores_hosp > 0:
            dados.append({'Categoria': 'Hospitais', 'Quantidade': trabalhadores_hosp})
        if trabalhadores_super > 0:
            dados.append({'Categoria': 'Superintendências', 'Quantidade': trabalhadores_super})
        if outros > 0:
            dados.append({'Categoria': 'Outros', 'Quantidade': outros})
        
        if dados:
            df_grafico = pd.DataFrame(dados)
            
            cores = ['#ff8f00', '#7b1fa2', '#6c757d']
            
            self.ui.grafico_donut(
                df_grafico,
                names='Categoria',
                values='Quantidade',
                titulo='',
                colors=cores,
                mostrar_rotulos=True
            )
            
            # Mostrar porcentagens
            total = df_grafico['Quantidade'].sum()
            for _, row in df_grafico.iterrows():
                perc = (row['Quantidade'] / total * 100) if total > 0 else 0
                st.caption(f"{row['Categoria']}: {row['Quantidade']:,} ({perc:.1f}%)")
        else:
            st.info("Dados insuficientes para este gráfico")
    
    def _render_grafico_distribuicao_vinculo(self, df):
        """Renderiza gráfico de distribuição por vínculo com rótulos"""
        st.markdown("#### 👤 Distribuição por Vínculo")
        
        if 'VINCULO' in df.columns:
            vinculo_counts = self._contagem_ordenada(
                df['VINCULO'], ['CONTRATADO', 'EFETIVO', 'COMISSIONADO', 'OUTROS']
            ).rename(columns={'Categoria': 'Vínculo'})
            
            if not vinculo_counts.empty:
                cores = ['#1E88E5', '#28a745', '#7b1fa2', '#ff8f00', '#dc3545']
                
                self.ui.grafico_pizza(
                    vinculo_counts,
                    names='Vínculo',
                    values='Quantidade',
                    titulo='',
                    colors=cores[:len(vinculo_counts)],
                    mostrar_rotulos=True
                )
                
                # Mostrar detalhes
                total = vinculo_counts['Quantidade'].sum()
                for _, row in vinculo_counts.iterrows():
                    perc = (row['Quantidade'] / total * 100) if total > 0 else 0
                    st.caption(f"{row['Vínculo']}: {row['Quantidade']:,} ({perc:.1f}%)")
            else:
                st.info("Dados de vínculo não disponíveis")
        else:
            st.info("Coluna 'VINCULO' não encontrada")
    
    def _render_top_hospitais(self, df):
        """Renderiza todos os Hospitais por Custo com visualização otimizada"""
        st.markdown("#### 🏥 Todos os Hospitais por Custo")
        
        if 'LOCAL' in df.columns and 'SETOR_AJUSTADO' in df.columns and 'VALOR NIVEL/REF - com teto' in df.columns:
            df_hosp = df[df['LOCAL'] == 'HOSPITAL'].copy()
            
            if not df_hosp.empty:
                hosp_custo = df_hosp.groupby('SETOR_AJUSTADO')['VALOR NIVEL/REF - com teto'].sum().reset_index()
                hosp_custo.columns = ['Hospital', 'Custo Total']
                hosp_custo = hosp_custo.sort_values('Custo Total', ascending=False)
                
                if not hosp_custo.empty:
                    # Formatar para exibição em tabela
                    df_exibicao = hosp_custo.copy()
                    df_exibicao['Custo Total'] = df_exibicao['Custo Total'].apply(
                        lambda x: f'R$ {x:,.2f}'
                    )
                    
                    # Mostrar quantidade total de hospitais
                    st.caption(f"📊 Total de hospitais: **{len(df_exibicao)}**")
                    
                    # Exibir tabela com scroll
                    st.dataframe(
                        df_exibicao, 
                        use_container_width=True, 
                        hide_index=True,
                        height=min(400, max(200, len(df_exibicao) * 35 + 50))
                    )
                    
                    # Gráfico com todos os hospitais
                    # Altura baseada na quantidade de hospitais
                    altura = max(300, min(800, len(hosp_custo) * 30))
                    
                    self.ui.grafico_barras_horizontais(
                        hosp_custo,
                        x='Hospital',
                        y='Custo Total',
                        titulo='',
                        cor='#ff8f00',
                        mostrar_rotulos=True,
                        altura=altura,
                        margem_esquerda=180,
                        margem_direita=120
                    )
                else:
                    st.info("Nenhum hospital encontrado")
            else:
                st.info("Nenhum hospital encontrado")
        else:
            st.info("Dados de hospitais não disponíveis")
    
    def _render_top_superintendencias(self, df):
        """Renderiza todas as Superintendências por Custo com visualização otimizada"""
        st.markdown("#### 🏛️ Todas as Superintendências por Custo")
        
        if 'SUPERINTENDENCIA' in df.columns and 'VALOR NIVEL/REF - com teto' in df.columns:
            df_super = df[df['SUPERINTENDENCIA'].notna() & (df['SUPERINTENDENCIA'] != '')].copy()
            
            if not df_super.empty:
                super_custo = df_super.groupby('SUPERINTENDENCIA')['VALOR NIVEL/REF - com teto'].sum().reset_index()
                super_custo.columns = ['Superintendência', 'Custo Total']
                super_custo = super_custo.sort_values('Custo Total', ascending=False)
                
                if not super_custo.empty:
                    # Formatar para exibição em tabela
                    df_exibicao = super_custo.copy()
                    df_exibicao['Custo Total'] = df_exibicao['Custo Total'].apply(
                        lambda x: f'R$ {x:,.2f}'
                    )
                    
                    # Mostrar quantidade total de superintendências
                    st.caption(f"📊 Total de superintendências: **{len(df_exibicao)}**")
                    
                    # Exibir tabela com scroll
                    st.dataframe(
                        df_exibicao, 
                        use_container_width=True, 
                        hide_index=True,
                        height=min(400, max(200, len(df_exibicao) * 35 + 50))
                    )
                    
                    # Gráfico com todas as superintendências
                    altura = max(300, min(800, len(super_custo) * 30))
                    
                    self.ui.grafico_barras_horizontais(
                        super_custo,
                        x='Superintendência',
                        y='Custo Total',
                        titulo='',
                        cor='#7b1fa2',
                        mostrar_rotulos=True,
                        altura=altura,
                        margem_esquerda=200,
                        margem_direita=120
                    )
                else:
                    st.info("Nenhuma superintendência encontrada")
            else:
                st.info("Nenhuma superintendência encontrada")
        else:
            st.info("Dados de superintendências não disponíveis")

    
    def _render_analise_temporal(self, df):
        """Renderiza seção de análise temporal (preparada para futuro)"""
        st.markdown("---")
        st.markdown("### 📅 Análise Temporal")
        
        # Verificar se há colunas com datas
        colunas_data = ['MES_ANO_FOLHA', 'DATA_ADMISSAO', 'DTNASC', 'ANO_INGRESSO']
        colunas_existentes = [col for col in colunas_data if col in df.columns]
        
        if colunas_existentes:
            st.success(f"✅ Dados temporais disponíveis! Colunas encontradas: {', '.join(colunas_existentes)}")
            
            # Se tiver MES_ANO_FOLHA, mostrar evolução
            if 'MES_ANO_FOLHA' in df.columns:
                try:
                    # Tentar converter para data
                    df_temp = df.copy()
                    df_temp['MES_ANO_FOLHA'] = pd.to_datetime(df_temp['MES_ANO_FOLHA'], errors='coerce')
                    df_temp = df_temp[df_temp['MES_ANO_FOLHA'].notna()]
                    
                    if not df_temp.empty and 'VALOR NIVEL/REF - com teto' in df_temp.columns:
                        evolucao = df_temp.groupby(df_temp['MES_ANO_FOLHA'].dt.to_period('M'))['VALOR NIVEL/REF - com teto'].sum().reset_index()
                        evolucao['MES_ANO_FOLHA'] = evolucao['MES_ANO_FOLHA'].astype(str)
                        evolucao.columns = ['Mês/Ano', 'Custo Total']
                        
                        st.markdown("#### 📈 Evolução do Custo por Mês")
                        self.ui.grafico_linhas(
                            evolucao,
                            x='Mês/Ano',
                            y=['Custo Total'],
                            titulo='',
                            mostrar_rotulos=True
                        )
                except Exception as e:
                    st.warning(f"Não foi possível processar dados temporais: {str(e)}")
        else:
            st.info("""
            🔜 **Dados temporais estarão disponíveis em breve**
            
            Para habilitar análises temporais, adicione colunas com datas como:
            - `MES_ANO_FOLHA` - Para evolução mensal
            - `DATA_ADMISSAO` - Para análise de admissões
            - `ANO_INGRESSO` - Para análise por ano
            """)
    
    # ==================== ANÁLISE PESSOAL ====================
    
    def _render_analise_pessoal_tab(self):
        """Renderiza a aba de Análise Pessoal com filtros do dashboard"""
        st.markdown("## 👥 Análise Pessoal")
        
        df = st.session_state.df_completo
        
        # ===== FILTROS DO DASHBOARD =====
        df_filtrado = self._render_filtros_dashboard(df, sufixo_key="_pessoal")
        
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por Faixa Etária
            if 'FAIXA ETARIA' in df_filtrado.columns:
                st.markdown("#### 👤 Distribuição por Faixa Etária")
                faixa_counts = self._contagem_ordenada(
                    df_filtrado['FAIXA ETARIA'],
                    ['MENOR DE 18', '18 a 29', '30 a 39', '40 a 49',
                     '50 a 54', '55 a 59', '60 OU MAIS']
                ).rename(columns={'Categoria': 'Faixa Etária'})
                
                if not faixa_counts.empty:
                    self.ui.grafico_barras(
                        faixa_counts,
                        x='Faixa Etária',
                        y='Quantidade',
                        titulo='',
                        cor='#1E88E5',
                        mostrar_rotulos=True
                    )
                    
                    # Mostrar detalhes
                    total = faixa_counts['Quantidade'].sum()
                    for _, row in faixa_counts.iterrows():
                        perc = (row['Quantidade'] / total * 100) if total > 0 else 0
                        st.caption(f"{row['Faixa Etária']}: {row['Quantidade']:,} ({perc:.1f}%)")
            else:
                st.info("Dados de faixa etária não disponíveis")
        
        with col2:
            # Servidores Idosos
            if 'SERVIDOR IDOSO' in df_filtrado.columns:
                st.markdown("#### 👴 Servidores Idosos")
                idoso_counts = self._contagem_ordenada(
                    df_filtrado['SERVIDOR IDOSO'], ['NAO', 'SIM']
                ).rename(columns={'Categoria': 'Idoso'})
                
                if not idoso_counts.empty:
                    cores = ['#28a745' if x == 'NAO' else '#dc3545' for x in idoso_counts['Idoso']]
                    
                    self.ui.grafico_pizza(
                        idoso_counts,
                        names='Idoso',
                        values='Quantidade',
                        titulo='',
                        colors=cores,
                        mostrar_rotulos=True
                    )
                    
                    total = idoso_counts['Quantidade'].sum()
                    for _, row in idoso_counts.iterrows():
                        perc = (row['Quantidade'] / total * 100) if total > 0 else 0
                        st.caption(f"{row['Idoso']}: {row['Quantidade']:,} ({perc:.1f}%)")
            else:
                st.info("Dados de servidores idosos não disponíveis")
    
    # ==================== ANÁLISE FINANCEIRA ====================
    
    def _render_analise_financeira_tab(self):
        """Renderiza a aba de Análise Financeira com filtros do dashboard"""
        st.markdown("## 💰 Análise Financeira")
        
        df = st.session_state.df_completo
        
        # ===== FILTROS DO DASHBOARD =====
        df_filtrado = self._render_filtros_dashboard(df, sufixo_key="_financeira")
        
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Situação Salarial
            if 'SITUACAO SALARIAL' in df_filtrado.columns:
                st.markdown("#### 📊 Situação Salarial")
                situacao_counts = self._contagem_ordenada(
                    df_filtrado['SITUACAO SALARIAL'],
                    ['ABAIXO DO MINIMO', 'DENTRO DO LIMITE',
                     'ACIMA DO TETO', 'SEM INFORMACAO']
                ).rename(columns={'Categoria': 'Situação'})
                
                if not situacao_counts.empty:
                    cores = {
                        'DENTRO DO LIMITE': '#28a745',
                        'ABAIXO DO MINIMO': '#dc3545',
                        'ACIMA DO TETO': '#ffc107',
                        'SEM INFORMACAO': '#6c757d'
                    }
                    color_list = [cores.get(s, '#6c757d') for s in situacao_counts['Situação']]                    
                    self.ui.grafico_donut(
                        situacao_counts,
                        names='Situação',
                        values='Quantidade',
                        titulo='',
                        colors=color_list,
                        mostrar_rotulos=True
                    )
                    
                    total = situacao_counts['Quantidade'].sum()
                    for _, row in situacao_counts.iterrows():
                        perc = (row['Quantidade'] / total * 100) if total > 0 else 0
                        st.caption(f"{row['Situação']}: {row['Quantidade']:,} ({perc:.1f}%)")
            else:
                st.info("Dados de situação salarial não disponíveis")
        
        with col2:
            # Faixa Salarial
            if 'FAIXA SALARIAL' in df_filtrado.columns:
                st.markdown("#### 💰 Distribuição por Faixa Salarial")
                salario_counts = self._contagem_ordenada(
                    df_filtrado['FAIXA SALARIAL'],
                    ['Até 3 salários mínimos', 'De 3 a 6 salários mínimos',
                     'De 6 a 10 salários mínimos', 'De 10 a 15 salários mínimos',
                     'Mais de 15 salários mínimos']
                ).rename(columns={'Categoria': 'Faixa Salarial'})
                
                if not salario_counts.empty:
                    self.ui.grafico_barras(
                        salario_counts,
                        x='Faixa Salarial',
                        y='Quantidade',
                        titulo='',
                        cor='#28a745',
                        mostrar_rotulos=True
                    )
                    
                    total = salario_counts['Quantidade'].sum()
                    for _, row in salario_counts.iterrows():
                        perc = (row['Quantidade'] / total * 100) if total > 0 else 0
                        st.caption(f"{row['Faixa Salarial']}: {row['Quantidade']:,} ({perc:.1f}%)")
            else:
                st.info("Dados de faixa salarial não disponíveis")
    
    # ==================== UPLOAD ====================
    
    def _render_upload_section(self):
        """Renderiza seção de upload"""
        st.markdown("### 📤 Upload dos Arquivos")
        st.markdown("Faça o upload dos dois arquivos para iniciar o processamento.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            file_ergon = self.ui.file_upload_section(
                "📄 Arquivo Ergon",
                "ergon",
                icone="📄"
            )
        
        with col2:
            file_apoio = self.ui.file_upload_section(
                "📋 Planilha de Apoio",
                "apoio",
                icone="📋"
            )
        
        if file_ergon is not None and file_apoio is not None:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Processar Arquivos", use_container_width=True):
                    self._processar_arquivos(file_ergon, file_apoio)
    
    def _processar_arquivos(self, file_ergon, file_apoio):
        """Processa os arquivos carregados"""
        try:
            st.session_state.colunas_selecionadas = []
            
            with st.spinner('📖 Lendo arquivos...'):
                df_ergon = self.file_handler.ler_arquivo(file_ergon)
                df_apoio = self.file_handler.ler_arquivo(file_apoio)
            
            with st.spinner('⚙️ Processando dados...'):
                resultado = self.ergon_service.processar_dados(df_ergon, df_apoio)
                
                if resultado is not None:
                    df_completo = resultado.df
                    info = resultado.info
                    st.session_state.df_completo = df_completo
                    st.session_state.df_filtrado = df_completo.copy()
                    st.session_state.df_resultado = df_completo.copy()
                    st.session_state.info = info
                    st.session_state.processado = True
                    
                    self.ui.info_box("✅ Processamento concluído com sucesso!", "success")
                    st.rerun()
        
        except Exception as e:
            st.error(f"❌ Erro durante o processamento: {str(e)}")
            import traceback
            with st.expander("🔍 Detalhes do Erro"):
                st.code(traceback.format_exc())
    
    # ==================== DADOS ====================
    
    def _render_data_tab(self):
        """Renderiza a aba de dados"""
        st.markdown("### 📊 Visualização dos Dados")
        
        df = st.session_state.df_completo
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros", f"{len(df):,}")
        with col2:
            st.metric("Total de Colunas", len(df.columns))
        with col3:
            st.metric("Memória Estimada", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        with st.expander("👁️ Visualizar Dados Completos", expanded=True):
            st.dataframe(df, use_container_width=True, height=400)
        
        with st.expander("📊 Estatísticas das Colunas"):
            st.dataframe(df.describe(include='all'), use_container_width=True)

    
    # ==================== FILTROS ====================
    
    def _render_filters_tab(self):
        """Renderiza a aba de filtros"""
        st.markdown("### 🔍 Filtros e Seleção de Colunas")
        
        self._render_duplicate_removal()
        
        st.markdown("---")
        
        df_filtrado = self.ui.filter_section(st.session_state.df_completo)
        st.session_state.df_filtrado = df_filtrado
        
        st.markdown("---")
        
        colunas_disponiveis = list(df_filtrado.columns)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✅ Selecionar Todas", use_container_width=True):
                st.session_state.colunas_selecionadas = colunas_disponiveis.copy()
                st.rerun()
        with col2:
            if st.button("📋 Principais", use_container_width=True):
                principais = ['ORDEM', 'NUMERO FUNCIONAL', 'NOME', 'LOTACAO', 'SETOR', 'VINCULO', 
                             'CARGO AJUSTADO',
                             'IDADE', 'FAIXA ETARIA', 'SERVIDOR IDOSO']
                st.session_state.colunas_selecionadas = [
                    col for col in principais if col in colunas_disponiveis
                ]
                st.rerun()
        with col3:
            if st.button("💰 Salariais", use_container_width=True):
                salariais = ['ORDEM', 'NUMERO FUNCIONAL', 'NOME', 'VINCULO', 'VALOR NIVEL/REF', 
                            'VALOR_SIMBOLO', 'VALOR NIVEL/REF - com teto', 'FAIXA SALARIAL', 
                            'SITUACAO SALARIAL']
                st.session_state.colunas_selecionadas = [
                    col for col in salariais if col in colunas_disponiveis
                ]
                st.rerun()
        with col4:
            if st.button("🔄 Limpar", use_container_width=True):
                st.session_state.colunas_selecionadas = []
                st.rerun()
        
        st.markdown("---")
        
        selecionadas = self.ui.column_selector(
            colunas_disponiveis,
            st.session_state.colunas_selecionadas
        )
        st.session_state.colunas_selecionadas = selecionadas
        
        if selecionadas:
            st.markdown("---")
            selecionadas = self.ui.column_reorder(selecionadas)
            st.session_state.colunas_selecionadas = selecionadas
            
            if selecionadas:
                st.session_state.df_resultado = df_filtrado[selecionadas].copy()
            else:
                st.session_state.df_resultado = pd.DataFrame()
    
    def _render_duplicate_removal(self):
        """Renderiza seção de remoção de duplicatas"""
        df = st.session_state.df_completo
        total_duplicatas = self.validator.contar_duplicatas(df)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.markdown("### 🔄 Remover Duplicatas")
        with col2:
            if total_duplicatas > 0:
                st.markdown(f"<span class='badge badge-red'>⚠️ {total_duplicatas} duplicatas</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='badge badge-green'>✅ Nenhuma duplicata</span>", unsafe_allow_html=True)
        with col3:
            if total_duplicatas > 0:
                if st.button("🗑️ Remover Duplicatas", use_container_width=True):
                    df_limpo = self.validator.remover_duplicatas(df)
                    total_removidas = len(df) - len(df_limpo)
                    
                    st.session_state.df_completo = df_limpo
                    st.session_state.df_filtrado = df_limpo.copy()
                    st.session_state.df_resultado = df_limpo.copy()
                    
                    self.ui.info_box(f"✅ {total_removidas} linhas duplicadas removidas com sucesso!", "success")
                    st.rerun()
    
    # ==================== EXPORTAR ====================
    
    def _render_export_tab(self):
        """Renderiza a aba de exportação"""
        st.markdown("### 📥 Exportar Dados")
        
        if st.session_state.df_resultado.empty:
            self.ui.info_box("⚠️ Selecione pelo menos uma coluna na aba 'Filtros & Colunas' para exportar.", "warning")
            return
        
        self.ui.info_box("💡 Clique no botão abaixo para baixar o arquivo processado em formato Excel", "info")
        
        nome_relatorio = st.text_input(
            "📝 Nome do relatório",
            value="Relatorio Tratado",
            help="Digite um nome para identificar o relatório"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.spinner('Preparando arquivo para download...'):
                excel_data = self.formatter.formatar_excel(
                    st.session_state.df_resultado,
                    nome_relatorio
                )
                
                st.download_button(
                    label="📥 Baixar Arquivo Excel",
                    data=excel_data,
                    file_name=f"{nome_relatorio}_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with st.expander("👁️ Visualizar Dados Selecionados"):
            st.dataframe(st.session_state.df_resultado, use_container_width=True, height=400)
            
            if st.checkbox("📊 Ver Estatísticas"):
                st.dataframe(st.session_state.df_resultado.describe(include='all'), use_container_width=True)
    
    # ==================== HOSPITAIS ====================
    
    def _render_hospital_tab(self):
        """Renderiza a aba de hospitais com filtros do dashboard"""
        st.markdown("### 🏥 Relatório de Custo por Hospital")
        
        if st.session_state.df_completo is not None:
            df = st.session_state.df_completo
            
            # ===== FILTROS DO DASHBOARD =====
            df_filtrado = self._render_filtros_dashboard(df, sufixo_key="_hosp")
            
            if df_filtrado.empty:
                st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados.")
                return
            
            tem_hospitais = self.validator.tem_hospitais(df_filtrado)
            
            if tem_hospitais:
                self.ui.info_box(
                    "💡 Escolha o tipo de relatório:",
                    "info"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📊 Detalhado (por cargo)", use_container_width=True, key="hosp_detalhado"):
                        with st.spinner('Gerando relatório detalhado...'):
                            df_relatorio = self.report_service.gerar_relatorio_hospitais(df_filtrado)
                            if df_relatorio is not None:
                                st.session_state.df_relatorio_hospitais = df_relatorio
                                self.ui.info_box(
                                    f"✅ Relatório detalhado gerado! {len(df_relatorio['HOSPITAL'].unique())} hospitais encontrados.",
                                    "success"
                                )
                                self._render_hospital_report_detail(df_relatorio)
                
                with col2:
                    if st.button("📊 Resumido (apenas totais)", use_container_width=True, key="hosp_resumido"):
                        with st.spinner('Gerando relatório resumido...'):
                            df_relatorio = self.report_service.gerar_relatorio_hospitais_resumido(df_filtrado)
                            if df_relatorio is not None:
                                st.session_state.df_relatorio_hospitais_resumido = df_relatorio
                                self.ui.info_box(
                                    f"✅ Relatório resumido gerado! {len(df_relatorio) - 1} hospitais encontrados.",
                                    "success"
                                )
                                self._render_hospital_report_detail_resumido(df_relatorio)
            else:
                self.ui.info_box("⚠️ Nenhum hospital encontrado nos dados (após filtros).", "warning")
        else:
            self.ui.info_box("⚠️ Processe os dados primeiro para gerar o relatório.", "warning")
    
    def _render_hospital_report_detail(self, df_relatorio: pd.DataFrame):
        """Renderiza detalhes do relatório de hospitais"""
        with st.expander("👁️ Visualizar Relatório Detalhado", expanded=True):
            hospitais = df_relatorio['HOSPITAL'].unique()
            
            for hospital in hospitais:
                st.markdown(f"### 🏥 {hospital}")
                df_hospital = df_relatorio[df_relatorio['HOSPITAL'] == hospital].drop('HOSPITAL', axis=1)
                
                df_exibicao = df_hospital.copy()
                colunas_custo = [col for col in df_exibicao.columns if 'CUSTO' in col]
                for col in colunas_custo:
                    df_exibicao[col] = df_exibicao[col].apply(
                        lambda x: f'R$ {x:,.2f}' if pd.notna(x) else 'R$ 0,00'
                    )
                
                st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
                st.markdown("---")
        
        with st.spinner('Preparando download...'):
            excel_data = self.report_service.salvar_relatorio_hospitais(df_relatorio)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Baixar Relatório Detalhado de Hospitais",
                    data=excel_data,
                    file_name=f"relatorio_hospitais_detalhado_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    def _render_hospital_report_detail_resumido(self, df_relatorio: pd.DataFrame):
        """Renderiza detalhes do relatório resumido de hospitais"""
        with st.expander("👁️ Visualizar Relatório Resumido", expanded=True):
            df_exibicao = df_relatorio.copy()
            colunas_custo = [col for col in df_exibicao.columns if 'CUSTO' in col and col != 'TOTAL_CUSTO']
            for col in colunas_custo:
                df_exibicao[col] = df_exibicao[col].apply(
                    lambda x: f'R$ {x:,.2f}' if pd.notna(x) else 'R$ 0,00'
                )
            df_exibicao['TOTAL_CUSTO'] = df_exibicao['TOTAL_CUSTO'].apply(
                lambda x: f'R$ {x:,.2f}' if pd.notna(x) else 'R$ 0,00'
            )
            
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            
            st.markdown("#### 📊 Distribuição de Custos por Hospital")
            df_grafico = df_relatorio[df_relatorio['HOSPITAL'] != 'TOTAL GERAL'].copy()
            if not df_grafico.empty:
                self.ui.grafico_barras_horizontais(
                    df_grafico,
                    x='HOSPITAL',
                    y='TOTAL_CUSTO',
                    titulo='',
                    cor='#1E88E5',
                    mostrar_rotulos=True
                )
        
        with st.spinner('Preparando download...'):
            excel_data = self.report_service.salvar_relatorio_hospitais_resumido(df_relatorio)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Baixar Relatório Resumido de Hospitais",
                    data=excel_data,
                    file_name=f"relatorio_hospitais_resumido_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    # ==================== SUPERINTENDÊNCIAS ====================
    
    def _render_superintendencia_tab(self):
        """Renderiza a aba de superintendências com filtros do dashboard"""
        st.markdown("### 🏛️ Relatório de Custo por Superintendência")
        
        if st.session_state.df_completo is not None:
            df = st.session_state.df_completo
            
            # ===== FILTROS DO DASHBOARD =====
            df_filtrado = self._render_filtros_dashboard(df, sufixo_key="_super")
            
            if df_filtrado.empty:
                st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados.")
                return
            
            tem_superintendencias = 'SUPERINTENDENCIA' in df_filtrado.columns and df_filtrado['SUPERINTENDENCIA'].notna().any()
            
            if tem_superintendencias:
                self.ui.info_box(
                    "💡 Escolha o tipo de relatório:",
                    "info"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📊 Detalhado (por cargo)", use_container_width=True, key="super_detalhado"):
                        with st.spinner('Gerando relatório detalhado...'):
                            df_relatorio = self.report_service.gerar_relatorio_superintendencias(df_filtrado)
                            if df_relatorio is not None:
                                st.session_state.df_relatorio_superintendencias = df_relatorio
                                self.ui.info_box(
                                    f"✅ Relatório detalhado gerado! {len(df_relatorio['SUPERINTENDENCIA'].unique())} superintendências encontradas.",
                                    "success"
                                )
                                self._render_superintendencia_report_detail(df_relatorio)
                
                with col2:
                    if st.button("📊 Resumido (apenas totais)", use_container_width=True, key="super_resumido"):
                        with st.spinner('Gerando relatório resumido...'):
                            df_relatorio = self.report_service.gerar_relatorio_superintendencias_resumido(df_filtrado)
                            if df_relatorio is not None:
                                st.session_state.df_relatorio_superintendencias_resumido = df_relatorio
                                self.ui.info_box(
                                    f"✅ Relatório resumido gerado! {len(df_relatorio) - 1} superintendências encontradas.",
                                    "success"
                                )
                                self._render_superintendencia_report_detail_resumido(df_relatorio)
            else:
                self.ui.info_box("⚠️ Nenhuma superintendência encontrada nos dados (após filtros).", "warning")
        else:
            self.ui.info_box("⚠️ Processe os dados primeiro para gerar o relatório.", "warning")
    
    def _render_superintendencia_report_detail(self, df_relatorio: pd.DataFrame):
        """Renderiza detalhes do relatório de superintendências"""
        with st.expander("👁️ Visualizar Relatório Detalhado", expanded=True):
            superintendencias = df_relatorio['SUPERINTENDENCIA'].unique()
            
            for superintendencia in superintendencias:
                st.markdown(f"### 🏛️ {superintendencia}")
                df_super = df_relatorio[df_relatorio['SUPERINTENDENCIA'] == superintendencia].drop('SUPERINTENDENCIA', axis=1)
                
                df_exibicao = df_super.copy()
                colunas_custo = [col for col in df_exibicao.columns if 'CUSTO' in col]
                for col in colunas_custo:
                    df_exibicao[col] = df_exibicao[col].apply(
                        lambda x: f'R$ {x:,.2f}' if pd.notna(x) else 'R$ 0,00'
                    )
                
                st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
                st.markdown("---")
        
        with st.spinner('Preparando download...'):
            excel_data = self.report_service.salvar_relatorio_superintendencias(df_relatorio)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Baixar Relatório Detalhado de Superintendências",
                    data=excel_data,
                    file_name=f"relatorio_superintendencias_detalhado_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    def _render_superintendencia_report_detail_resumido(self, df_relatorio: pd.DataFrame):
        """Renderiza detalhes do relatório resumido de superintendências"""
        with st.expander("👁️ Visualizar Relatório Resumido", expanded=True):
            df_exibicao = df_relatorio.copy()
            colunas_custo = [col for col in df_exibicao.columns if 'CUSTO' in col and col != 'TOTAL_CUSTO']
            for col in colunas_custo:
                df_exibicao[col] = df_exibicao[col].apply(
                    lambda x: f'R$ {x:,.2f}' if pd.notna(x) else 'R$ 0,00'
                )
            df_exibicao['TOTAL_CUSTO'] = df_exibicao['TOTAL_CUSTO'].apply(
                lambda x: f'R$ {x:,.2f}' if pd.notna(x) else 'R$ 0,00'
            )
            
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            
            st.markdown("#### 📊 Distribuição de Custos por Superintendência")
            df_grafico = df_relatorio[df_relatorio['SUPERINTENDENCIA'] != 'TOTAL GERAL'].copy()
            if not df_grafico.empty:
                self.ui.grafico_barras_horizontais(
                    df_grafico,
                    x='SUPERINTENDENCIA',
                    y='TOTAL_CUSTO',
                    titulo='',
                    cor='#7b1fa2',
                    mostrar_rotulos=True
                )
        
        with st.spinner('Preparando download...'):
            excel_data = self.report_service.salvar_relatorio_superintendencias_resumido(df_relatorio)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Baixar Relatório Resumido de Superintendências",
                    data=excel_data,
                    file_name=f"relatorio_superintendencias_resumido_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    def _render_footer(self):
        """Renderiza rodapé"""
        st.markdown("""
        <div class="footer">
            Desenvolvido com ❤️ para o Sistema Ergon<br>
            Versão 4.0 - Com Dashboard Reformulado, Todos os Hospitais/Superintendências e Rótulos
        </div>
        """, unsafe_allow_html=True)
