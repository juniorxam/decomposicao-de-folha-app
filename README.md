# Sistema de Tratamento de Dados - Ergon

Aplicação Streamlit para tratamento, consolidação, análise e exportação de dados do Ergon.

## Requisitos

- Python 3.10 ou superior
- Windows (o arquivo `executar app.bat` automatiza a instalação)
- Dependências em `requirements.txt`

## Execução

1. Clone ou baixe o repositório.
2. Execute `executar app.bat`.
3. O navegador será aberto em `http://localhost:8501`.

Para instalação manual:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Fluxo do sistema

1. Enviar o arquivo Ergon (FOLHA ou ATIVOS).
2. Enviar a planilha de apoio.
3. O sistema identifica o tipo do relatório e valida as colunas essenciais.
4. Os dados são normalizados e cruzados pela coluna de setor/lotação.
5. São calculados vínculos, idade, faixa etária e regras salariais quando aplicáveis.
6. O usuário pode filtrar, selecionar e reordenar colunas.
7. O sistema gera relatórios detalhados e resumidos de hospitais e superintendências.
8. Os resultados podem ser exportados para Excel.

## Tipos de entrada

### FOLHA

É identificada pela presença de `MES_ANO_FOLHA`.

Colunas estruturais esperadas:
- `SETOR`
- `TIPOVINC`

### ATIVOS

Quando `MES_ANO_FOLHA` não está presente, o arquivo é tratado como ATIVOS.

Colunas estruturais esperadas:
- `LOTACAO`
- `TIPO_VINCULO`

A planilha de apoio deve conter:
- `SETOR`

## Regras importantes

- Vínculos são padronizados em CONTRATADO, EFETIVO, COMISSIONADO ou OUTROS.
- Valores monetários aceitam formatos numéricos e formatos brasileiros, como `1.234,56`.
- Para ATIVOS, a idade é calculada a partir de `DTNASC`.
- O teto salarial é aplicado somente quando o relatório é de ATIVOS.
- Os relatórios Excel detalhados criam uma aba por hospital/superintendência, com nomes sanitizados e únicos para respeitar as limitações do Excel.

## Estrutura

- `app.py`: entrada da aplicação.
- `config.py`: constantes e regras de configuração.
- `services/ergon_service.py`: processamento principal dos dados.
- `services/report_service.py`: geração dos relatórios.
- `utils/data_processors.py`: conversões e cálculos.
- `utils/file_handlers.py`: leitura e escrita de arquivos.
- `utils/formatters.py`: formatação de Excel.
- `utils/validators.py`: validações.
- `ui/components.py`: componentes visuais.
- `ui/pages.py`: fluxo da interface.
- `ui/styles.py`: estilos visuais.

## Observação

Os arquivos de dados Ergon/Excel/CSV são ignorados pelo Git por segurança e não devem ser versionados no repositório.
