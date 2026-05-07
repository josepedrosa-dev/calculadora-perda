# Calculadora de Recuperacao de Energia

Aplicacao Streamlit para analise de perda de energia, com entrada manual, importacao de planilha e extracao automatica por PDF de medicao fiscal.

## Visao Geral da Evolucao

Este documento apresenta o comparativo entre o script base anexado (versao original) e o estado atual do projeto em [app.py](app.py).

### Resultado da evolucao

A aplicacao saiu de um fluxo unico, com entrada simples e simulacao basica, para uma experiencia guiada por etapas, com validacoes robustas, estado persistente e suporte a PDF com escolha de referencia.

## Comparativo Antes x Atual

| Area | Antes (script base) | Atual (projeto) |
|---|---|---|
| Entrada de dados | Upload apenas Excel + Manual | Upload de Arquivo (Excel e PDF) + Manual |
| Validacao de dados | Validacao minima | Validacao estruturada por colunas, tipos, negativos e duplicidade |
| Fluxo da tela | Fluxo linear | Navegacao por etapas (Entrada, Resultados, Simulacao) com status visual |
| Interface | Layout funcional simples | Layout refinado, hierarquia visual, feedbacks, cards e componentes orientativos |
| Simulacao | Parametros basicos | Persistencia completa de estado, limpeza segura, semaforo e barra de progresso |
| Estado no Streamlit | Menos controle de sessao | Controle robusto de session state para evitar excecoes de widgets |
| Importacao PDF | Inexistente | Extracao automatica de campos-chave com tratamento de referencia |
| Referencia para calculo (PDF) | Nao aplicavel | Selecao de referencia (3 meses + Media), com fallback seguro |

## Principais Modificacoes Implementadas

### 1) Front-end e UX

- Tema visual consolidado com melhor contraste e legibilidade.
- Cabecalho e secoes com identidade visual mais clara.
- Organizacao por etapas com indicador de status operacional.
- Botoes com hierarquia de acao:
- primario para Rodar analise
- secundario para acoes de apoio/remocao

### 2) Fluxo guiado e navegacao

- A tela passou a trabalhar por etapas:
- Entrada
- Resultados
- Simulacao
- Apos rodar analise, a aplicacao avanca automaticamente para Resultados.

### 3) Entrada de dados mais robusta

- Validacao centralizada via funcao de validacao.
- Verificacao de:
- colunas obrigatorias
- valores numericos
- valores negativos
- instalacao vazia
- instalacao duplicada
- Entrada manual com edicao da base e remocao de instalacao.

### 4) Simulador evoluido

- Modo valor medio e modo customizado individualmente.
- Persistencia dos valores customizados ao navegar entre etapas.
- Botao Limpar codigos com reset seguro via estado pendente.
- Indicador de progresso para meta com semaforo:
- Critico
- Atencao
- Meta proxima/atingida

### 5) Suporte a PDF de medicao fiscal

- Inclusao de parser em [app.py](app.py) para extrair automaticamente:
- INSTALACAO
- REQUERIDA
- INJETADA
- REVERSA
- CONSUMO
- ILUMINACAO_PUBLICA
- Selecao da referencia de extracao (meses e media).
- Normalizacao numerica para formatos com ponto e virgula.
- Regras de fallback para variacoes de layout no PDF.

### 6) Dependencias atualizadas

- Inclusao de biblioteca de leitura PDF em [requirements.txt](requirements.txt):
- pypdf

## Ganhos Praticos

- Menor chance de erro operacional na entrada.
- Experiencia mais intuitiva para usuario final.
- Maior confiabilidade no fluxo de simulacao.
- Reducao de trabalho manual ao importar dados de PDF.
- Melhor base para manutencao e futuras evolucoes.

## Estrutura Atual

- Aplicacao principal: [app.py](app.py)
- Dependencias: [requirements.txt](requirements.txt)

## Como Executar

1. Instale dependencias:

```bash
pip install -r requirements.txt
```

2. Execute a aplicacao:

```bash
streamlit run app.py
```

## Roadmap Recomendado (proximos passos)

1. Adicionar validacao visual de referencia extraida do PDF (tabela de conferencia antes do calculo).
2. Criar testes para parser de PDF com multiplos layouts reais.
3. Exportar relatorio consolidado (CSV/Excel) incluindo referencia selecionada.
4. Implementar log de auditoria para rastrear entrada, referencia e resultado da simulacao.

---

Desenvolvimento orientado para uso operacional, foco em confiabilidade de dados e melhoria continua da experiencia do usuario.
